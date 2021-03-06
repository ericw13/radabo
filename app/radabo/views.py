import re
import json

from django.shortcuts import render, render_to_response
from django.http import HttpResponse
from django.utils import timezone
from django.views import generic
from django.db.models import F, Q, Avg, Count, Sum
from django.template import Context
from django.template.loader import get_template
from datetime import timedelta
from itertools import chain

from radabo.models import Sprint, Story, Release, Blog
from radabo.forms import SearchForm
# imports 11 functions defined in radabo.utils.__all__
from radabo.utils import *

def _text(count):
    if count == 1:
        return str(count) + ' story'
    else:
        return str(count) + ' stories'

# Create your views here.
class IndexView(generic.ListView):
    """
    View for the main page which pulls the latest blog entries
    """
    template_name = 'radabo/index.html'
    context_object_name = 'entries'
    def get_queryset(self):
        return Blog.objects.order_by('-created_at')[:10]

def Info(request):
    """
    View that displays various information about the site.  It doesn't actually
    pull any data from the database.
    """
    return render_to_response('radabo/info.html', {})

def routeToError(request):
    """
    Used for any unrecognized URL patterns
    """
    return render(request,'radabo/error.html', {})

def _drawVelocity(request, kwargs, template):
    """
    Common function that fetches sprint velocity data and json-ifies it for use 
    with the Google Charts API
    """

    results=(Sprint.objects.filter(**kwargs)
             .order_by('startDate')
             .values('name','velocity')[:24])
    avg = results.aggregate(Avg('velocity'))['velocity__avg']
    c = {'velocity':
         json.dumps([dict(item) for item in results]),
         'avg': avg}
    return render_to_response(template, c)

def VelocityChart(request):
    """
    Bi-weekly sprint velocity - new schedule started early June 2016
    """
    kwargs = {
        'status': 'Accepted',
        'startDate__gte': '2016-06-01 00:00:00',
    }
    return _drawVelocity(request, kwargs, 'radabo/velocity.html')

def OldVelocityChart(request):
    """
    Monthly sprint velocity - schedule deprecated early June 2016
    """
    kwargs = {
        'status': 'Accepted',
        'startDate__gte': '2015-09-01 00:00:00',
        'endDate__lte': '2016-06-10 00:00:00',
    }
    return _drawVelocity(request, kwargs, 'radabo/month_velocity.html')

# Old process that cared about whether enhancements were delivered in the sprint
# in which they were originally scheduled.  This is no longer used.
#def DelayedItems(request):
    #dateLimit = timezone.now() + timedelta(days=-365)
    #args = ( 
            #~Q(initialSprint=F('currentSprint') ), 
           #)
    #kwargs = {
              #'initialSprint__startDate__gte': dateLimit,
              #'storyType': 'Enhancement',
             #}
    #results=(Story.objects.filter(*args, **kwargs)
    #         .order_by('initialSprint__id')
    #c = {'story': results}
    #return render_to_response('radabo/lateStories.html',c)

#def Success(request):
    #sprints=getSprintList()
    #sprintName=None 
    #default="Last Six Months"
    #if request.method == 'POST':
        #sprintName = getValue(request.POST,'sprintSelect')
    #if sprintName == None:
        #sprintName = default
#
    #kwargs = {
        #'storyType': 'Enhancement',
    #}
    #if sprintName == default:
        #start = timezone.now() + timedelta(days=-182)
        #l=Sprint.objects.filter(status='Accepted',startDate__gte=start)
        #kwargs.update({'initialSprint__in': l})
    #else:
        #kwargs.update({'initialSprint__name': sprintName,
                       #'initialSprint__status': 'Accepted'})
#
    #extra={
        #'on_schedule': "CASE WHEN initialSprint_id = currentSprint_id THEN 'Yes' ELSE 'No' END"
          #}
    #story=Story.objects.extra(select=extra).filter(**kwargs).values('on_schedule').order_by('-on_schedule').annotate(Count('rallyNumber'))
#
    #c = {
         #'data': json.dumps([dict(item) for item in story]),
         #'sprint': sprintName,
         #'average': default,
         #'list': sprints,
        #}
    #return render(request, 'radabo/speedo.html', c)
#
def _buildRelease(request):
    """
    Generic function building a list of stories in a given release
    """
    releaseList=getReleaseList()
    releaseName = None
    defaultRelease = getPriorRelease()
    if request.method == 'POST':
        releaseName = request.POST.get('choice')
    if releaseName == None:
        releaseName = (str(defaultRelease.name) if defaultRelease 
                         else releaseList[0])

    kwargs = {
              'release__name': releaseName,
              'status': 'A',
              'storyType': 'Enhancement',
             }
    story=(Story.objects.filter(**kwargs)
           .order_by('-businessValue','theme','rallyNumber'))
    c = {
         'story': story, 
         'current': releaseName,
         'header': 'Enhancements released in '+ releaseName + ': ' + _text(len(story)),
         'exception': 'No enhancements have yet been released in '+ releaseName,
         'buttonText': 'Select Release',
         'list': releaseList,
        }
    return c

def ReleaseReport(request):
    context = _buildRelease(request)
    return render(request,'radabo/release.html',context)

def _buildSprint(request):
    """
    Generic function building a list of stories in a given sprint 
    """

    sprintList=getSprintList()
    thisSprint=getCurrentSprint()
    sprint = None
    if request.method == 'POST':
        sprint = request.POST.get('choice')

    if sprint == None:
        sprint=str(thisSprint.name) if thisSprint else sprintList[0]

    selectedSprint = getSprint(sprint)
    kwargs = {
        'currentSprint__name': sprint,
        'storyType': 'Enhancement',
    }
    myord = ['-businessValue','theme','rallyNumber']

    story=Story.objects.filter(**kwargs).order_by(*myord)
    sortedStory = sorted(story, key=lambda p: p.status_sort())
    c = {
         'story': sortedStory, 
         'current': sprint,
         'header': 'Enhancement stories scheduled for ' + sprint + ': ' + _text(len(story)),
         'startDate': selectedSprint.startDate,
         'endDate': selectedSprint.endDate,
         'exception': 'No enhancements have yet been scheduled for '+ sprint,
         'buttonText': 'Select Sprint',
         'list': sprintList,
        }

    return c

def SprintReport(request):
    context = _buildSprint(request)
    return render(request,'radabo/release.html',context)

def enhByModule(request):
    """
    All enhancements (backlog, active, complete)
    """

    modList = getModuleList()
    if request.method == 'POST':
        module = request.POST.get('choice')
        kwargs = {
            'storyType': 'Enhancement',
            'module__moduleName': module,
        }
        story=Story.objects.filter(**kwargs).order_by('-rallyNumber')
        header = 'All enhancements for %s module: %s' % (module, _text(len(story)))
        exc = 'No enhancements have yet been defined for '+ module

    elif request.method == 'GET':
        header = 'Please select a module from the list'
        story = None
        module = ''
        exc = ''
        
    c = {
         'story': story,
         'current': module,
         'header': header,
         'exception': exc,
         'buttonText': 'Select Module',
         'list': modList,
        }
    return render(request,'radabo/release.html',c)

def PendingUAT(request):
    """
    Enhancements in Complete status with no release.  Drives Pending UAT page
    """

    kwargs = {
        'release': None,
        'storyType': 'Enhancement',
        'status': 'C',
    }
    myord=[
           'currentSprint__endDate',
           '-businessValue',
           'rallyNumber',
          ]

    story=Story.objects.filter(**kwargs).order_by(*myord)

    c = {
         'story': story, 
         'header': 'Enhancements Pending UAT: ' + _text(len(story)),
         'exception': 'No enhancements are pending UAT.',
         'showSprint': 'Y',
        }
    return render(request, 'radabo/release.html',c)

def Backlog(request):
    """
    Enhancement backlog page, optionally filtered via clicking a chart
    """

    kwargs = {
        'currentSprint': None,
        'storyType': 'Enhancement',
        'status__in': ['B','D'],
    }

    filter=': '
    if request.method == 'POST':
        track = request.POST.get('track')
        module = request.POST.get('module')
        size = request.POST.get('size')
        theme = request.POST.get('theme')
        region = request.POST.get('region')
        # Only one parameter can be passed in via chart click, so this is fine
        if track:
            kwargs.update({'track': track})
            filter = " (Track = %s): " % (track)
        elif module:
            kwargs.update({'module__moduleName': module})
            filter = " (Module = %s): " % (module)
        elif size:
            kwargs.update({'solutionSize': size})
            filter = " (Story Size = %s): " % (size)
        elif theme:
            kwargs.update({'theme': theme})
            filter = " (Investment Theme = %s): " % (theme)
        elif region:
            kwargs.update({'region': region})
            filter = " (Geographic Region = %s): " % (region)
 
    myord=[
           '-businessValue',
           'theme',
           'rallyNumber',
          ]
    story=Story.objects.filter(**kwargs).order_by(*myord)
    sortedStory = sorted(story, key=lambda p: p.status_sort())
    c = {
         'story': sortedStory, 
         'current': None,
         'header': 'Enhancement Backlog' + filter + _text(len(story)),
         'exception': 'No enhancements are in the backlog!',
         'gpo': 'Y',
         'list': None,
         }
    return render(request,'radabo/release.html',c)

def _allGraphs(request, **kwargs):
    """
    Function retrieving data for all four charts
    """
    theme=(Story.objects.filter(**kwargs).values('theme')
           .annotate(scount=Count('theme')).annotate(metric=F('theme'))
           .order_by('-scount','theme'))
    size=(Story.objects.filter(**kwargs).values('solutionSize')
           .annotate(scount=Count('solutionSize'))
           .annotate(metric=F('solutionSize')).order_by('solutionSize'))
    track=(Story.objects.filter(**kwargs).values('track')
           .annotate(scount=Count('track'))
           .annotate(metric=F('track')).order_by('-scount','track'))
    region=(Story.objects.filter(**kwargs).values('region')
           .annotate(scount=Count('region'))
           .annotate(metric=F('region')).order_by('-scount','region'))
    module=(Story.objects.filter(**kwargs).values('module__moduleName')
            .annotate(scount=Count('module__moduleName'))
            .annotate(metric=F('module__moduleName'))
            .order_by('-scount','module__moduleName'))

    allStories=Story.objects.filter(**kwargs)
    storyCount = len(allStories)
    
    c = {
         'theme': json.dumps([dict(item) for item in theme]),
         'size': json.dumps([dict(item) for item in size]),
         'track': json.dumps([dict(item) for item in track]),
         'module': json.dumps([dict(item) for item in module]),
         'region': json.dumps([dict(item) for item in region]),
         'header': "%s total stories" % (storyCount),
         'title': "Enhancement backlog by ",
        }
    return render(request,'radabo/allGraphs.html', c)

def enhGraph(request):
    """
    Function to graph enhancement release by count
    """
    kwargs = {
              'storyType': 'Enhancement',
              'release__isnull': False,
              'release__status': "Accepted",
              'release__endDate__gte': '2016-03-01 00:00:00',
             }
    data = (Story.objects.filter(**kwargs).values('release__name')
           .annotate(count=Count('release__name'))
           .annotate(sum=Sum('businessValue'))
           .order_by('release__startDate'))

    c = {
         'velocity': json.dumps([dict(item) for item in data]),
        }
    return render(request,'radabo/releaseGraph.html', c)

def BacklogGraphs(request, chartType):
    """
    Function for generating a specific chart.  Function for generating all
    charts was hacked into here, but needs a more elegant solution
    """
    kwargs = {
        'currentSprint': None,
        'status__in': ['B','D'],
        'storyType': 'Enhancement',
    }

    if chartType in ["track","theme","region"]:
        var = chartType
        myOrder = ['-scount', var,]
        myDesc = var
        
    elif chartType == "module":
        var = "module__moduleName"
        myOrder = ['-scount', var,]
        myDesc = chartType
        
    elif chartType == "size":
        var = "solutionSize"
        myOrder = [var,]
        myDesc = "solution size"

    elif chartType == "all":
        return _allGraphs(request, **kwargs)

    else:
        var = None
        
    if var:
        data=(Story.objects.filter(**kwargs).values(var)
              .annotate(scount=Count(var))
              .annotate(metric=F(var)).order_by(*myOrder))
        allStories=Story.objects.filter(**kwargs)
        storyCount = len(allStories)
    
        c = {'data': json.dumps([dict(item) for item in data]),
             'title': "Enhancement backlog by "+myDesc,
             'header': "%s total stories" % (storyCount),
             'chartType': chartType,
            }
        return render(request,'radabo/blGraphs.html', c)
    else:
        return render(request,'radabo/error.html', {})

def ProjectGrooming(request):
    """
    View defining the project grooming page
    """
    kwargs = {
        'storyType': 'Project Grooming',
    }
    myord = [
             'track',
             'module',
             'rallyNumber',
            ]
    story=Story.objects.filter(**kwargs).order_by(*myord)
    c = {'story': story,
         'header': 'Project grooming: ' + _text(len(story)),
         'exception': 'No project grooming stories'}
    return render(request,'radabo/grooming.html',c)

def updateStory(request):
    """
    View for the update story page
    """
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
                    result = ("%s is not a valid Rally user story number." 
                               % (request.POST['story']))
            else:
                result = "Parameter story not passed in."
        else:
            result = "Form validation failed."

    c = {'form': SearchForm(),
         'message': text,
         'status' : status,
         'result' : result,
        }
    return render(request, 'radabo/update.html', c)

def EpicView(request):
    """
    Page dynamically fetching active project epics
    """

    status, data = getEpics()
    gantt = []
    if status == 'N':
        print str(data)

    else:
        key_list = ['id','name','percent','startDate','endDate']
        for row in data:
            row['startDate'] = row['startDate'].strftime('%Y-%m-%d')
            row['endDate'] = row['endDate'].strftime('%Y-%m-%d')
            record = {k: row[k] for k in key_list if k in row}
            gantt.append(record)

    c = {
         'story': data,
         'gantt': json.dumps([dict(item) for item in gantt]),
        }
    return render(request, 'radabo/projects.html', c)

def ProjectStories(request, epic):
    """
    Page dynamically fetching stories for a particular epic
    """

    status, data = getProjectStories(epic)
    if status == "Y":
        projectName = data[0]['project']
        c = {'story': data,
             'header': projectName,
            }
        return render(request, 'radabo/project_stories.html', c)
    else:
        return render(request, 'radabo/error.html', {})

def FullSprint(request):
    """
    Page that dynamically pulls all stories in a sprint from Rally
    """

    sprintList = getSprintList()
    if request.method == 'POST':
        sprintName=request.POST.get('choice')
        sprint = getSprint(sprintName)
    elif request.method == 'GET':
        sprint = getCurrentSprint()
        sprintName = sprint.name

    if sprint:
        startDate = sprint.startDate
        endDate = sprint.endDate
        status, data = getAllStoriesInSprint(sprintName)
        if status == 'Y':
            vel = 0
            for i in data:
                vel += i['points']
            header = ('All stories assigned to sprint %s: %s points' 
                      % (sprintName, vel))
        else:
            header = 'Nothing has been assigned to sprint %s' % (sprintName)
            data = None
    else:
        header = '%s is not a valid sprint name' % (sprintName)
        data = None
        startDate = None
        endDate = None

    c = {
        'story': data,
        'header': header,
        'buttonText': 'Select Sprint',
        'startDate': startDate,
        'endDate': endDate,
        'list': sprintList,
        }
    return render(request, 'radabo/full_sprint.html', c)

def Priority(request):
    """
    Page that shows items not yet prioritized or prioritized but not yet
    groomed.
    """

    header = "Prioritization and grooming status"
    exc = "Something has gone horribly wrong!"

    # Get everything not prioritized
    kwargs = {
        'status': 'B',
        'ready': 'N',
        }
    myOrd = [
        '-storyType',
        '-businessValue',
        'theme',
        'rallyNumber',
        ]
    snp = Story.objects.filter(**kwargs).order_by(*myOrd)

    # Get prioritized enhancements not yet groomed
    kwargs = {
        'status': 'B',
        'ready': 'Y',
        'storyType': 'Enhancement',
        }
    myOrd = [
        '-businessValue',
        'theme',
        'rallyNumber',
        ]
    eng = Story.objects.filter(**kwargs).order_by(*myOrd)

    # Get prioritized project groomings not yet completed - this takes two steps
    # 1. Status = Backlog, Ready = Yes
    # 2. Status in Defined, In-Progress

    # 1. Update storyType, keep same ordering
    kwargs['storyType'] = 'Project Grooming'
    pgns = Story.objects.filter(**kwargs).order_by(*myOrd)

    # 2.
    kwargs = {
        'status__in': ['D','P'],
        'storyType': 'Project Grooming',
    }
    pgip = Story.objects.filter(**kwargs).order_by(*myOrd)

    # Merge and sort the two project lists with the enhancements not groomed.
    inprogress = sorted(
                    chain(eng, pgns, pgip),
                    key=lambda x: x.status_sort())

    c = {
        'stories_not_started': snp,
        'stories_not_done': inprogress,
        'header': header,
        'exception': exc,
        'story': 'Y', # Ugly hack to make export.html show the export button!
    }
    return render(request, 'radabo/priority.html', c)

def NonFinance(request):
    header = "Non-IT Finance stories"
    exc = "There are no active stories owned by other teams that are being tracked by IT-Finance"
    kwargs = {
        'status__in': ['B','D','P','C'],
        'storyType': 'Non-Finance',
    }
    story = Story.objects.filter(**kwargs).order_by('-rallyNumber')

    c = {
         'story':  story,
         'header': header,
         'exception': exc,
        }

    return render(request, 'radabo/non_finance.html', c)

def Dashboard(request):
    header = "Enhancement Dashboard"
    exc = "Something has gone horribly wrong!"
    kwargs = {
        'status__in': ['B','D','P','C'],
        'storyType': 'Enhancement',
    }

    #Not accepted stories
    nota = (Story.objects.filter(**kwargs).values('status')
            .annotate(count=Count('status')))

    kwargs = {
        'status': 'A',
        'storyType': 'Enhancement',
        'release__endDate__gte': '2016-03-01 00:00:00',
    }

    # Accepted in current FY
    a = (Story.objects.filter(**kwargs).values('status')
         .annotate(count=Count('status')))

    # Need to re-sort based on SDLC progression
    data = []
    for s in ('B','D','P','C','A'):
        val=filter(lambda x: x['status'] == s, chain(nota, a))[0]
        if val:
            data.append(val)

    c = {
         'data': json.dumps([dict(item) for item in data]),
         'title': header,
         'exception': exc,
        }

    return render(request, 'radabo/dashboard.html', c)
