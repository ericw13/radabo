from metrics.models import Sprint, Story, Release
from django.db.models import Q
from django.utils import timezone

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

