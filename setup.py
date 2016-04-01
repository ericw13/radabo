#!/usr/bin/env python

from setuptools import setup

setup(
    # GETTING-STARTED: set your app name:
    name='xfrAdmin',
    # GETTING-STARTED: set your app version:
    version='1.0',
    # GETTING-STARTED: set your app description:
    description='Puddlejumper Data Management',
    # GETTING-STARTED: set author name (your name):
    author='Eric Wright',
    # GETTING-STARTED: set author email (your email):
    author_email='ewright@redhat.com',
    # GETTING-STARTED: set author url (your url):
    url='http://www.redhat.com/',
    # GETTING-STARTED: define required django version:
    install_requires=[
        'Django==1.9.5'
    ],
    dependency_links=[
        'https://pypi.python.org/simple/django/'
    ],
)
