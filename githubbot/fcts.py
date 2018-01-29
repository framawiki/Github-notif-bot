#-*- coding:utf-8 -*-

# Github-notif-bot - Github to Phabricator gateway
# Copyright (C) 2017-2018 Framawiki <framawiki@tools.wmflabs.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals, print_function

import requests
from ipaddress import ip_network, ip_address
from json import loads, dumps
import re
import logging
import phabricator

class Config(object):

    def __init__(self):
        with open('config.json', 'r') as cfg:
            self.config = loads(cfg.read())

    def get(self, name, default):
        return self.config.get(name, default)


class IpWhitelist(object):

    def __init__(self, debug):
        self.debug = debug
        self.whitelist = self.debug
        self.update()
    
    def update(self):
        self.whitelist = self.debug
        uri = 'https://api.github.com/meta'
        gh_api = requests.get(uri)
        if gh_api.status_code != 200:
            raise Exception('received {0} status from {1}'.format(gh_api.status_code, uri))
        assert gh_api.text
        gh_api = gh_api.json()['hooks']
        for ip in gh_api:
            self.whitelist.append(ip_network(ip))
        logging.info('IpWhitelist updated : now contains %s' % ', '.join([str(i) for i in self.whitelist]))
    
    def is_ok(self, ip):
        ip = ip_address('{}'.format(ip))
        if not ip in self.whitelist:
            logging.info('IP: %s is not in the whitelist, update it then retry' % ip)
            self.update()
            if not ip in self.whitelist:
                return False
        return True


class RepoWhitelist(object): #TODO

    def __init__(self, debug):
        self.debug = debug
        self.whitelist = self.debug
        self.update()
    
    def update(self):
        self.whitelist = self.debug
        uri = 'https://wikitech.wikimedia.org/w/index.php?title=XXX&action=raw'
        wikipage = requests.get(uri)
        if wikipage.status_code != 200:
            raise Exception('RepoWhitelist: received {0} status from {1}'.format(wikipage.status_code, uri))
        assert wikipage.text
        wikipage = wikipage.json()['repositories']
        for repo in wikipage:
            # Whitelist list entry like ['framawiki'] or ['framawiki', 'testrepo']
            if len(repo) in [1, 2]:
                self.whitelist.append(repo)
            else:
                logging.info('RepoWhitelist: bad entry ? Len should be 1 or 2, get %s. """%s"""' % (len(repo), repo))
        logging.info('RepoWhitelist updated : now contains %s' % ', '.join([str(i) for i in self.whitelist]))
        
    def verify(self, repo):
        for whitelisted in self.whitelist:
            if len(whitelisted) == 1:
                if whitelisted[0] == repo[0]:
                    return True
            else:
                if whitelisted == repo:
                    return True
            return False
        
    def is_ok(self, repo):
        if not self.verify(repo):
            logging.info('Repo: %s is not in the whitelist, update it then retry' % repo)
            self.update()
            if not self.verify(repo):
                return False
        return True


def getBranch(payload, event):
    branch = 'no-branch'
    try:
        if 'ref_type' in payload:
            if payload['ref_type'] == 'branch':
                branch = payload['ref']
        elif 'pull_request' in payload:
            branch = payload['pull_request']['base']['ref']
        elif event in ['push']:
            branch = payload['ref'].split('/')[2]
    except KeyError:
        pass
    return branch


def getRepoName(payload):
    if 'repository' in payload:
        name = payload['repository']['full_name'].split('/') # or ['name']
        assert len(name) == 2
        return name
    return
    

def getSections(text):
    return text.rstrip().replace('\\r', '').replace('\\n', '\n').split('\n\n')
    
    
def getTaskID(text):
    find = re.findall(r'^Bug ?\: ?(T\d+)$', getSections(text)[-1], re.I|re.U|re.M)
    if not find:
        logging.info('No linked phab tasks found')
        return []
    else:
        logging.info('Phab tasks found (%s): %s' % (len(find), ', '.join(find)))
        return list(set([i.upper() for i in find]))
    

def parsePayload(payload=None, event=None, reponame=None, branch=None):
    assert payload
    assert event
    assert reponame
    phabActions = []

    if event == "pull_request" and "pull_request" in payload:
        print('pull_request. Action: %s' % payload["action"])
        template = None
        
        # PR created
        if payload["action"] == "opened":
            template = 'pullrequest-opened'
            
        elif payload["action"] == "closed":
            # PR closed
            
            if payload["pull_request"]["merged"] == False:
                # PR closed with unmerged commits
                template = 'pullrequest-closed'
                
            elif payload["pull_request"]["merged"] == True:
                # PR was merged
                template = 'pullrequest-merged'
        
        assert template
        phabActions.append({'taskid': getTaskID(text=''),#TODO: get pr content
                                'template': template,
                                'url': payload["pull_request"]["html_url"],
                                'uploader-name': payload["pull_request"]["user"]["login"],
                                'subject': payload["pull_request"]["title"],
                                'reponame': reponame,
                                'branch': branch,
                                'patchForReview': True if template == 'pullrequest-opened' else False
                               })
                               
    elif event == "push" and "commits" in payload:
        print('commits.')
        # One or more commits were sent, we need to parse each of them
        for commit in payload["commits"]:
            phabActions.append({'taskid': getTaskID(commit["message"]),
                                'template': 'commit-puched',
                                'url': commit["url"],
                                'user': commit["author"]["username"],
                                'subject': getSections(commit["message"])[0],
                                'reponame': reponame,
                                'branch': branch,
                                'patchForReview': True
                               })
    
    logging.info(str(phabActions))
    
    #TODO: implement gh issues
    return phabActions


def generateComment(phabAction):
    with open('templates/%s' % phabAction['template'], 'rb') as f:
        template = f.read().decode("UTF-8")
    return template.format(**phabAction)


def postComment(host=None, token=None, taskID=None, comment=None, patchForReview=False):
    data = [{'type': 'comment', 'value': comment}]
    if patchForReview:
        data.append({'type':'projects.add', 'value':['Patch-For-Review']})
    logging.info('Posting comment to %s, data:\n%s' % (taskID, dumps(data, indent=4)))
    phab = phabricator.Phabricator(host=host, token=token)
    phab.maniphest.edit(objectIdentifier=taskID, transactions=data)
