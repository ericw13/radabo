import re,json
import cStringIO as StringIO
from django.shortcuts import render, render_to_response
from django.http import HttpResponse
from metrics.models import Sprint, Story, Release
from metrics.utils import getSprintList, getReleaseList, getCurrentSprint, getCurrentRelease, getOrCreateStory, getEpics, getProjectStories, getPriorRelease, getSprint
from metrics.forms import SearchForm
from django.utils import timezone
from django.views import generic
from django.db.models import F, Q, Avg, Count
from django.template import Context
from django.template.loader import get_template
from datetime import timedelta

# Utility functions
def _getValue(inputs, key):
    if key in inputs and inputs[key]:
        return inputs[key]
    else:
        return None

# Create your views here.
def index(request):
    return render(request, 'metrics/index.html', {})

def routeToError(request):
    return render(request,'metrics/error.html', {})

def _drawVelocity(request, kwargs, template):

    results=Sprint.objects.filter(**kwargs).order_by('startDate').values('name','velocity')[:24]
    avg = results.aggregate(Avg('velocity'))['velocity__avg']
    c = {'velocity':
         json.dumps([dict(item) for item in results]),
         'avg': avg}
    return render_to_response(template, c)

def VelocityChart(request):
    kwargs = {
        'status': 'Accepted',
        'startDate__gte': '2016-06-01 00:00:00',
    }
    return _drawVelocity(request, kwargs, 'metrics/velocity.html')

def OldVelocityChart(request):
    kwargs = {
        'status': 'Accepted',
        'startDate__gte': '2015-09-01 00:00:00',
        'endDate__lte': '2016-06-10 00:00:00',
    }
    return _drawVelocity(request, kwargs, 'metrics/month_velocity.html')

def DelayedItems(request):
    dateLimit = timezone.now() + timedelta(days=-365)
    args = ( 
        ~Q(initialSprint=F('currentSprint') ), 
    )
    kwargs = {
        'initialSprint__startDate__gte': dateLimit,
        'storyType': 'Enhancement',
    }
    results=Story.objects.filter(*args, **kwargs).order_by('initialSprint__id')
    c = {'story': results}
    return render_to_response('metrics/lateStories.html',c)

def Success(request):
    sprints=getSprintList()
    sprintName=None 
    default="Last Six Months"
    if request.method == 'POST':
        sprintName = getValue(request.POST,'sprintSelect')
    if sprintName == None:
        sprintName = default

    kwargs = {
        'storyType': 'Enhancement',
    }
    if sprintName == default:
        start = timezone.now() + timedelta(days=-182)
        l=Sprint.objects.filter(status='Accepted',startDate__gte=start)
        kwargs.update({'initialSprint__in': l})
    else:
        kwargs.update({'initialSprint__name': sprintName,
                       'initialSprint__status': 'Accepted'})

    extra={
        'on_schedule': "CASE WHEN initialSprint_id = currentSprint_id THEN 'Yes' ELSE 'No' END"
    }
    story=Story.objects.extra(select=extra).filter(**kwargs).values('on_schedule').order_by('-on_schedule').annotate(Count('rallyNumber'))

    c = {'data': json.dumps([dict(item) for item in story]),
         'sprint': sprintName,
         'average': default,
         'list': sprints}
    return render(request, 'metrics/speedo.html', c)

def BuildRelease(request):
    releaseList=getReleaseList()
    releaseName = None
    defaultRelease = getPriorRelease()
    if request.method == 'POST':
        releaseName = _getValue(request.POST,'choice')
    if releaseName == None:
        releaseName = str(defaultRelease.name) if defaultRelease else releaseList[0]

    kwargs = {
        'release__name': releaseName,
        'status': 'A',
        'storyType': 'Enhancement',
    }
    story=Story.objects.filter(**kwargs).order_by('theme','-businessValue','rallyNumber')
    c = {'story': story, 
         'current': releaseName,
         'header': 'Enhancements released in '+ releaseName,
         'exception': 'No enhancements have yet been released in '+ releaseName,
         'list': releaseList}
    return c

def ReleaseReport(request):
    context = BuildRelease(request)
    return render(request,'metrics/release.html',context)

def SprintReport(request):
    sprintList=getSprintList()
    thisSprint=getCurrentSprint()
    sprint = None
    if request.method == 'POST':
        sprint = _getValue(request.POST,'choice')

    if sprint == None:
        sprint=str(thisSprint.name) if thisSprint else sprintList[0]

    selectedSprint = getSprint(sprint)
    kwargs = {
        'currentSprint__name': sprint,
        'storyType': 'Enhancement',
    }

    story=Story.objects.filter(**kwargs).order_by('theme','-businessValue','rallyNumber')
    c = {'story': story, 
         'current': sprint,
         'header': 'Enhancement stories scheduled for ' + sprint,
         'startDate': selectedSprint.startDate,
         'endDate': selectedSprint.endDate,
         'exception': 'No enhancements have yet been scheduled for '+ sprint,
         'list': sprintList}
    return render(request,'metrics/release.html',c)

def PendingUAT(request):

    kwargs = {
        'release': None,
        'storyType': 'Enhancement',
        'status': 'C',
    }

    extra = {
        'globalLead': "select globalLead from metrics_module where moduleName = metrics_story.module",
        'sprintEnd': "select endDate from metrics_sprint where id = metrics_story.currentSprint_id",
        'color': "select case when datediff(now(),endDate) > 28 then 'R' when datediff(now(),endDate) > 14 then 'Y' else 'G' end from metrics_sprint where id = metrics_story.currentSprint_id",
        }

    story=Story.objects.filter(**kwargs).extra(select=extra).order_by('theme','sprintEnd','rallyNumber')

    c = {
         'story': story, 
         'header': 'Enhancements Pending UAT',
         'exception': 'No enhancements are pending UAT.',
         'showSprint': 'Y',
        }
    return render(request, 'metrics/release.html',c)

def Backlog(request):

    kwargs = {
        'release': None,
        'storyType': 'Enhancement',
        'status__in': ['B','D'],
    }

    filter=': '
    if request.method == 'POST':
        track = _getValue(request.POST,'track')
        module = _getValue(request.POST,'module')
        size = _getValue(request.POST,'size')
        theme = _getValue(request.POST,'theme')
        if track:
            kwargs.update({'track': track})
            filter = " (Track = %s): " % (request.POST['track'])
        elif module:
            kwargs.update({'module': module})
            filter = " (Module = %s): " % (request.POST['module'])
        elif size:
            kwargs.update({'solutionSize': request.POST['size']})
            filter = " (Story Size = %s): " % (request.POST['size'])
        elif theme:
            kwargs.update({'theme': request.POST['theme']})
            filter = " (Investment Theme = %s): " % (request.POST['theme'])
 
    extra={'globalLead': "select globalLead from metrics_module where moduleName = metrics_story.module"}
    story=Story.objects.filter(**kwargs).extra(select=extra).order_by('-businessValue','theme','rallyNumber')
    c = {'story': story, 
         'current': None,
         'header': 'Enhancement Backlog' + filter + str(len(story)) + ' stories',
         'exception': 'No enhancements are in the backlog!',
         'gpo': 'Y',
         'list': None,
         'showBlocked': 'Y'}
    return render(request,'metrics/release.html',c)

def _allGraphs(request, **kwargs):
    theme=Story.objects.filter(**kwargs).values('theme').annotate(scount=Count('theme')).annotate(metric=F('theme')).order_by('-scount','theme')
    size=Story.objects.filter(**kwargs).values('solutionSize').annotate(scount=Count('solutionSize')).annotate(metric=F('solutionSize')).order_by('solutionSize')
    track=Story.objects.filter(**kwargs).values('track').annotate(scount=Count('track')).annotate(metric=F('track')).order_by('-scount','track')
    module=Story.objects.filter(**kwargs).values('module').annotate(scount=Count('module')).annotate(metric=F('module')).order_by('-scount','module')

    allStories=Story.objects.filter(**kwargs)
    storyCount = len(allStories)
    
    c = {
         'theme': json.dumps([dict(item) for item in theme]),
         'size': json.dumps([dict(item) for item in size]),
         'track': json.dumps([dict(item) for item in track]),
         'module': json.dumps([dict(item) for item in module]),
         'header': "%s total stories" % (storyCount),
         'title': "Enhancement backlog by ",
        }
    return render(request,'metrics/allGraphs.html', c)

def BacklogGraphs(request, chartType):
    kwargs = {
        'release': None,
        'status__in': ['B','D'],
        'storyType': 'Enhancement',
    }

    if chartType in ["module","track","theme"]:
        var = chartType
        myOrder = ['-scount', var,]
        myDesc = var
        
    elif chartType == "size":
        var = "solutionSize"
        myOrder = [var,]
        myDesc = "solution size"

    elif chartType == "all":
        return _allGraphs(request, **kwargs)

    else:
        var = None
        
    if var:
        data=Story.objects.filter(**kwargs).values(var).annotate(scount=Count(var)).annotate(metric=F(var)).order_by(*myOrder)
        allStories=Story.objects.filter(**kwargs)
        storyCount = len(allStories)
    
        c = {'data': json.dumps([dict(item) for item in data]),
             'title': "Enhancement backlog by "+myDesc,
             'header': "%s total stories" % (storyCount),
             'chartType': chartType,
            }
        return render(request,'metrics/blGraphs.html', c)
    else:
        return render(request,'metrics/error.html', {})

def ProjectGrooming(request):
    kwargs = {
        'storyType': 'Project Grooming',
    }
    story=Story.objects.filter(**kwargs).extra({'globalLead': "select globalLead from metrics_module where moduleName = metrics_story.module"}).order_by('track','module','rallyNumber')
    c = {'story': story,
         'header': "Project grooming (%s stories)" % (len(story)),
         'exception': 'No project grooming stories'}
    return render(request,'metrics/grooming.html',c)

def updateStory(request):
    text = 'Enter user story to sync'
    status = 'N'
    result = ''
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            if 'story' in request.POST and request.POST['story']:
                # Add an re check for story format
                if re.match(r'^US\d+$',request.POST['story']):
                    status, result = getOrCreateStory(request.POST['story'])
                else:
                    result = "%s is not a valid Rally user story number." % (request.POST['story'])
            else:
                result = "Parameter story not passed in."
        else:
            result = "Form validation failed."

    c = {'form': SearchForm(),
         'message': text,
         'status' : status,
         'result' : result,
        }
    return render(request, 'metrics/update.html', c)

def EpicView(request):

    status, data = getEpics()
    c = {'data': data}
    return render(request, 'metrics/projects.html', c)

def ProjectStories(request, epic):

    status, data = getProjectStories(epic)
    if status == "Y":
        projectName = data[0]['project']
        c = {'data': data,
             'projectName': projectName,
            }
        return render(request, 'metrics/project_stories.html', c)
    else:
        return render(request, 'metrics/error.html', {})
