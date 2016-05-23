#!/usr/bin/python

import requests,sys,re,os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "xfr.settings")
import django
django.setup()
from metrics.models import Story, Session
from metrics.utils import getStory, createStory, updateStory, initRally
from pyral import Rally, rallyWorkset
from rallyUtil import get_api_key
from django.utils import timezone
from django.db.models import Q, F

session=Session()
session.save()
rally = initRally()

# Load new backlog items from Rally
q = '((Feature.FormattedID = "1467") AND (Release = "")) OR (Feature.FormattedID = "3841")'
#q = [
    #'Release = null',
    #'Feature.FormattedID = 1467',
    #]
response = rally.get('UserStory',query=q,fetch="FormattedID,ObjectID,Name,PlanEstimate,c_BusinessValueBV,ScheduleStatePrefix,Package,Project,Feature,c_SolutionSize,c_Stakeholders,Iteration,Release,Tags,RevisionHistory",order="FormattedID")

if response.resultCount == 0:
    print "Cannot find any stories in the backlog!"
    print response.errors
    sys.exit(1)

for story in response:

    this=getStory(story.FormattedID)
    if this == None:
      # Create new instance
        createStory(story, session)
    else:
        updateStory(this, story, session)
# Query items not already updated and update them
stories = Story.objects.filter(~Q(session=session) | Q(session__isnull=True), Q(release__status__in=['Active','Planning']) | Q(release=None))
for this in stories:
    q = ['FormattedId = "%s"' % this.rallyNumber]
    response = rally.get('UserStory',query=q,fetch="FormattedID,ObjectID,Name,PlanEstimate,c_BusinessValueBV,ScheduleStatePrefix,Project,Package,Feature,c_SolutionSize,c_Stakeholders,Iteration,Release,Tags,RevisionHistory",order="FormattedID")

    for story in response:
        updateStory(this, story, session)

session.close()
