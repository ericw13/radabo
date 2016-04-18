#!/usr/bin/python
import requests,os,re
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "xfr.settings")
import django
django.setup()
from metrics import rallyurls, rallycreds
from metrics.models import Release
from metrics.views import getRelease
from datetime import datetime

opts = "?pagesize=99"
url = rallyurls.releaseUrl + opts
results = requests.get(url, auth=(rallycreds.user,rallycreds.pw))
data = results.json()

for release in data['QueryResult']['Results']:
  if re.search(r'Enh Release', release['_refObjectName']) and datetime.strptime(release['ReleaseStartDate'], '%Y-%m-%dT%H:%M:%S.%fZ') > datetime(2016,1,1,0,0):
    this=getRelease(release['Name'])
    # TODO start here
    if this == None:
      # Create new instance
       this = Release(name=release['Name'],
                     startDate=release['ReleaseStartDate'],
                     endDate=release['ReleaseDate'],
                     status=release['State'])
    else:
       this.startDate = release['StartDate']
       this.endDate = release['EndDate']
       this.status = release['State']

    this.save()
