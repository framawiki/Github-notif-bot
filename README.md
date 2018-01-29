# Github-notif-bot

Project to create a bot that add a comment in linked Phabricator task when a Pull-request is open or a commit is pushed on Github.

See this project on Phabricator, our bugtracker : https://phabricator.wikimedia.org/project/profile/2762/

## Install it on Tools

On a clean project

See this help page too : https://wikitech.wikimedia.org/wiki/Help:Tool_Labs/My_first_Flask_OAuth_tool

```
cd $HOME
webservice --backend=kubernetes python shell
python3 -m venv $HOME/www/python/venv
source $HOME/www/python/venv/bin/activate
git clone https://github.com/framawiki/Github-notif-bot
pip install --upgrade pip
pip install -r Github-notif-bot/requirements.txt
ln -s $HOME/Github-notif-bot/githubbot/ $HOME/www/python/src
webservice --backend=kubernetes python start
```

## Credits - see also

The creation of this project was inspired by 

- [its-phabricator](https://gerrit-review.googlesource.com/admin/repos/plugins%2Fits-phabricator) for the idea and functionalities of the bot (the original is coded in java and links gerrit and phabricator) - aka. gerritbot
- [python-github-webhooks](https://github.com/carlos-jenkins/python-github-webhooks/) for ideas regarding the analysis of github data
