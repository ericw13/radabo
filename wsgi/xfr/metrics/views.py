import re,json
import cStringIO as StringIO
from django.shortcuts import render, render_to_response
from django.http import HttpResponse
from metrics.models import Sprint, Story, Release
from metrics.utils import getSprintList, getReleaseList, getCurrentSprint, getCurrentRelease, getOrCreateStory
from metrics.forms import SearchForm
from django.utils import timezone
from django.views import generic
from django.db.models import F, Q, Avg, Count
from django.template import Context
from django.template.loader import get_template
from datetime import timedelta

# Create your views here.
def index(request):
    return render_to_response('metrics/index.html', {})

def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    context = Context(context_dict)
    html = template.render(context)
    result = StringIO.StringIO()

    pdf = pisa.pisaDocument(StringIO.StringIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return HttpResponse('We had some errors<pre>%s</pre>' % escape(html))

def VelocityChart(request):
    kwargs = {
        'status': 'Accepted',
        'startDate__gte': '2016-06-01 00:00:00',
    }
    results=Sprint.objects.filter(**kwargs).order_by('startDate').values('name','velocity')
    avg = results.aggregate(Avg('velocity'))['velocity__avg']
    c = {'velocity':
         json.dumps([dict(item) for item in results]),
         'avg': avg}
    return render_to_response('metrics/velocity.html', c)

def OldVelocityChart(request):
    kwargs = {
        'status': 'Accepted',
        'startDate__gte': '2015-09-01 00:00:00',
        'endDate__lte': '2016-06-10 00:00:00',
    }
    results=Sprint.objects.filter(**kwargs).order_by('startDate').values('name','velocity')[:24]
    avg = results.aggregate(Avg('velocity'))['velocity__avg']
    c = {'velocity':
         json.dumps([dict(item) for item in results]),
         'avg': avg}
    return render_to_response('metrics/month_velocity.html', c)

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
    thisRelease = getCurrentRelease()
    if request.method == 'POST':
        if 'choice' in request.POST and request.POST['choice']:
            releaseName=request.POST['choice']
    if releaseName == None:
        releaseName=str(thisRelease.name) if thisRelease else releaseList[0]

    kwargs = {
        'release__name': releaseName,
        'status': 'A',
        'storyType': 'Enhancement',
    }
    story=Story.objects.filter(**kwargs).order_by('-businessValue','rallyNumber')
    c = {'story': story, 
         'current': releaseName,
         'header': 'Enhancements released in '+ releaseName, 
         'exception': 'No enhancements have yet been released in '+ releaseName,
         'list': releaseList}
    return c

def ReleaseReport(request):
    context = BuildRelease(request)
    return render(request,'metrics/release.html',context)

def ReleasePDF(request):
    context = BuildRelease(request)
    context.update({'pagesize': 'A4'})
    return render_to_pdf('metrics/releasePDF.html', context)

def SprintReport(request):
    sprintList=getSprintList()
    thisSprint=getCurrentSprint()
    sprint = None
    if request.method == 'POST':
        if 'choice' in request.POST and request.POST['choice']:
            sprint = request.POST['choice']
    if sprint == None:
        sprint=str(thisSprint.name) if thisSprint else sprintList[0]

    kwargs = {
        'currentSprint__name': sprint,
        'storyType': 'Enhancement',
    }

    story=Story.objects.filter(**kwargs).order_by('-businessValue','rallyNumber')
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
            
    extra={'globalLead': "select globalLead from metrics_module where moduleName = metrics_story.module"}
    story=Story.objects.filter(**kwargs).extra(select=extra).order_by('-businessValue','rallyNumber')
    c = {'story': story, 
         'current': None,
         'header': 'Enhancement Backlog' + filter + str(len(story)) + ' stories',
         'exception': 'No enhancements are in the backlog!',
         'gpo': 'Y',
         'list': None,
         'showBlocked': 'Y'}
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
    text = 'Enter user story to sync (eg. US12345)'
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
