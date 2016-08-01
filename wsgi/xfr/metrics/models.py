from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible

class Module(models.Model):
    TRACK_CHOICES = (
        ('OTC', 'Order to Cash'),
        ('RTP', 'Requisition to Pay'),
        ('RTR', 'Record to Report'),
        ('OTH', 'Other'),
    )
    moduleName = models.CharField(max_length=30,unique=True,verbose_name="Module Name")
    track = models.CharField(max_length=3,choices=TRACK_CHOICES)
    globalLead = models.CharField(max_length=50,verbose_name="Global Lead")
    def __str__(self):
        return self.moduleName

class Sprint(models.Model):
    name = models.CharField(max_length=50,unique=True)
    startDate = models.DateTimeField()
    endDate = models.DateTimeField()
    velocity = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20,default='Planning')
    def __str__(self):
       return self.name
    def to_json(self):
       return {
          'name': self.name,
          'velocity': self.velocity,
       }

class Release(models.Model):
    name = models.CharField(max_length=100,unique=True)
    startDate = models.DateTimeField()
    endDate = models.DateTimeField()
    status = models.CharField(max_length=20,default='Planning')
    def __str__(self):
        return self.name

class Session(models.Model):
    startDate = models.DateTimeField(default=timezone.now)
    endDate = models.DateTimeField(null=True,blank=True)
    def __str__(self):
        return "%s: %s -> %s" % (self.id, self.startDate, self.endDate)
    def close(self):
        self.endDate = timezone.now()
        self.save()

@python_2_unicode_compatible
class Story(models.Model):
    STATUS_CHOICES = (
        ('B', 'Backlog'),
        ('D', 'Defined'),
        ('P', 'In-Progress'),
        ('C', 'Complete'),
        ('A', 'Accepted')
    )
    BV_CHOICES = (
        (None, 'Undefined'),
        (0, 'IT Research'),
        (1, 'Nice to Have'),
        (3, 'Personal Productivity Improvement'),
        (5, 'Regional Productivity Improvement'),
        (8, 'Global Productivity Improvement'),
        (13, 'Impacting Financials, Cash, Revenue or Payments'),
        (20, 'Compliance')
    )
    class Meta:
        verbose_name_plural = "stories"

    rallyNumber = models.CharField(max_length=20,unique=True)
    description = models.CharField(max_length=255)
    longDescription = models.CharField(max_length=2000,null=True,blank=True)
    storyType = models.CharField(max_length=20, default="Enhancement")
    points = models.IntegerField(null=True, blank=True)
    businessValue = models.IntegerField(choices=BV_CHOICES, null=True, blank=True)
    currentSprint = models.ForeignKey(Sprint, on_delete=models.SET_NULL, related_name='currentSprint',null=True, blank=True)
    initialSprint = models.ForeignKey(Sprint, on_delete=models.SET_NULL, related_name='initialSprint',null=True, blank=True)
    status = models.CharField(max_length=1,choices=STATUS_CHOICES,default='B')
    release = models.ForeignKey(Release, on_delete=models.SET_NULL, related_name='release',null=True, blank=True)
    completionDate = models.DateTimeField(null=True, blank=True)
    module = models.CharField(max_length=50, null=True, blank=True)
    track = models.CharField(max_length=30, null=True, blank=True)
    theme = models.CharField(max_length=50, null=True, blank=True)
    stakeholders = models.CharField(max_length=255, null=True, blank=True)
    solutionSize = models.CharField(max_length=20, null=True, blank=True)
    blocked = models.CharField(max_length=1, default='N')
    session = models.ForeignKey(Session, on_delete=models.SET_NULL, related_name='session',null=True, blank=True)
    storyURL = models.CharField(max_length=200,null=True, blank=True)
    blockedReason = models.CharField(max_length=512,null=True,blank=True)

    def __str__(self):
        return "%s: %s" % (self.rallyNumber, self.description)
    def _on_schedule(self):
        return self.initialSprint == self.currentSprint

class Blog(models.Model):
    NOTE_TYPE_CHOICES = (
        ('I', 'Informational'),
        ('R', 'Release Notes'),
        ('W', 'Warnings'),
    )
    note = models.CharField(max_length=1000)
    noteType = models.CharField(max_length=1,choices=NOTE_TYPE_CHOICES,verbose_name="Note Type")
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.note[:40] + ("..." if len(self.note)>40 else "")

    class Meta:
        verbose_name = "Blog entry"
        verbose_name_plural = "Blog entries"
