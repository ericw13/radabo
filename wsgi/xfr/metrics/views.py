from django.shortcuts import render, render_to_response
from django.http import HttpResponse
from metrics.models import Sprint, Story, Release
from metrics import utils
from django.utils import timezone
from django.views import generic
from django.db.models import F, Q, Avg, Count
from datetime import timedelta
import json

# Create your views here.
def index(request):
    return render_to_response('metrics/index.html', {})

def VelocityChart(request):
    results=Sprint.objects.filter(status="Accepted",startDate__gte="2015-09-01 00:00:00").order_by('startDate').values('name','velocity')[:12]
    avg = results.aggregate(Avg('velocity'))['velocity__avg']
    c = {'velocity':
         json.dumps([dict(item) for item in results]),
         'avg': avg}
    return render_to_response('metrics/velocity.html', c)

def DelayedItems(request):
    dateLimit = timezone.now() + timedelta(days=-365)
    results=Story.objects.filter(~Q(initialSprint=F('currentSprint')),initialSprint__startDate__gte=dateLimit,storyType="Enhancement").order_by('initialSprint__id')
    c = {'story': results}
    return render_to_response('metrics/lateStories.html',c)

def Pie(request):
    sprints=utils.getSprintList()
    sprintName=None 
    default="Last Six Months"
    if request.method == 'POST':
        if 'sprintSelect' in request.POST and request.POST['sprintSelect']:
            sprintName = request.POST['sprintSelect']
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
    story=Story.objects.extra(select={'on_schedule': "CASE WHEN initialSprint_id = currentSprint_id THEN 'Yes' ELSE 'No' END"}).filter(**kwargs).values('on_schedule').order_by('-on_schedule').annotate(Count('rallyNumber'))

    c = {'data': json.dumps([dict(item) for item in story]),
         'sprint': sprintName,
         'average': default,
         'list': sprints}
    return render(request, 'metrics/speedo.html', c)

def ReleaseReport(request):
    releaseList=utils.getReleaseList()
    releaseName = None
    thisRelease = utils.getCurrentRelease()
    if request.method == 'POST':
        if 'choice' in request.POST and request.POST['choice']:
            releaseName=request.POST['choice']
    if releaseName == None:
        releaseName=str(thisRelease.name) if thisRelease else releaseList[0]

    story=Story.objects.filter(release__name=releaseName,status="A",storyType="Enhancement").order_by('-businessValue','rallyNumber')
    c = {'story': story, 
         'current': releaseName,
         'header': 'Enhancements released in '+ releaseName, 
         'exception': 'No enhancements have yet been released in '+ releaseName,
         'list': releaseList}
    return render(request,'metrics/release.html',c)

def SprintReport(request):
    sprintList=utils.getSprintList()
    thisSprint=utils.getCurrentSprint()
    sprint = None
    if request.method == 'POST':
        if 'choice' in request.POST and request.POST['choice']:
            sprint = request.POST['choice']
    if sprint == None:
        sprint=str(thisSprint.name) if thisSprint else sprintList[0]

    story=Story.objects.filter(currentSprint__name=sprint,storyType="Enhancement").order_by('-businessValue','rallyNumber')
    c = {'story': story, 
         'current': sprint,
         'header': 'Stories scheduled for ' + sprint,
         'exception': 'No enhancements have yet been scheduled for '+ sprint,
         'list': sprintList}
    return render(request,'metrics/release.html',c)

def Backlog(request):

    kwargs = {
        'release': None,
        'storyType': 'Enhancement',
        'status__in': ['B','D'],
    }

    filter=': '
    if request.method == 'POST':
        if 'track' in request.POST and request.POST['track']:
            if request.POST['track'] == 'null':
                kwargs.update({'track__isnull': True})
            else:
                kwargs.update({'track': request.POST['track']})
            filter = " (Track = %s): " % (request.POST['track'])
        if 'module' in request.POST and request.POST['module']:
            if request.POST['module'] == 'null':
                kwargs.update({'module__isnull': True})
            else:
                kwargs.update({'module': request.POST['module']})
            filter = " (Module = %s): " % (request.POST['module'])
        if 'solutionSize' in request.POST and request.POST['solutionSize']:
            if request.POST['solutionSize'] == 'null':
                kwargs.update({'solutionSize__isnull': True})
            else:
                kwargs.update({'solutionSize': request.POST['solutionSize']})
            filter = " (Story Size = %s): " % (request.POST['solutionSize'])
            
    story=Story.objects.filter(**kwargs).extra({'globalLead': "select globalLead from metrics_module where moduleName = metrics_story.module"}).order_by('-businessValue','rallyNumber')
    c = {'story': story, 
         'current': None,
         'header': 'Enhancement Backlog' + filter + str(len(story)) + ' stories',
         'exception': 'No enhancements are in the backlog!',
         'gpo': 'Y',
         'list': None}
    return render(request,'metrics/release.html',c)

def BacklogGraphs(request):
    kwargs = {
        'release': None,
        'status__in': ['B','D'],
        'storyType': 'Enhancement',
    }
    modcount=Story.objects.filter(**kwargs).values('module').annotate(mcount=Count('module')).order_by('-mcount','module')
    trackcount=Story.objects.filter(**kwargs).values('track').annotate(tcount=Count('track')).order_by('-tcount','track')
    sizecount=Story.objects.filter(**kwargs).values('solutionSize').annotate(scount=Count('track')).order_by('solutionSize')

    kwargs.update({'module__isnull': True})
    nullmod=Story.objects.filter(**kwargs)
    nullcount = len(nullmod)
    
    c = {'modcount': json.dumps([dict(item) for item in modcount]),
         'trackcount': json.dumps([dict(item2) for item2 in trackcount]),
         'sizecount': json.dumps([dict(item3) for item3 in sizecount]),
         'nullcount': nullcount
        }
    return render(request,'metrics/blGraphs.html', c)
