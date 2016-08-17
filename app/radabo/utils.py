import os, re
from radabo.models import Sprint, Story, Release, Session, Module
from django.db.models import Q
from django.utils import timezone
from pyral import Rally, rallyWorkset
from datetime import datetime, timedelta

_ENH = "F1467"
_PRJ = "F3841"

def getApiKey():
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
    
def initRally():
    """
    Convenience function to get WSAPI key and instantiate a server instance
    """
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
        return Sprint.objects.filter(endDate__lt=cur.startDate).order_by('-startDate')[0]
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
        return Release.objects.filter(endDate__lt=cur.startDate).order_by('-startDate')[0]
    except Release.DoesNotExist:
        return None

def getReleaseList():
    """
    Function that returns a list of Release names for creating the dropdown
    selector list.
    """
    try:
        t=timezone.now() + timedelta(days=-182)
        return Release.objects.filter(startDate__gte=t).values_list('name',flat=True).order_by('-startDate')
    except:
        return None

def getSprintList():
    """
    Function that returns a list of Sprint names for creating the dropdown
    selector list.
    """
    try:
        t=timezone.now() + timedelta(days=-91)
        return Sprint.objects.filter(startDate__gte=t).values_list('name',flat=True).order_by('-startDate')
    except:
        return None

def getModuleList():
    """
    Function that returns a list of Module names for creating the dropdown
    selector list.
    """
    try:
        return Module.objects.all().values_list('moduleName',flat=True).order_by('moduleName')
    except:
        return None

def getProjectID(projectWSURL):
    """
    Function used to identify the project id to build a URL for the story.
    """
    projectMatch = re.search(r'\d+$',projectWSURL)
    return projectMatch.group(0)

def getStoryURL(projectID, storyID):
    """
    Function that builds the URL based on projectID returned by getProjectID()
    """
    return "https://rally1.rallydev.com/#/" + str(projectID) + "d/detail/userstory/"+ str(storyID)

def getSolutionSize(points, verbiage):
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

def getFeatureDesc(text):
    """
    Function that sets storyType based on the Feature.FormattedID value.
    """
    if text == _ENH:
        return "Enhancement"
    elif text == _PRJ:
        return "Project Grooming"
    else:
        return "Project Deliverable"

def getLongDesc(text):
    """
    Function that parses the long description and ensures it fits within the
    2000 character limit.
    """
    x=re.sub(r'<b>Solution.*$','',text)
    if len(x) > 2000:
        return x[:1997]+"...".decode('utf-8')
    else:
        return x.decode('utf-8')

def createStory(story,session):
    """
    Function that will create a new Story object in the local DB if it does
    not already exist.
    """
    solSize = getSolutionSize(story.PlanEstimate, story.c_SolutionSize)
    tag=story.Tags[0].Name if story.Tags else None

    projectID = getProjectID(story.Project._ref)
    storyURL = getStoryURL(projectID, story.ObjectID)
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
                 longDescription=getLongDesc(story.Description),
                 storyType=getFeatureDesc(story.Feature.FormattedID),
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
                 rallyCreationDate=story.CreationDate,
                 blocked="Y" if story.Blocked else "N",
                 track=tag,
                 session=session,
                 storyURL=storyURL,
                 blockedReason=story.BlockedReason)
    this.save()

def updateStory(this, that, session):
    """
    Function that updates an existing Story object with the latest details.
    """
    projectID = getProjectID(that.Project._ref)
    storyURL = getStoryURL(projectID, that.ObjectID)
    module = getModule(that.c_Module)

    print "Updating %s" % (this.rallyNumber)

    this.description = that.Name
    this.longDescription = getLongDesc(that.Description)
    this.storyType = getFeatureDesc(that.Feature.FormattedID)
    this.points = that.PlanEstimate
    this.businessValue = that.c_BusinessValueBV
    this.status = that.ScheduleStatePrefix
    this.module = module
    this.theme = that.c_Theme
    this.stakeholders = that.c_Stakeholders
    this.solutionSize = getSolutionSize(that.PlanEstimate, that.c_SolutionSize)
    this.blocked = "Y" if that.Blocked else "N"
    this.blockedReason = that.BlockedReason
    this.session = session
    this.storyURL = storyURL
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

def fetchStoryFromRally(storyNumber):
    """
    Function that will get the information for a single story from Rally.
    """
    try:
        rally = initRally()
        q="FormattedID = %s" % (storyNumber)
        f="FormattedID,ObjectID,Name,Description,PlanEstimate,c_BusinessValueBV,ScheduleStatePrefix,c_Module,Project,Feature,c_SolutionSize,c_Stakeholders,Iteration,Release,Tags,RevisionHistory,c_Theme,Blocked,BlockedReason,CreationDate"

        response=rally.get(
                     'UserStory',
                     query=q,
                     fetch=f)

    except Exception as e:
        raise Exception(e)

    if response.resultCount == 0:
        raise Exception("User story %s not found." % (storyNumber))

    return response

def getOrCreateStory(storyNumber):
    """
    Function used by the Sync Story form.  It calls fetchStoryFromRally() and
    will then call createStory() or updateStory() as needed.
    """
    try:
        session = Session()
        session.save()
    except:
        return 'N', "Create session failed."

    try:
        response = fetchStoryFromRally(storyNumber)
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
        response = fetchStoryFromRally(storyNumber)
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
        f="FormattedID,Name,State,PercentDoneByStoryCount,LeafStoryCount,c_Region,c_ProjectManager,c_Requester"
        data = rally.get(
                   'PortfolioItem/BusinessEpic', 
                   query=q, 
                   fetch=f,
                   order="FormattedID")
    except Exception as e:
        return str(e), None

    results = []
    for item in data:
        if item.State != None:
            status = item.State.Name
        else:
            status = 'Undefined'
        rec = {
            'id': item.FormattedID,
            'name': item.Name,
            'percent': int(round(item.PercentDoneByStoryCount*100,0)),
            'count': item.LeafStoryCount,
            'status': status,
            'region': item.c_Region,
            'sponsor': item.c_Requester,
            'pm': item.c_ProjectManager,
        }
        results.append(rec)

    return 'Y', results
        
def getProjectStories(epic):
    """
    Function that will get all stories belonging to the specified project/epic.
    """
    try:
        rally = initRally()
    except Exception as e:
        return 'N', None

    """
    TODO
    Currently, any exception encountered just gets you redirected to the
    generic error page.  I should fix that some day.
    """
    try:
        q=['Feature.Parent.FormattedId = "%s"' % (epic)]
        data = rally.get('User Story',query=q, fetch="FormattedID,Name,ScheduleState,PlanEstimate,Feature,Owner",order="Feature")
    except Exception as e:
        return str(e), None

    if data.resultCount == 0:
        return "Invalid project identifier: %s" % (epic), None

    results = []
    for item in data:
        rec = {
            'id': item.FormattedID,
            'feature': item.Feature.Name,
            'featureid': item.Feature.FormattedID,
            'project': item.Feature.Parent.Name,
            'name': item.Name,
            'status': item.ScheduleState,
            'points': int(item.PlanEstimate) if item.PlanEstimate else 0,
            'owner': item.Owner.Name,
        }
        results.append(rec)

    return 'Y', results

