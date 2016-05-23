#!/usr/bin/python
import requests,os,re,sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "xfr.settings")
import django
django.setup()
from metrics.models import Release
from metrics.utils import getRelease, initRally
from datetime import datetime

rally=initRally()

q = ['Name contains "Enh Release"',
     'ReleaseStartDate > "2016-01-01T00:00:00.000Z"'
    ]
response = rally.get('Release',query=q,fetch="Name,ReleaseStartDate,ReleaseDate,State")
for release in response:
    this=getRelease(release.Name)
    if this == None:
      # Create new instance
       this = Release(name=release.Name,
                     startDate=release.ReleaseStartDate,
                     endDate=release.ReleaseDate,
                     status=release.State)
    else:
       this.startDate = release.ReleaseStartDate
       this.endDate = release.ReleaseDate
       this.status = release.State

    this.save()
