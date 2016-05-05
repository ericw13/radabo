from django.shortcuts import render, render_to_response
from django.http import HttpResponse
from metrics.models import Sprint, Story, Release
from django.utils import timezone
from django.views import generic
from django.db.models import F, Q, Avg, Count
from datetime import timedelta
import json

# Create your views here.
def index(request):
    return render_to_response('metrics/index.html', {})

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

def VelocityChart(request):
    results=Sprint.objects.filter(status="Accepted",startDate__gte="2015-09-01 00:00:00").order_by('startDate').values('name','velocity')[:12]
    avg = results.aggregate(Avg('velocity'))['velocity__avg']
    c = {'velocity':
         json.dumps([dict(item) for item in results]),
         'avg': avg}
    return render_to_response('metrics/velocity.html', c)

def DelayedItems(request):
    dateLimit = timezone.now() + timedelta(days=-365)
    results=Story.objects.filter(~Q(initialSprint=F('currentSprint')),initialSprint__startDate__gte=dateLimit).order_by('initialSprint__id')
    c = {'story': results}
    return render_to_response('metrics/lateStories.html',c)

def Pie(request):
    sprints=getSprintList()
    sprintName=None 
    default="Last Six Months"
    if request.method == 'POST':
        if 'sprintSelect' in request.POST and request.POST['sprintSelect']:
            sprintName = request.POST['sprintSelect']
    if sprintName == None:
        sprintName = default

    if sprintName == default:
        start = timezone.now() + timedelta(days=-182)
        l=Sprint.objects.filter(status='Accepted',startDate__gte=start)
        story=Story.objects.extra(select={'on_schedule': "CASE WHEN initialSprint_id = currentSprint_id THEN 'Yes' ELSE 'No' END"}).filter(initialSprint__in=l).values('on_schedule').order_by('-on_schedule').annotate(Count('rallyNumber'))
    else:
        story=Story.objects.extra(select={'on_schedule': "CASE WHEN initialSprint_id = currentSprint_id THEN 'Yes' ELSE 'No' END"}).filter(initialSprint__name=sprintName,initialSprint__status='Accepted').values('on_schedule').order_by('-on_schedule').annotate(Count('rallyNumber'))

    c = {'data': json.dumps([dict(item) for item in story]),
         'sprint': sprintName,
         'average': default,
         'list': sprints}
    return render(request, 'metrics/speedo.html', c)

def ReleaseReport(request):
    releaseList=getReleaseList()
    releaseName = None
    thisRelease = getCurrentRelease()
    if request.method == 'POST':
        if 'choice' in request.POST and request.POST['choice']:
            releaseName=request.POST['choice']
    if releaseName == None:
        releaseName=str(thisRelease.name) if thisRelease else releaseList[0]

    story=Story.objects.filter(release__name=releaseName,status="A").order_by('-businessValue','rallyNumber')
    c = {'story': story, 
         'current': releaseName,
         'header': 'Enhancements released in '+ releaseName, 
         'exception': 'No enhancements have yet been released in '+ releaseName,
         'list': releaseList}
    return render(request,'metrics/release.html',c)

def SprintReport(request):
    sprintList=getSprintList()
    thisSprint=getCurrentSprint()
    sprint = None
    if request.method == 'POST':
        if 'choice' in request.POST and request.POST['choice']:
            sprint = request.POST['choice']
    if sprint == None:
        sprint=str(thisSprint.name) if thisSprint else sprintList[0]

    story=Story.objects.filter(currentSprint__name=sprint).order_by('-businessValue','rallyNumber')
    c = {'story': story, 
         'current': sprint,
         'header': 'Stories scheduled for ' + sprint,
         'exception': 'No enhancements have yet been scheduled for '+ sprint,
         'list': sprintList}
    return render(request,'metrics/release.html',c)

def Backlog(request):
    story=Story.objects.filter(release=None, status__in=['B','D']).order_by('-businessValue','rallyNumber')
    c = {'story': story, 
         'current': None,
         'header': 'Enhancement Backlog: ' + str(len(story)) + ' stories',
         'exception': 'No enhancements are in the backlog!',
         'list': None}
    return render(request,'metrics/release.html',c)

def BacklogGraphs(request):
    modcount=Story.objects.filter(release=None, status__in=['B','D']).values('module').annotate(mcount=Count('module')).order_by('-mcount','module')
    trackcount=Story.objects.filter(release=None, status__in=['B','D']).values('track').annotate(tcount=Count('track')).order_by('-tcount','track')
    sizecount=Story.objects.filter(release=None, status__in=['B','D']).values('solutionSize').annotate(scount=Count('track')).order_by('solutionSize')
    nullmod=Story.objects.filter(release=None, status__in=['B','D'], module__isnull=True)
    nullcount = len(nullmod)
    
    c = {'modcount': json.dumps([dict(item) for item in modcount]),
         'trackcount': json.dumps([dict(item2) for item2 in trackcount]),
         'sizecount': json.dumps([dict(item3) for item3 in sizecount]),
         'nullcount': nullcount
        }
    return render(request,'metrics/blGraphs.html', c)
