from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible

class Module(models.Model):
    """
    Class that defines the various Oracle modules that may be impacted by a
    change.  Cross-functional is included.  This data is managed via admin
    form.
    """
    TRACK_CHOICES = (
        ('OTC', 'Order to Cash'),
        ('RTP', 'Requisition to Pay'),
        ('RTR', 'Record to Report'),
        ('OTH', 'Other'),
    )
    moduleName = models.CharField(max_length=30,
                                  unique=True,
                                  verbose_name="Module Name")
    track = models.CharField(max_length=3,choices=TRACK_CHOICES)
    globalLead = models.CharField(max_length=50,verbose_name="Global Lead")
    def __str__(self):
        return self.moduleName

class Sprint(models.Model):
    """
    Class that defines the sprint timebox.  This data is managed via rally
    WSAPI script loadSprint.py.  This script should be scheduled to run daily.
    """
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
    """
    Class that defines the release timebox.  This data is managed via rally
    WSAPI script loadRelease.py.  This script should be scheduled to run daily.
    """
    name = models.CharField(max_length=100,unique=True)
    startDate = models.DateTimeField()
    endDate = models.DateTimeField()
    status = models.CharField(max_length=20,default='Planning')
    def __str__(self):
        return self.name

class Session(models.Model):
    """
    This class defines a session used by updateStory.py.  It helps identify
    which stories were created/updated via Rally WSAPI and which were not.
    The second pass in updateStory.py looks for any story in the DB not already
    updated in the current session, verifies it is not available in Rally and
    deletes it locally.
    """
    startDate = models.DateTimeField(default=timezone.now)
    endDate = models.DateTimeField(null=True,blank=True)
    def __str__(self):
        return "%s: %s -> %s" % (self.id, self.startDate, self.endDate)
    def close(self):
        self.endDate = timezone.now()
        self.save()

@python_2_unicode_compatible
class Story(models.Model):
    """
    This class defines the Rally user story.  It has optional foreign key
    references to Module, Release, Sprint and Session.
    """
    STATUS_CHOICES = (
        ('B', 'Backlog'),
        ('D', 'Defined'),
        ('P', 'In-Progress'),
        ('C', 'Complete'),
        ('A', 'Accepted')
    )
    class Meta:
        verbose_name_plural = "stories"

    rallyNumber = models.CharField(max_length=20,unique=True)
    description = models.CharField(max_length=255)
    longDescription = models.CharField(max_length=2000,null=True,blank=True)
    storyType = models.CharField(max_length=20, default="Enhancement")
    points = models.IntegerField(null=True, blank=True)
    businessValue = models.IntegerField(null=True, blank=True)
    currentSprint = models.ForeignKey(Sprint, 
                                      on_delete=models.SET_NULL, 
                                      related_name='currentSprint',
                                      null=True, 
                                      blank=True)
    initialSprint = models.ForeignKey(Sprint, 
                                      on_delete=models.SET_NULL, 
                                      related_name='initialSprint',
                                      null=True, 
                                      blank=True)
    status = models.CharField(max_length=1,choices=STATUS_CHOICES,default='B')
    release = models.ForeignKey(Release, 
                                on_delete=models.SET_NULL, 
                                related_name='release',
                                null=True, 
                                blank=True)
    rallyCreationDate = models.DateTimeField(null=True,blank=True)
    completionDate = models.DateTimeField(null=True, blank=True)
    module = models.ForeignKey(Module, 
                               on_delete=models.SET_NULL, 
                               related_name='module',
                               null=True, 
                               blank=True)
    track = models.CharField(max_length=30, null=True, blank=True)
    theme = models.CharField(max_length=50, null=True, blank=True)
    stakeholders = models.CharField(max_length=255, null=True, blank=True)
    solutionSize = models.CharField(max_length=20, null=True, blank=True)
    blocked = models.CharField(max_length=1, default='N')
    session = models.ForeignKey(Session, 
                                on_delete=models.SET_NULL, 
                                related_name='session',
                                null=True, 
                                blank=True)
    storyURL = models.CharField(max_length=200,null=True, blank=True)
    blockedReason = models.CharField(max_length=512,null=True,blank=True)

    def __str__(self):
        return "%s: %s" % (self.rallyNumber, self.description)
    def _on_schedule(self):
        # Use of this function is deprecated, but left for reference
        return self.initialSprint == self.currentSprint

class Blog(models.Model):
    """
    This class defines the notes that can be displayed on the front page
    of the app.  The NOTE_TYPE_CHOICES drive the Bootstrap theme used to
    display the entry.
    """
    NOTE_TYPE_CHOICES = (
        ('I', 'Informational'),
        ('R', 'Release Notes'),
        ('W', 'Warnings'),
    )
    note = models.CharField(max_length=1000)
    noteType = models.CharField(max_length=1,
                                choices=NOTE_TYPE_CHOICES,
                                verbose_name="Note Type")
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.note[:40] + ("..." if len(self.note)>40 else "")

    class Meta:
        verbose_name = "Blog entry"
        verbose_name_plural = "Blog entries"
