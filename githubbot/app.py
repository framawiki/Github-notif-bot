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

from json import loads, dumps
import logging
from sys import stdout
# logging.basicConfig(stream=stdout)
logging.basicConfig(level=logging.DEBUG)
from ipaddress import ip_address
from flask import Flask, request, abort

import fcts

application = Flask(__name__)

config = fcts.Config()
ipWhitelist = fcts.IpWhitelist([ip_address(u'127.0.0.1')])
repoWhitelist = fcts.RepoWhitelist([]) # insert here debug IP and repo user/name


@application.route('/endpoint', methods=['POST', 'GET'])
def index():
    # if request.method != 'POST':
    #   abort(501)

    # Verify IP in Github ones whitelist
    assert request.remote_addr
    if not ipWhitelist.is_ok(request.remote_addr):
        abort(403)

    # If Github wants to verify that we exist
    event = request.headers.get('X-GitHub-Event', None)
    if not event:
        return dumps({'msg': 'Hello here'})

    # Get datas
    payload = loads(request.data)
    branch = fcts.getBranch(payload, event)
    reponame = fcts.getRepoName(payload)
    
    # Verify repository name in whitelist
    assert reponame
    if not repoWhitelist.is_ok(reponame):
        abort(403)
    
    # Analys datas
    phabActions = fcts.parsePayload(payload=payload, event=event, reponame=reponame, branch=branch)
    logging.info('PhabActions: %s: %s' % (len(phabActions), ' ; '.join(phabActions)))

    # Ececute
    if not phabActions:
        return dumps({'msg': 'this action is out of scope'})
    for phabAction in phabActions:
        if not phabAction['taskid']:
            continue
        fcts.postComment(host=config.get('host', None),
                         token=config.get('token', None),
                         taskID=phabAction['taskid'],
                         comment=fcts.generateComment(phabAction),
                         patchForReview=phabAction['patchForReview']
                         )

    return dumps({'msg': '%s actions done' % len(phabActions)})


if __name__ == '__main__':
    # application.run(debug=False, host='0.0.0.0')
    application.run(debug=True)
