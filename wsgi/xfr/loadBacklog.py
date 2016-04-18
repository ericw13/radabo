#!/usr/bin/python

import requests,sys,re,os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "xfr.settings")
import django
django.setup()
from metrics import rallyurls, rallycreds
from metrics.models import Story
from metrics.views import getStory

url = rallyurls.storyUrl + "query=((Release%20%3D%20%22%22)%20and%20(Feature.FormattedID%20%3D%201467))&fetch=true&pagesize=200"
results = requests.get(url, auth=(rallycreds.user,rallycreds.pw))
data = results.json()

for story in data['QueryResult']['Results']:
    this=getStory(story['FormattedID'])
    if len(story['Tags']['_tagsNameArray']) > 0:
        tag=story['Tags']['_tagsNameArray'][0]['Name']
    else:
        tag=None

    if this == None:
      # Create new instance

       this = Story(rallyNumber=story['FormattedID'],
                    description=story['_refObjectName'],
                    points=story['PlanEstimate'],
                    businessValue=story['c_BusinessValueBV'],
                    status=story['ScheduleStatePrefix'],                   
                    rallyOID=story['ObjectID'],
                    revHistoryURL=story['RevisionHistory']['_ref'],
                    module=story['Package'],
                    stakeholders=story['c_Stakeholders'],
                    track=tag)
    else:
       this.description=story['_refObjectName']
       this.points=story['PlanEstimate']
       this.businessValue=story['c_BusinessValueBV']
       this.status=story['ScheduleStatePrefix']
       this.module=story['Package']
       this.stakeholders=story['c_Stakeholders']
       this.track = tag

# Look at revision history and try to get completion date

    if this.status in ['C','A'] and this.completionDate == None:
        url = this.revHistoryURL + "/Revisions"
        payload = {'pagesize': '50'}
        res = requests.get(url,params=payload,auth=(rallycreds.user,rallycreds.pw))
        data = res.json()
        for rev in data['QueryResult']['Results']:
          if re.match(r'.*?SCHEDULE STATE changed.*to \[Completed\]',rev['Description']):
              this.completionDate = rev['CreationDate']
              break

    this.save()
