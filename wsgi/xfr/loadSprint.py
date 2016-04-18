#!/usr/bin/python
import requests,os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rally.settings")
import django
django.setup()
from metrics import rallyurls, rallycreds
from metrics.models import Sprint
from metrics.views import getSprint

results = requests.get(rallyurls.sprintUrl, auth=(rallycreds.user,rallycreds.pw))
data = results.json()

for sprint in data['QueryResult']['Results']:
    this=getSprint(sprint['Name'])
    if this == None:
      # Create new instance
       this = Sprint(name=sprint['Name'],
                     startDate=sprint['StartDate'],
                     endDate=sprint['EndDate'],
                     velocity=sprint['PlanEstimate'],
                     status=sprint['State'])
    else:
       this.startDate = sprint['StartDate']
       this.endDate = sprint['EndDate']
       this.velocity = sprint['PlanEstimate']
       this.status = sprint['State']

    this.save()
