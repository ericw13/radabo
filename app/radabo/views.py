import re,json
from django.shortcuts import render, render_to_response
from django.http import HttpResponse
from radabo.models import Sprint, Story, Release, Blog
from radabo.utils import getSprintList, getReleaseList, getCurrentSprint, getCurrentRelease, getOrCreateStory, getEpics, getProjectStories, getPriorRelease, getSprint, getModuleList, getAllStoriesInSprint
from radabo.forms import SearchForm
from django.utils import timezone
from django.views import generic
from django.db.models import F, Q, Avg, Count
from django.template import Context
from django.template.loader import get_template
from datetime import timedelta

# Create your views here.
class IndexView(generic.ListView):
    """
    View for the main page which pulls the latest blog entries
    """
    template_name = 'radabo/index.html'
    context_object_name = 'entries'
    def get_queryset(self):
        return Blog.objects.order_by('-created_at')[:10]

def routeToError(request):
    """
    Used for any unrecognized URL patterns
    """
    return render(request,'radabo/error.html', {})

def _drawVelocity(request, kwargs, template):
    """
    Common function that fetches data and json-ifies it for use with the
    Google Charts API
    """

    results=Sprint.objects.filter(**kwargs).order_by('startDate').values('name','velocity')[:24]
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
    #results=Story.objects.filter(*args, **kwargs).order_by('initialSprint__id')
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
        releaseName = str(defaultRelease.name) if defaultRelease else releaseList[0]

    kwargs = {
              'release__name': releaseName,
              'status': 'A',
              'storyType': 'Enhancement',
             }
    story=Story.objects.filter(**kwargs).order_by('-businessValue','theme','rallyNumber')
    c = {
         'story': story, 
         'current': releaseName,
         'header': 'Enhancements released in '+ releaseName,
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

    story=Story.objects.filter(**kwargs).order_by('-businessValue','theme','rallyNumber')
    c = {
         'story': story, 
         'current': sprint,
         'header': 'Enhancement stories scheduled for ' + sprint,
         'startDate': selectedSprint.startDate,
         'endDate': selectedSprint.endDate,
         'exception': 'No enhancements have yet been scheduled for '+ sprint,
         'buttonText': 'Select Sprint',
         'list': sprintList,
         'showStatus': 'Y',
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
        header = 'All enhancements for %s module' % (module)
        exc = 'No enhancements have yet been defined for '+ module,

        story=Story.objects.filter(**kwargs).order_by('-rallyNumber')
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
         'showStatus': 'Y',
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

    # I would love a different way to handle this... maybe explore any possible
    # template-based solutions
    extra = {
        'color': "select case when datediff(now(),endDate) > 28 then 'R' when datediff(now(),endDate) > 14 then 'Y' else 'G' end from radabo_sprint where id = radabo_story.currentSprint_id",
        }

    story=Story.objects.filter(**kwargs).extra(select=extra).order_by('theme','currentSprint__endDate','rallyNumber')

    c = {
         'story': story, 
         'header': 'Enhancements Pending UAT',
         'exception': 'No enhancements are pending UAT.',
         'showSprint': 'Y',
        }
    return render(request, 'radabo/release.html',c)

def Backlog(request):
    """
    Enhancement backlog page, optionally filtered via clicking a chart
    """

    kwargs = {
        'release': None,
        'storyType': 'Enhancement',
        'status__in': ['B','D'],
    }

    filter=': '
    if request.method == 'POST':
        track = request.POST.get('track')
        module = request.POST.get('module')
        size = request.POST.get('size')
        theme = request.POST.get('theme')
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
 
    story=Story.objects.filter(**kwargs).order_by('-businessValue','theme','rallyNumber')
    c = {
         'story': story, 
         'current': None,
         'header': 'Enhancement Backlog' + filter + str(len(story)) + ' stories',
         'exception': 'No enhancements are in the backlog!',
         'gpo': 'Y',
         'list': None,
         }
    return render(request,'radabo/release.html',c)

def _allGraphs(request, **kwargs):
    """
    Function retrieving data for all four charts
    """
    theme=Story.objects.filter(**kwargs).values('theme').annotate(scount=Count('theme')).annotate(metric=F('theme')).order_by('-scount','theme')
    size=Story.objects.filter(**kwargs).values('solutionSize').annotate(scount=Count('solutionSize')).annotate(metric=F('solutionSize')).order_by('solutionSize')
    track=Story.objects.filter(**kwargs).values('track').annotate(scount=Count('track')).annotate(metric=F('track')).order_by('-scount','track')
    module=Story.objects.filter(**kwargs).values('module__moduleName').annotate(scount=Count('module__moduleName')).annotate(metric=F('module__moduleName')).order_by('-scount','module__moduleName')

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
    return render(request,'radabo/allGraphs.html', c)

def BacklogGraphs(request, chartType):
    """
    Function for generating a specific chart.  Function for generating all
    charts was hacked into here, but needs a more elegant solution
    """
    kwargs = {
        'release': None,
        'status__in': ['B','D'],
        'storyType': 'Enhancement',
    }

    if chartType in ["track","theme"]:
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
        data=Story.objects.filter(**kwargs).values(var).annotate(scount=Count(var)).annotate(metric=F(var)).order_by(*myOrder)
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
    story=Story.objects.filter(**kwargs).order_by('track','module','rallyNumber')
    c = {'story': story,
         'header': "Project grooming (%s stories)" % (len(story)),
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
    return render(request, 'radabo/update.html', c)

def EpicView(request):
    """
    Page dynamically fetching active project epics
    """

    status, data = getEpics()
    if status == 'N':
        print str(data)

    c = {'story': data}
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
        if sprint:
            startDate = sprint.startDate
            endDate = sprint.endDate
            status, data = getAllStoriesInSprint(sprintName)
            if status == 'Y':
                vel = 0
                for i in data:
                    vel += i['points']
                header = 'All stories assigned to sprint %s (%s points)' % (sprintName, vel)
            else:
                header = 'Nothing has been assigned to sprint %s' % (sprintName)
                data = None
        else:
            header = '%s is not a valid sprint name' % (sprintName)
            data = None
    elif request.method == 'GET':
        header = 'Please select a sprint from the list'
        startDate = None
        endDate = None
        data = None

    c = {
        'story': data,
        'header': header,
        'buttonText': 'Select Sprint',
        'startDate': startDate,
        'endDate': endDate,
        'list': sprintList,
        }
    return render(request, 'radabo/full_sprint.html', c)
