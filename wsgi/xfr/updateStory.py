#!/usr/bin/python

import requests,sys,re,os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "xfr.settings")
import django
django.setup()
from metrics.models import Story
from metrics.views import getSprint, getRelease
from django.db.models import Q, F
from pyral import Rally, rallyWorkset
from rallyUtil import get_api_key

api_key = get_api_key()
rallyServer = rallyWorkset([])[0]
rally = Rally(rallyServer, apikey = api_key, user=None, password=None)

#stories = Story.objects.filter(rallyNumber="US50609")
stories = Story.objects.filter(~Q(currentSprint__status="Accepted",status="A"))
for this in stories:
    q = [
         'FormattedID = "%s"' % (this.rallyNumber)
        ]
    response = rally.get('UserStory',query=q,fetch="Name,PlanEstimate,c_BusinessValueBV,ScheduleStatePrefix,Package,c_SolutionSize,c_Stakeholders,Iteration,Release,Tags,RevisionHistory")

    if response.resultCount == 0:
        print "Deleting %s" % (this.rallyNumber)
        this.delete()
    else:
      print "Updating %s" % (this.rallyNumber)
      for story in response:

        if not story.PlanEstimate:
           solSize = story.c_SolutionSize
        elif story.PlanEstimate <= 3:
           solSize = "Small"
        elif story.PlanEstimate <= 8:
           solSize = "Medium"
        elif story.PlanEstimate <= 99:
           solSize = "Large"

        # This script only updates existing stories
        this.description=story.Name
        this.points=story.PlanEstimate
        this.businessValue=story.c_BusinessValueBV
        this.status=story.ScheduleStatePrefix
        this.module=story.Package
        this.stakeholders=story.c_Stakeholders
        this.solutionSize=solSize
        if story.Iteration:
            this.currentSprint = getSprint(story.Iteration.Name)
        if this.initialSprint == None:
            this.initialSprint = this.currentSprint
        if story.Release:
            this.release = getRelease(story.Release.Name)
        if story.Tags:
            this.track = story.Tags[0].Name
        if this.status in ['B','D','P']:
            this.completionDate = None
        elif this.status in ['C','A'] and this.completionDate == None:
            for rec in story.RevisionHistory.Revisions:
                if re.match(r'.*?SCHEDULE STATE changed.*to \[Completed\]',rec.Description):
                    this.completionDate = rec.CreationDate
                    break

        this.save()
