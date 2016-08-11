import os, re
from radabo.models import Sprint, Story, Release, Session, Module
from django.db.models import Q
from django.utils import timezone
from pyral import Rally, rallyWorkset
from datetime import datetime, timedelta

_ENH = "F1467"
_PRJ = "F3841"

def getApiKey():
    if 'DJANGO_SECRET_DIR' in os.environ:
        api_key = open(os.path.join(os.environ.get('DJANGO_SECRET_DIR'),'.rally')).read().strip()
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

def getModule(name):
    try:
        return Module.objects.get(moduleName=name)
    except:
        return None

def getPriorSprint():
    try:
        cur = getCurrentSprint()
        return Sprint.objects.filter(endDate__lt=cur.startDate).order_by('-startDate')[0]
    except Sprint.DoesNotExist:
        return None

def getPriorRelease():
    try:
        cur = getCurrentRelease()
        return Release.objects.filter(endDate__lt=cur.startDate).order_by('-startDate')[0]
    except Release.DoesNotExist:
        return None

def getReleaseList():
    try:
        t=timezone.now() + timedelta(days=-182)
        return Release.objects.filter(startDate__gte=t).values_list('name',flat=True).order_by('-startDate')
    except:
        return None

def getSprintList():
    try:
        t=timezone.now() + timedelta(days=-91)
        return Sprint.objects.filter(startDate__gte=t).values_list('name',flat=True).order_by('-startDate')
    except:
        return None

def getModuleList():
    try:
        return Module.objects.all().values_list('moduleName',flat=True).order_by('moduleName')
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

def getLongDesc(text):
    x=re.sub(r'<b>Solution.*$','',text)
    if len(x) > 2000:
        return x[:1997]+"...".decode('utf-8')
    else:
        return x.decode('utf-8')

def createStory(story,session):

    solSize = getSolutionSize(story.PlanEstimate, story.c_SolutionSize)
    tag=story.Tags[0].Name if story.Tags else None

    projectID = getProjectID(story.Project._ref)
    storyURL = getStoryURL(projectID, story.ObjectID)
    module = getModule(story.c_Module)
        
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
                 blocked="Y" if story.Blocked else "N",
                 track=tag,
                 session=session,
                 storyURL=storyURL,
                 blockedReason=story.BlockedReason)
    this.save()

def updateStory(this, that, session):
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
    try:
        rally = initRally()
        q="FormattedID = %s" % (storyNumber)
        response=rally.get('UserStory',query=q,fetch="FormattedID,ObjectID,Name,Description,PlanEstimate,c_BusinessValueBV,ScheduleStatePrefix,c_Module,Project,Feature,c_SolutionSize,c_Stakeholders,Iteration,Release,Tags,RevisionHistory,c_Theme,Blocked,BlockedReason")

    except Exception as e:
        raise Exception(e)

    if response.resultCount == 0:
        raise Exception("User story %s not found." % (storyNumber))

    return response

def getOrCreateStory(storyNumber):
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
        except:
            action = "update" if this else "create"
            return 'N', "Failed to %s story." % (action)

    session.close()
    return 'Y', "Success!"

def storyDetail(storyNumber):
    try:
        response = fetchStoryFromRally(storyNumber)
    except Exception as e:
        return 'N', e

    text = response.next().Description
    return 'Y', text

def getEpics():
    try:
        rally = initRally()
    except Exception as e:
        return 'N', None

    try:
        q=['Parent.FormattedId = "I68"',
           'State.Name != "Done"',
           'FormattedID != "E258"',
          ]
        data = rally.get('PortfolioItem/BusinessEpic', query=q, fetch="FormattedID,Name,State,PercentDoneByStoryCount,LeafStoryCount")
    except Exception as e:
        return str(e), None

    results = []
    for item in data:
        rec = {}
        if item.State != None:
            rec['status'] = item.State.Name
        else:
            rec['status'] = 'Undefined'
        rec['id'] = item.FormattedID
        rec['name'] = item.Name
        rec['percent'] = int(round(item.PercentDoneByStoryCount*100,0))
        rec['count'] = item.LeafStoryCount
        results.append(rec)

    return 'Y', results
        
def getProjectStories(epic):
    try:
        rally = initRally()
    except Exception as e:
        return 'N', None

    try:
        q=['Feature.Parent.FormattedId = "%s"' % (epic)]
        data = rally.get('User Story',query=q, fetch="FormattedID,Name,ScheduleState,PlanEstimate,Feature,Owner",order="Feature")
    except Exception as e:
        return str(e), None

    results = []
    for item in data:
        rec = {}
        rec['id'] = item.FormattedID
        rec['feature'] = item.Feature.Name
        rec['featureid'] = item.Feature.FormattedID
        rec['project'] = item.Feature.Parent.Name
        rec['name'] = item.Name
        rec['status'] = item.ScheduleState
        rec['points'] = int(item.PlanEstimate) if item.PlanEstimate else 0
        rec['owner'] = item.Owner.Name
        results.append(rec)

    return 'Y', results

