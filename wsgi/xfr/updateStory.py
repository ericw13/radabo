#!/usr/bin/python

import requests,sys,re,os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rally.settings")
import django
django.setup()
from metrics import rallyurls, rallycreds
from metrics.models import Story
from metrics.views import getSprint, getRelease
from django.db.models import Q, F

#stories = Story.objects.filter(~Q(status="A"))
stories = Story.objects.all()
urlopts = "&fetch=true"
for this in stories:
    qs = "query=(FormattedID%20%3D%20%22" + this.rallyNumber + "%22)"
    url = rallyurls.storyUrl + qs + urlopts
    results = requests.get(url, auth=(rallycreds.user,rallycreds.pw))
    data = results.json()

    for story in data['QueryResult']['Results']:

        # This script only updates existing stories
        this.description=story['_refObjectName']
        this.points=story['PlanEstimate']
        this.businessValue=story['c_BusinessValueBV']
        this.status=story['ScheduleStatePrefix']
        this.module=story['Package']
        this.stakeholders=story['c_Stakeholders']
        if story['Iteration']:
            this.currentSprint = getSprint(story['Iteration']['_refObjectName'])

        if this.initialSprint == None:
            this.initialSprint = this.currentSprint

        if story['Release']:
            this.release = getRelease(story['Release']['_refObjectName'])
            print "Set release %s for story %s" % (this.release, this.rallyNumber)

        if len(story['Tags']['_tagsNameArray']) > 0:
            this.track=story['Tags']['_tagsNameArray'][0]['Name']

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
