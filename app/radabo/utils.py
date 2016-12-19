import os
import re

from django.db.models import Q
from django.utils import timezone
from pyral import Rally, rallyWorkset
from datetime import datetime, timedelta
from dateutil.parser import parse

from radabo.models import Sprint, Story, Release, Session, Module

_ENH = "F1467"
_PRJ = "F3841"
_OPER = "E258"
_NONFIN = "F5275"

__all__ = [
           'getSprintList',
           'getReleaseList',
           'getCurrentSprint',
           'getCurrentRelease',
           'getOrCreateStory',
           'getEpics',
           'getProjectStories',
           'getPriorRelease',
           'getSprint',
           'getModuleList',
           'getAllStoriesInSprint',
           'createStory',
           'updateStory',
          ]

"""
Functions for internal use only, not defined in __all__
"""
def _getApiKey():
    """
    Find the Rally WSAPI key ... I will be glad to move to OpenShift v3 and
    get rid of all but the first option
    """
    if 'DJANGO_SECRET_DIR' in os.environ:
        api_key = open(os.path.join(os.environ.get('DJANGO_SECRET_DIR'),'.rally')).read().strip()
    elif 'OPENSHIFT_HOMEDIR' in os.environ:
        api_key = open(os.path.expanduser('~/app-root/repo/wsgi/xfr/metrics/.rally')).read().strip()
    else:
        api_key = open(os.path.expanduser('~/.rally')).read().strip()

    return api_key
    
def _getProjectID(projectWSURL):
    """
    Function used to identify the project id to build a URL for the story.
    """
    projectMatch = re.search(r'\d+$',projectWSURL)
    return projectMatch.group(0)

def _getStoryURL(projectID, storyID):
    """
    Function that builds the URL based on projectID returned by _getProjectID()
    """
    return ("https://rally1.rallydev.com/#/" 
           + str(projectID) 
           + "d/detail/userstory/"
           + str(storyID))

def _getSolutionSize(points, verbiage):
    """
    Function that returns solution size based on the story point estimate where
    available.  Otherwise, the original S/M/L estimate is returned.  If no
    sizing was ever done, Unknown is returned.
    """
    if not points:
       solSize = verbiage if verbiage else 'Unknown'
    elif points <= 3:
       solSize = "Small"
    elif points <= 8:
       solSize = "Medium"
    elif points <= 99:
       solSize = "Large"

    return solSize

def _getLongDesc(text):
    """
    Function that parses the long description and ensures it fits within the
    2000 character limit.
    """
    x=re.sub(r'<b>(<[\w\s]+/>)?Solution.*$','',text)
    if len(x) > 2000:
        return x[:1997]+"...".decode('utf-8')
    else:
        return x.decode('utf-8')

def _getEpicID(featureID):
    """ 
    Hacky workaround to the fact that Story.Feature.Parent.FormattedID
    references fail
    """
    try:
        s=initRally()
        f="FormattedID,Parent"
        q='FormattedID = "%s"' % (featureID)
        data=s.get('Feature',query=q,fetch=f)
        if data.resultCount == 1:
            for x in data:
                epicID = x.Parent.FormattedID
        else:
            epicID = None

        return epicID
    except:
        return None
def _getFeatureDesc(feature):
    """
    Function that sets storyType based on the Feature Parent FormattedID.
    There is a bug in pyral where direct references don't work.  Management
    command updateStory specifically looks for E258/_OPER and sets this 
    before calling utils package.  The sync story page doesn't have this luxury.
    _getEpicID hacked in for now
    """
    try:
        epic = feature.Parent.FormattedID
    except:
        # TODO figure out how to work around bug for generic stories
        try:
            epic = _getEpicID(feature.FormattedID)
        except:
            epic = _OPER

    if epic == _OPER:
        if feature.FormattedID == _PRJ:
            return "Project Grooming"
        elif feature.FormattedID == _NONFIN:
            return "Non-Finance"
        else:
            return "Enhancement"
    else:
        return "Project Deliverable"

def _fetchStoryFromRally(storyNumber):
    """
    Function that will get the information for a single story from Rally.
    """
    try:
        rally = initRally()
        q="FormattedID = %s" % (storyNumber)
        f="FormattedID,ObjectID,Name,Description,PlanEstimate," \
          "c_BusinessValueBV,ScheduleStatePrefix,c_Module,Project,Feature," \
          "c_SolutionSize,c_Stakeholders,Iteration,Release,Tags," \
          "RevisionHistory,c_Theme,Blocked,BlockedReason,CreationDate," \
          "c_Region,Ready"

        response=rally.get(
                     'UserStory',
                     query=q,
                     fetch=f)

    except Exception as e:
        raise Exception(e)

    if response.resultCount == 0:
        raise Exception("User story %s not found." % (storyNumber))

    return response

def _workDaysInRange(fromDate, toDate):
    """
    Function that determines the number of work days between start and end
    date.  This function adds one to resolve the fence-post issue (29 Aug - 29
    Aug is 1 day, not 0).
    """
    fromWorkday = fromDate.weekday()
    toWorkday = toDate.weekday()
    # if start or end date is after Friday, modify it to Monday
    if fromWorkday > 5:
        fromWorkday = 0
    if toWorkday > 5:
        toWorkday = 0

    dayDiff = toWorkday - fromWorkday
    weeks = ((toDate - fromDate).days - dayDiff) / 7
    days1 = weeks * 5
    correction = min(dayDiff,5) - (max(toDate.weekday() - 4,0) % 5) + 1
    days = days1 + correction
    return days

def _calculateProgress(story):
    """
    Function that implements logic documented at
    https://help.rallydev.com/track-portfolio-items
    This defines the progress of a project based on the % complete by story
    count and where we are in the project duration.
    """

    today = datetime.now()
    pctComplete = 100 * story.PercentDoneByStoryCount

    if story.ActualStartDate:
        startDate = parse(story.ActualStartDate, ignoretz=True)
    elif story.PlannedStartDate:
        startDate = parse(story.PlannedStartDate, ignoretz=True)
    else:
        startDate = today

    if pctComplete == 100:
        if story.ActualEndDate:
            endDate = parse(story.ActualEndDate, ignoretz=True)
        elif story.PlannedEndDate:
            endDate = parse(story.PlannedEndDate, ignoretz=True)
        else:
            endDate = today
    else:
        if story.PlannedEndDate:
            endDate = parse(story.PlannedEndDate, ignoretz=True)
        else:
            endDate = today
        
    totalDuration = _workDaysInRange(endDate, startDate)
    elapsedDuration = _workDaysInRange(today, startDate)
    acceptanceStartDelay = totalDuration * 0.2
    warningDelay = totalDuration * 0.2
    elapsedPct = int(100 * elapsedDuration / totalDuration)
    rv = {
       'startDate': startDate,
       'endDate': endDate,
       'elapsed': elapsedPct,
    }

    if today < startDate:
        rv.update({'color':'progress-bar-purple'})
        return rv

    if today >= endDate:
        if pctComplete >= 100.0:
            rv.update({'color':'progress-bar-blue'})
            return rv
        else:
            rv.update({'color':'progress-bar-red'})
            return rv

    redXIntercept = 1 + acceptanceStartDelay + warningDelay
    redSlope = 100.0 / (totalDuration - redXIntercept)
    redYIntercept = -1.0 * redXIntercept * redSlope
    redThreshold = redSlope * elapsedDuration + redYIntercept
    if pctComplete < redThreshold:
        rv.update({'color':'progress-bar-red'})
        return rv

    yellowXIntercept = 1 + acceptanceStartDelay
    yellowSlope = 100.0 / (totalDuration - yellowXIntercept)
    yellowYIntercept = -1.0 * yellowXIntercept * yellowSlope
    yellowThreshold = yellowSlope * elapsedDuration + yellowYIntercept
    if pctComplete < yellowThreshold:
        rv.update({'color':'progress-bar-yellow'})
        return rv

    rv.update({'color':'progress-bar-green'})
    return rv

"""
Public methods exposed in __all__
"""
def initRally():
    """
    Convenience function to get WSAPI key and instantiate a server instance
    """
    try:
        api_key = _getApiKey()
    except Exception as e:
        raise Exception("Cannot read api key from file: %s." % (str(e)))

    try:
        rallyServer = rallyWorkset([])[0]
        ws='Red Hat IT Workspace'
        prj='IT Finance and GWS (855)'
        rally = Rally(rallyServer, apikey = api_key, workspace=ws, project=prj, user=None, password=None)
    except Exception as e:
        raise Exception("Unexpected error contacting Rally: %s." % (str(e)))

    return rally

def closeSession(session):
    """
    Function to set the end of a session used in updateStory.py
    """
    session.endDate = timezone.now()
    session.save()

def getSprint(name):
    """
    Function that returns a sprint object based on the name returned by Rally
    in Iteration.Name
    """
    try:
        return Sprint.objects.get(name=name)
    except Sprint.DoesNotExist:
        return None

def getStory(name):
    """
    Function that returns a story object based on the rallyNumber/FormattedID
    """
    try:
        return Story.objects.get(rallyNumber=name)
    except Story.DoesNotExist:
        return None

def getRelease(name):
    """
    Function that returns an iteration object based on the name returned 
    by Rally in Release.Name
    """
    try:
        return Release.objects.get(name=name)
    except Release.DoesNotExist:
        return None

def getCurrentSprint():
    """
    Function that returns the active sprint, based on now() being between the
    start and end date
    """
    now = timezone.now()
    try:
        return Sprint.objects.get(startDate__lte=now,endDate__gte=now)
    except Sprint.DoesNotExist:
        return None

def getCurrentRelease():
    """
    Function that returns the active release, based on now() being between the
    start and end date
    """
    now = timezone.now()
    try:
        return Release.objects.get(startDate__lte=now,endDate__gte=now)
    except Release.DoesNotExist:
        return None

def getModule(name):
    """
    Function that returns a module object based on the name returned by rally
    in c_Module
    """
    try:
        return Module.objects.get(moduleName=name)
    except:
        return None

def getPriorSprint():
    """
    Function that returns the sprint before the current one.  This is not 
    currently used, but is included as a partner to getPriorRelease.
    """
    try:
        cur = getCurrentSprint()
        return (Sprint.objects.filter(endDate__lt=cur.startDate)
                .order_by('-startDate')[0])
    except Sprint.DoesNotExist:
        return None

def getPriorRelease():
    """
    Function that returns the release before the current one.  This is used as
    a default on the Enhancement Release page, as this is likely the most
    recent Accepted release.
    """
    try:
        cur = getCurrentRelease()
        return (Release.objects.filter(endDate__lt=cur.startDate)
                .order_by('-startDate')[0])
    except Release.DoesNotExist:
        return None

def getReleaseList():
    """
    Function that returns a list of Release names for creating the dropdown
    selector list.
    """
    try:
        t=timezone.now() + timedelta(days=-182)
        return (Release.objects.filter(startDate__gte=t)
                .values_list('name',flat=True).order_by('-startDate'))
    except:
        return None

def getSprintList():
    """
    Function that returns a list of Sprint names for creating the dropdown
    selector list.
    """
    try:
        t=timezone.now() + timedelta(days=-91)
        return (Sprint.objects.filter(startDate__gte=t)
                .values_list('name',flat=True).order_by('-startDate'))
    except:
        return None

def getModuleList():
    """
    Function that returns a list of Module names for creating the dropdown
    selector list.
    """
    try:
        return (Module.objects.all().values_list('moduleName',flat=True)
                .order_by('moduleName'))
    except:
        return None

def createStory(story,session):
    """
    Function that will create a new Story object in the local DB if it does
    not already exist.
    """
    solSize = _getSolutionSize(story.PlanEstimate, story.c_SolutionSize)
    tag=story.Tags[0].Name if story.Tags else None

    projectID = _getProjectID(story.Project._ref)
    storyURL = _getStoryURL(projectID, story.ObjectID)
    module = getModule(story.c_Module)
    sprint = None
    release = None
    if story.Release:
        release = getRelease(story.Release.Name)
    if story.Iteration:
        sprint = getSprint(story.Iteration.Name)
        
    print "Creating " + story.FormattedID
    this = Story(rallyNumber=story.FormattedID,
                 description=story.Name,
                 longDescription=_getLongDesc(story.Description),
                 storyType=_getFeatureDesc(story.Feature),
                 points=story.PlanEstimate,
                 businessValue=story.c_BusinessValueBV,
                 status=story.ScheduleStatePrefix,                   
                 module=module,
                 theme=story.c_Theme,
                 stakeholders=story.c_Stakeholders,
                 solutionSize=solSize,
                 initialSprint=sprint,
                 currentSprint=sprint,
                 release=release,
                 region=story.c_Region,
                 rallyCreationDate=story.CreationDate,
                 blocked="Y" if story.Blocked else "N",
                 track=tag,
                 session=session,
                 storyURL=storyURL,
                 ready='Y' if story.Ready else 'N',
                 blockedReason=story.BlockedReason)
    this.save()

def updateStory(this, that, session):
    """
    Function that updates an existing Story object with the latest details.
    """
    projectID = _getProjectID(that.Project._ref)
    storyURL = _getStoryURL(projectID, that.ObjectID)
    module = getModule(that.c_Module)

    print "Updating %s" % (this.rallyNumber)

    this.description = that.Name
    this.longDescription = _getLongDesc(that.Description)
    this.storyType = _getFeatureDesc(that.Feature)
    this.points = that.PlanEstimate
    this.businessValue = that.c_BusinessValueBV
    this.status = that.ScheduleStatePrefix
    this.module = module
    this.theme = that.c_Theme
    this.stakeholders = that.c_Stakeholders
    this.solutionSize = _getSolutionSize(that.PlanEstimate, that.c_SolutionSize)
    this.blocked = "Y" if that.Blocked else "N"
    this.blockedReason = that.BlockedReason
    this.session = session
    this.storyURL = storyURL
    this.ready = "Y" if that.Ready else "N"
    this.region = that.c_Region
    this.rallyCreationDate = that.CreationDate
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
    """
    Function used by the Sync Story form.  It calls _fetchStoryFromRally() and
    will then call createStory() or updateStory() as needed.
    """
    try:
        session = Session()
        session.save()
    except:
        return 'N', "Create session failed."

    try:
        response = _fetchStoryFromRally(storyNumber)
    except Exception as e:
        return 'N', e

    for story in response:
        this=getStory(story.FormattedID)
        try:
            if this == None:
                createStory(story, session)
            else:
                updateStory(this, story, session)
        except Exception as e:
            action = "update" if this else "create"
            return 'N', "Failed to %s story: %s" % (action, str(e))

    session.close()
    return 'Y', "Success!"

def storyDetail(storyNumber):
    """
    This function will fetch a single story from Rally and pull out the long
    description.  It is not currently being used as this was added to the
    database on createStory() or updateStory().  It could be used if someone
    wants to make that function dynamic.
    """
    try:
        response = _fetchStoryFromRally(storyNumber)
    except Exception as e:
        return 'N', e

    text = response.next().Description
    return 'Y', text

def getEpics():
    """
    Function that fetches projects from the portfolio hierarchy which are in
    progress.
    """
    try:
        rally = initRally()
    except Exception as e:
        return 'N', None

    try:
        #E258 is the "project" that is the parent to all enhancements (F1467)
        q=['Parent.FormattedId = "I68"',
           'State.Name != "Done"',
           'FormattedID != "E258"',
          ]
        f="FormattedID,Name,State,PercentDoneByStoryCount,LeafStoryCount," \
          "c_Region,c_ProjectManager,c_Requester,PlannedStartDate," \
          "PlannedEndDate,ActualStartDate,ActualEndDate"
        # pyral 1.2.0 changed the item type to BusinessEpic
        data = rally.get(
                   'BusinessEpic', 
                   query=q, 
                   fetch=f,
                   order="PlannedEndDate")
    except Exception as e:
        return str(e), None

    results = []
    for item in data:
        if item.State != None:
            # Allow use of Undefined State to block RADABO from displaying.
            # Useful for projects put on hold.
            rec = _calculateProgress(item)

            rec.update({
                "id": item.FormattedID,
                "name": item.Name,
                "percent": int(round(item.PercentDoneByStoryCount*100,0)),
                "count": item.LeafStoryCount,
                "status": item.State.Name,
                "region": item.c_Region,
                "sponsor": item.c_Requester,
                "pm": item.c_ProjectManager,
            })
            results.append(rec)

    return 'Y', results
        
def getProjectStories(epic):
    """
    Function that will get all stories belonging to the specified project/epic.
    """
    try:
        rally = initRally()
    except Exception as e:
        return 'N', str(e)

    """
    TODO
    Currently, any exception encountered just gets you redirected to the
    generic error page.  I should fix that some day.
    """
    """
    2016-12-12 - pyral 1.2.2 no longer likes reference to BusinessEpic
    level from User Story.  Will look up name separately based on epic
    """

    try:
        q='FormattedId = "%s"' % (epic)
        f="Name"
        data = rally.get(
            'BusinessEpic',
            query=q,
            fetch=f)
    except Exception as e:
        return 'N', str(e)

    if data.resultCount == 0:
        return 'N', "Invalid project identifier: %s" % (epic)

    prj = data.next()
    project = str(prj.Name)

    try:
        q='Feature.Parent.FormattedId = "%s"' % (epic)
        f="FormattedID,Name,ScheduleState,PlanEstimate,Feature,Owner"
        data = rally.get(
            'User Story',
            query=q, 
            fetch=f,
            order="Feature")
    except Exception as e:
        return 'N', str(e)

    if data.resultCount == 0:
        return 'N', "Invalid project identifier: %s" % (epic)

    results = []
    for item in data:
        rec = {
            'id': item.FormattedID,
            'feature': item.Feature.Name,
            'featureid': item.Feature.FormattedID,
            'project': project,
            'name': item.Name,
            'status': item.ScheduleState,
            'points': int(item.PlanEstimate) if item.PlanEstimate else 0,
            'owner': item.Owner.Name,
        }
        results.append(rec)

    return 'Y', results

def getAllStoriesInSprint(sprint):
    """
    Function to get a consolidated list of all stories being worked in the
    specified sprint
    """
    try:
        rally = initRally()
    except Exception as e:
        return 'N', str(e)

    try:
        q=['Iteration.Name = "%s"' % (sprint)]
        f='FormattedID,Name,Project,ScheduleState,PlanEstimate'
        o='Project.Name'
        data=rally.get(
                 'UserStory',
                 query=q,
                 fetch=f,
                 order=o)
    except Exception as e:
        return 'N', str(e)

    if data.resultCount == 0:
        return 'N', None

    results = []
    for item in data:
        if item.Project.Name == "Team: IT Finance":
            project = "Enhancements"
        else:
            project = item.Project.Name
        rec = {
            'id': item.FormattedID,
            'name': item.Name,
            'project': project,
            'status': item.ScheduleState,
            'points': int(item.PlanEstimate) if item.PlanEstimate else 0,
        }
        results.append(rec)

    return 'Y', results
