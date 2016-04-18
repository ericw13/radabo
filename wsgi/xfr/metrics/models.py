from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible

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

class Story(models.Model):
    STATUS_CHOICES = (
        ('B', 'Backlog'),
        ('D', 'Defined'),
        ('P', 'In-Progress'),
        ('C', 'Complete'),
        ('A', 'Accepted')
    )
    BV_CHOICES = (
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
    points = models.IntegerField(null=True, blank=True)
    businessValue = models.IntegerField(choices=BV_CHOICES, null=True, blank=True)
    currentSprint = models.ForeignKey(Sprint, on_delete=models.SET_NULL, related_name='currentSprint',null=True, blank=True)
    initialSprint = models.ForeignKey(Sprint, on_delete=models.SET_NULL, related_name='initialSprint',null=True, blank=True)
    status = models.CharField(max_length=1,choices=STATUS_CHOICES,default='B')
    release = models.ForeignKey(Release, on_delete=models.SET_NULL, related_name='release',null=True, blank=True)
    completionDate = models.DateTimeField(null=True, blank=True)
    rallyOID = models.BigIntegerField()
    revHistoryURL = models.CharField(max_length=500)
    module = models.CharField(max_length=50, null=True, blank=True)
    track = models.CharField(max_length=30, null=True, blank=True)
    stakeholders = models.CharField(max_length=255, null=True, blank=True)
    @property
    def solutionSize(self):
        if self.points <= 3:
           return "Small"
        elif self.points <= 8:
           return "Medium"
        elif self.points <= 99:
           return "Large"
        else:
           return None

    def __str__(self):
        return "%s: %s" % (self.rallyNumber, self.description)
    def _on_schedule(self):
        return self.initialSprint == self.currentSprint
