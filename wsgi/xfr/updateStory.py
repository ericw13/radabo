#!/usr/bin/python

import requests,sys,re,os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "xfr.settings")
import django
django.setup()
from metrics.models import Story, Session
from metrics.utils import getStory, getSprint, getRelease
from pyral import Rally, rallyWorkset
from rallyUtil import get_api_key
from django.utils import timezone
from django.db.models import Q, F

def getProjectID(projectWSURL):
    projectMatch = re.search(r'\d+$',projectWSURL)
    return projectMatch.group(0)

def getStoryURL(projectID, storyID):
    return "https://rally1.rallydev.com/#/" + str(projectID) + "d/detail/userstory/"+ str(storyID)

def getSolutionSize(points):
    if not points:
       solSize = story.c_SolutionSize if story.c_SolutionSize else 'Unknown'
    elif points <= 3:
       solSize = "Small"
    elif points <= 8:
       solSize = "Medium"
    elif points <= 99:
       solSize = "Large"

    return solSize


def createStory(story,session):
    print "Creating " + story.FormattedID

    solSize = getSolutionSize(story.PlanEstimate)
    tag=story.Tags[0].Name if story.Tags else None

    projectID = getProjectID(story.Project._ref)
    storyURL = getStoryURL(projectID, story.ObjectID)
    this = Story(rallyNumber=story.FormattedID,
                 description=story.Name,
                 points=story.PlanEstimate,
                 businessValue=story.c_BusinessValueBV,
                 status=story.ScheduleStatePrefix,                   
                 module=story.Package,
                 stakeholders=story.c_Stakeholders,
                 solutionSize=solSize,
                 track=tag,
                 session=session,
                 storyURL=storyURL)
    this.save()

def updateStory(this, that, session):
    projectID = getProjectID(that.Project._ref)
    storyURL = getStoryURL(projectID, that.ObjectID)
    print "Updating %s" % (this.rallyNumber)

    this.description = that.Name
    this.points = that.PlanEstimate
    this.businessValue = that.c_BusinessValueBV
    this.status = that.ScheduleStatePrefix
    this.module = that.Package
    this.stakeholders = that.c_Stakeholders
    this.solutionSize = getSolutionSize(that.PlanEstimate)
    this.session = session
    this.storyURL = storyURL
    if that.Iteration:
        this.currentSprint = getSprint(that.Iteration.Name)
    if this.initialSprint == None:
        this.initialSprint = this.currentSprint
    if that.Release:
        this.release = getRelease(that.Release.Name)
    if that.Tags:
        this.track = that.Tags[0].Name
    if this.status in ['B','D','P']:
        this.completionDate = None
    elif this.status in ['C','A'] and this.completionDate == None:
        for rec in that.RevisionHistory.Revisions:
            if re.match(r'.*?SCHEDULE STATE changed.*to \[Completed\]', rec.Description):
                this.completionDate = rec.CreationDate
                break
    this.save()

session=Session(startDate=timezone.now())
session.save()

api_key = get_api_key()
rallyServer = rallyWorkset([])[0]
rally = Rally(rallyServer, apikey = api_key, user=None, password=None)

# Load new backlog items from Rally
q = [
    'Release = null',
    'Feature.FormattedID = 1467',
    ]
response = rally.get('UserStory',query=q,fetch="FormattedID,ObjectID,Name,PlanEstimate,c_BusinessValueBV,ScheduleStatePrefix,Package,Project,c_SolutionSize,c_Stakeholders,Iteration,Release,Tags,RevisionHistory",order="FormattedID")

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
    response = rally.get('UserStory',query=q,fetch="FormattedID,ObjectID,Name,PlanEstimate,c_BusinessValueBV,ScheduleStatePrefix,Project,Package,c_SolutionSize,c_Stakeholders,Iteration,Release,Tags,RevisionHistory",order="FormattedID")

    for story in response:
        updateStory(this, story, session)

session.endDate = timezone.now()
session.save()
