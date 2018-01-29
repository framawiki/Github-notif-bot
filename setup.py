#!/bin/env python
# -*- coding: utf8 -*-

from distribute_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages

version = "0.1.0"

setup(
    name="githubbot",
    version=version,
    description="Github-notif-bot for Phabricator",
    classifiers=[],
    keywords="github hook hooks phabricator notification",
    author="Framawiki",
    author_email="framawiki@tools.wmflabs.org",
    url="https://phabricator.wikimedia.org/project/manage/2762/",
    license="GPL-3.0+",
    packages=find_packages(
    ),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "Flask",
        "ipaddress",
        "requests",
        "phabricator",
    ],
)
