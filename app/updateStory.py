#!/usr/bin/python

import requests,sys,re,os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rally.settings")
import django
django.setup()
from radabo.models import Story, Session
from radabo.utils import getStory, createStory, updateStory, initRally
from django.utils import timezone
from django.db.models import Q, F

session=Session()
session.save()
rallyServer = initRally()

# Load new backlog items from Rally
q = '((Feature.FormattedID = "1467") AND (Release = "")) OR ((Feature.FormattedID = "3841") AND (c_ITFinanceConsultingKanbanState != "Completed Archive"))'
#q = [
    #'Release = null',
    #'Feature.FormattedID = 1467',
    #]
response = rallyServer.get('UserStory',query=q,fetch="FormattedID,ObjectID,Name,Description,PlanEstimate,c_BusinessValueBV,ScheduleStatePrefix,c_Module,Project,Feature,c_SolutionSize,c_Stakeholders,Iteration,Release,Tags,RevisionHistory,c_Theme,Blocked,BlockedReason",order="FormattedID")

if response.resultCount == 0:
    print "Cannot find any stories in the backlog!"
    print response.errors
    sys.exit(1)

for story in response:

    try:
        this=getStory(story.FormattedID)
        if this == None:
          # Create new instance
            createStory(story, session)
        else:
            updateStory(this, story, session)
    except Exception as e:
        print "Failure on %s with module %s: %s" % (story.FormattedID, story.c_Module, str(e))
        sys.exit(1)

# Query items not already updated and update them
stories = Story.objects.filter(~Q(session=session) | Q(session__isnull=True), Q(release__status__in=['Active','Planning']) | Q(release=None))
for this in stories:
    q = ['FormattedId = "%s"' % this.rallyNumber]
    response = rallyServer.get('UserStory',query=q,fetch="FormattedID,ObjectID,Name,Description,PlanEstimate,c_BusinessValueBV,ScheduleStatePrefix,Project,c_Module,Feature,c_SolutionSize,c_Stakeholders,Iteration,Release,Tags,RevisionHistory,c_ITFinanceConsultingKanbanState,c_Theme,Blocked,BlockedReason",order="FormattedID")

    if response.resultCount == 0:
        print "Deleting %s" % (this.rallyNumber)
        this.delete()
    else:
        for story in response:
            if story.c_ITFinanceConsultingKanbanState == "Completed Archive":
                print "Deleting archived story %s" % (story.FormattedID)
                this.delete()
            else:
                print "Updating %s with release %s" % (story.FormattedID, (story.Release.Name if story.Release else 'No data'))
                updateStory(this, story, session)

session.close()
