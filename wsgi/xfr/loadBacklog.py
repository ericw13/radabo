#!/usr/bin/python

import requests,sys,re,os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "xfr.settings")
import django
django.setup()
from metrics.models import Story
from metrics.views import getStory
from pyral import Rally, rallyWorkset
from rallyUtil import get_api_key

api_key = get_api_key()
rallyServer = rallyWorkset([])[0]
rally = Rally(rallyServer, apikey = api_key, user=None, password=None)

q = [
    'Release = null',
    'Feature.FormattedID = 1467',
    ]
response = rally.get('UserStory',query=q,fetch="FormattedID,Name,PlanEstimate,c_BusinessValueBV,ScheduleStatePrefix,Package,c_SolutionSize,c_Stakeholders,Tags",order="FormattedID")

if response.resultCount == 0:
    print "Cannot find any stories in the backlog!"
    print response.errors
    sys.exit(1)

for story in response:

    this=getStory(story.FormattedID)
    if this == None:
      # Create new instance
        print "Creating story " + story.FormattedID
        tag=story.Tags[0].Name if story.Tags else None

        if not story.PlanEstimate:
           solSize = story.c_SolutionSize
        elif story.PlanEstimate <= 3:
           solSize = "Small"
        elif story.PlanEstimate <= 8:
           solSize = "Medium"
        elif story.PlanEstimate <= 99:
           solSize = "Large"


        this = Story(rallyNumber=story.FormattedID,
                     description=story.Name,
                     points=story.PlanEstimate,
                     businessValue=story.c_BusinessValueBV,
                     status=story.ScheduleStatePrefix,                   
                     module=story.Package,
                     stakeholders=story.c_Stakeholders,
                     solutionSize=solSize,
                     track=tag)
        this.save()
