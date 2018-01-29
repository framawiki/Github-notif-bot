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

import unittest
from json import loads

import fcts

def openfile(name):
    with open('tests/%s' % name, 'rb') as f:
        contents = f.read().decode("UTF-8")
    return contents


class testsgetTaskID(unittest.TestCase):
    """Test the getTaskID() function, the task number parser"""

    def testgetTaskID1(self):
        """1 task"""
        self.assertEqual(fcts.getTaskID(openfile('commit-msg1')), ['T169447'])
        
    def testgetTaskID2(self):
        """no task"""
        self.assertEqual(fcts.getTaskID(openfile('commit-msg2')), [])
         
    def testgetTaskID3(self):
        """1 task + 2 bad tasks"""
        self.assertEqual(fcts.getTaskID(openfile('commit-msg3')), ['T168784'])
        
    def testgetTaskID4(self):
        """2 tasks + blank lines"""
        self.assertListEqual(sorted(fcts.getTaskID(openfile('commit-msg4'))), ['T135304', 'T98116111'])


class testsupdateWhitelistIPs(unittest.TestCase):
    """Test the IpWhitelist class, that take care of the verification of the IP of Github"""

    def testupdateWhitelistIPs(self):
        """Github API parser works"""
        ipWhitelist = fcts.IpWhitelist([])
        self.assertTrue(len(ipWhitelist.whitelist))


class testsGenerateComment(unittest.TestCase):
    """Test the generateComment() function, that generate a comment from a phabAction"""

    def testGenerateComment1(self):
        """A comment is generated"""
        self.assertTrue(fcts.generateComment({'taskid': 'T999',
                                'template': 'pullrequest-opened',
                                'url': 'https://phabricator.wikimedia.org/D6595456464',
                                'uploader-name': 'Framawiki',
                                'subject': 'It\'s a test !',
                                'reponame': 'testrepo',
                                'branch': 'testbranch',
                               }))


class testsParsePayload(unittest.TestCase):
    """Test the parsePayload() function, the payload parser and phabAction generator"""

    def testParsePayload1(self):
        """A phabAction is generated with this push"""
        self.assertEqual(len(fcts.parsePayload(payload=loads(openfile('payload2-commitfileedit')),
                                               event='push', reponame='repo', branch='branch')),
                         1)
                         
    def testParsePayload2(self):
        """The good task id is returned"""
        self.assertEqual(fcts.parsePayload(payload=loads(openfile('payload2-commitfileedit')),
                                           event='push', reponame='repo', branch='branch')[0]['taskid'],
                         ['T1234'])
    
    def testParsePayload3(self):
        """No phabAction are (yet) generated with issue_comment"""
        self.assertEqual(fcts.parsePayload(payload=loads(openfile('payload13-issuecomment')),
                                           event='issue_comment', reponame='repo', branch='branch'),
                         [])

    def testParsePayload4(self):
        """A phabAction is generated with pull_request merged"""
        self.assertEqual(len(fcts.parsePayload(payload=loads(openfile('payload10-prclosedmerged1')),
                                               event='pull_request', reponame='repo', branch='branch')),
                         1)

    def testParsePayload5(self):
        """Two phabActions are generated with this push"""
        self.assertEqual(len(fcts.parsePayload(payload=loads(openfile('payload15-commit1pushed2commitsformcli')),
                                               event='push', reponame='repo', branch='branch')),
                         2)
    

class testGetRepoName(unittest.TestCase):
    """Test the getRepoName() function"""

    def testgetRepoName1(self):
        self.assertEqual(fcts.getRepoName(loads(openfile('payload2-commitfileedit'))), ['framawiki', 'testhook'])

if __name__ == '__main__':
    unittest.main()
