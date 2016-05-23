import os, re
from metrics.models import Sprint, Story, Release, Session
from django.db.models import Q
from django.utils import timezone
from pyral import Rally, rallyWorkset

_ENH = "F1467"
_PRJ = "F3841"

def getApiKey():
    if 'RALLY_API_KEY' in os.environ:
        api_key = os.environ['RALLY_API_KEY']
    elif 'OPENSHIFT_HOMEDIR' in os.environ:
        api_key = open(os.path.expanduser('~/app-root/repo/wsgi/xfr/metrics/.rally')).read().strip()
    else:
        api_key = open(os.path.expanduser('~/.rally')).read().strip()

    return api_key
    
def initRally():
    try:
        api_key = getApiKey()
    except Exception as e:
        raise Exception("Cannot read api key from file: %s." % (str(e)))

    try:
        rallyServer = rallyWorkset([])[0]
        rally = Rally(rallyServer, apikey = api_key, user=None, password=None)
    except Exception as e:
        raise Exception("Unexpected error contacting Rally: %s." % (str(e)))

    return rally

def closeSession(session):
    session.endDate = timezone.now()
    session.save()

def getSprint(name):
    try:
        return Sprint.objects.get(name=name)
    except Sprint.DoesNotExist:
        return None

def getStory(name):
    try:
        return Story.objects.get(rallyNumber=name)
    except Story.DoesNotExist:
        return None

def getRelease(name):
    try:
        return Release.objects.get(name=name)
    except Release.DoesNotExist:
        return None

def getCurrentSprint():
    now = timezone.now()
    try:
        return Sprint.objects.get(startDate__lte=now,endDate__gte=now)
    except Sprint.DoesNotExist:
        return None

def getCurrentRelease():
    now = timezone.now()
    try:
        return Release.objects.get(startDate__lte=now,endDate__gte=now)
    except Release.DoesNotExist:
        return None

def getPriorSprint():
    try:
        cur = getCurrentSprint()
        return Sprint.objects.filter(endDate__lt=cur.startDate).order_by('-startDate')[:1]
    except Sprint.DoesNotExist:
        return None

def getReleaseList():
    try:
        return Release.objects.all().values_list('name',flat=True).order_by('-startDate')
    except:
        return None

def getSprintList():
    try:
        return Story.objects.filter(~Q(initialSprint__name=None)).values_list('initialSprint__name',flat=True).distinct().order_by('-initialSprint__id')
    except:
        return None

def getProjectID(projectWSURL):
    projectMatch = re.search(r'\d+$',projectWSURL)
    return projectMatch.group(0)

def getStoryURL(projectID, storyID):
    return "https://rally1.rallydev.com/#/" + str(projectID) + "d/detail/userstory/"+ str(storyID)

def getSolutionSize(points, verbiage):
    if not points:
       solSize = verbiage if verbiage else 'Unknown'
    elif points <= 3:
       solSize = "Small"
    elif points <= 8:
       solSize = "Medium"
    elif points <= 99:
       solSize = "Large"

    return solSize

def getFeatureDesc(text):
    if text == _ENH:
        return "Enhancement"
    elif text == _PRJ:
        return "Project Grooming"
    else:
        return "Project Deliverable"


def createStory(story,session):
    print "Creating " + story.FormattedID

    solSize = getSolutionSize(story.PlanEstimate, story.c_SolutionSize)
    tag=story.Tags[0].Name if story.Tags else None

    projectID = getProjectID(story.Project._ref)
    storyURL = getStoryURL(projectID, story.ObjectID)
    this = Story(rallyNumber=story.FormattedID,
                 description=story.Name,
                 storyType=getFeatureDesc(story.Feature.FormattedID),
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
    this.storyType = getFeatureDesc(that.Feature.FormattedID)
    this.points = that.PlanEstimate
    this.businessValue = that.c_BusinessValueBV
    this.status = that.ScheduleStatePrefix
    this.module = that.Package
    this.stakeholders = that.c_Stakeholders
    this.solutionSize = getSolutionSize(that.PlanEstimate, that.c_SolutionSize)
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

def getOrCreateStory(storyNumber):
    try:
        rally = initRally()
    except Exception as e:
        return 'N', e

    try:
        session = Session()
        session.save()
    except:
        return 'N', "Create session failed."

    try:
        q="FormattedID = %s" % (storyNumber)
        response=rally.get('UserStory',query=q,fetch="FormattedID,ObjectID,Name,PlanEstimate,c_BusinessValueBV,ScheduleStatePrefix,Package,Project,Feature,c_SolutionSize,c_Stakeholders,Iteration,Release,Tags,RevisionHistory")
    except:
        return 'N', "Could not fetch User Story from Rally."

    if response.resultCount == 0:
        return 'N', "User story %s not found." % (storyNumber)

    for story in response:
        this=getStory(story.FormattedID)
        try:
            if this == None:
                createStory(story, session)
            else:
                updateStory(this, story, session)
        except:
            action = "update" if this else "create"
            return 'N', "Failed to %s story." % (action)

    session.close()
    return 'Y', "Success!"
