from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from smart_selects.db_fields import ChainedForeignKey

# Create your models here.
class Host(models.Model):
    host_alias = models.CharField(max_length=50,unique=True)
    host_name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, null=True, blank=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    last_update_date = models.DateTimeField(auto_now=True)
    def __str__(self):
        return "%s - %s" % (self.host_alias, self.host_name)

class Directory(models.Model):
    class Meta:
        verbose_name_plural = "directories"
    host = models.ForeignKey(Host, on_delete=models.CASCADE)
    directory_path = models.CharField(max_length=255)
    creation_date = models.DateTimeField(auto_now_add=True)
    last_update_date = models.DateTimeField(auto_now=True)
    class Meta:
        unique_together = ("host", "directory_path")
    def __str__(self):
        return "%s:%s" % (self.host.host_alias, self.directory_path)

class Login(models.Model):
    host = models.ForeignKey(Host, on_delete=models.CASCADE)
    user_name = models.CharField(max_length=64)
    account_description = models.CharField(max_length=255,null=True,blank=True)
    port = models.IntegerField(null=True, blank=True)
    password = models.CharField(max_length=32,null=True, blank=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    last_update_date = models.DateTimeField(auto_now=True)
    class Meta:
        unique_together = ("host", "user_name")
    def __str__(self):
        return self.user_name

class Process(models.Model):
    process_name = models.CharField(max_length=64,unique=True)
    script_location = models.CharField(max_length=255)
    creation_date = models.DateTimeField(auto_now_add=True)
    last_update_date = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name_plural = "processes"
    def __str__(self):
        return self.process_name

class Argument(models.Model):
    process = models.ForeignKey(Process,on_delete=models.CASCADE)
    command = models.CharField(max_length=30,null=True,blank=True)
    options = models.CharField(max_length=1024, null=True,blank=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    last_update_date = models.DateTimeField(auto_now=True)
    def __str__(self):
        return "%s %s" % (self.process.process_name, self.command)
    class Meta:
        unique_together = ("process","command")

class User(models.Model):
    ACTIVE = 'A'
    INACTIVE = 'I'
    STATUS_CHOICES = ( (ACTIVE,'Active'), (INACTIVE,'Inactive') )
    sso_user_id = models.CharField(max_length=20,unique=True)
    email_address = models.CharField(max_length=100,unique=True)
    user_name = models.CharField(max_length=100)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default=ACTIVE)
    creation_date = models.DateTimeField(auto_now_add=True)
    last_update_date = models.DateTimeField(auto_now=True)
    def __str__(self):
        return "%s (%s)" % (self.user_name, self.email_address)

class NotificationList(models.Model):
    list_name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=255,null=True,blank=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    last_update_date = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name_plural = 'notification lists'
    def __str__(self):
        return self.list_name

class NotificationUser(models.Model):
    ACTIVE = 'A'
    INACTIVE = 'I'
    STATUS_CHOICES = ( (ACTIVE,'Active'), (INACTIVE,'Inactive') )
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    notification_list = models.ForeignKey(NotificationList,on_delete=models.CASCADE)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default=ACTIVE)
    creation_date = models.DateTimeField(auto_now_add=True)
    last_update_date = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name_plural = 'notified users'
        unique_together = ("notification_list","user")
    def __str__(self):
        return "%s - %s" % (self.notification_list.list_name, self.user.email_address)

class TransferLocation(models.Model):
    ACTIVE = 'A'
    INACTIVE = 'I'
    YES = 'Y'
    NO = 'N'
    PUSH = 'PUSH'
    PULL = 'PULL'
    STATUS_CHOICES = ( (ACTIVE,'Active'), (INACTIVE,'Inactive') )
    DIRECTION_CHOICES = ( (PUSH, 'Push'), (PULL, 'Pull') )
    ENABLED_CHOICES = ( (YES,'Yes'), (NO,'No') )
    location_code = models.CharField(max_length=30,unique=True)
    remote_host = models.ForeignKey(Host, on_delete=models.CASCADE)
    login = ChainedForeignKey(Login,
                      chained_field="remote_host",
                      chained_model_field="host",
                      show_all=False,
                      auto_choose=True)
    transfer_direction=models.CharField(max_length=4, 
                      choices=DIRECTION_CHOICES, 
                      default=PULL)
    local_directory=models.ForeignKey(Directory,
                      on_delete=models.SET_DEFAULT,
                      default=-1,
                      db_column='local_directory',
                      related_name='local_dir')
    remote_directory=ChainedForeignKey(Directory,
                      chained_field="remote_host",
                      chained_model_field="host",
                      on_delete=models.SET_DEFAULT,
                      default=-1,
                      show_all=False,
                      auto_choose=True,
                      db_column='remote_directory',
                      related_name='remote_dir')
    archive_directory=models.ForeignKey(Directory,
                      on_delete=models.SET_NULL,
                      db_column='archive_directory',
                      related_name='archive_dir',
                      null=True,
                      blank=True)
    current_suffix = models.CharField(max_length=50,null=True,blank=True)
    local_rename_suffix = models.CharField(max_length=50,null=True,blank=True)
    remote_rename_suffix = models.CharField(max_length=50,null=True,blank=True)
    auto_transfer_enabled = models.CharField(max_length=1,choices=ENABLED_CHOICES,default=YES)
    filename_mask = models.CharField(max_length=50,null=True,blank=True)
    process = models.ForeignKey(Process,
                      on_delete=models.SET_DEFAULT,
                      default=-1,
                      db_column='process')
    notification_list = models.ForeignKey(NotificationList,
                      on_delete=models.SET_NULL,
                      db_column='notification_list',
                      null=True,
                      blank=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    last_update_date = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name_plural = 'transfer locations'
    def __str__(self):
        return self.location_code

class FileTransfer(models.Model):
    NEW = 'N'
    INPROCESS = 'I'
    COMPLETE = 'C'
    ERROR = 'E'
    STATUS_CHOICES = (
        (NEW, 'New'),
        (INPROCESS, 'In Process'),
        (COMPLETE, 'Complete'),
        (ERROR, 'Error')
    )
    location = models.ForeignKey(TransferLocation,on_delete=models.SET_DEFAULT,default=-1,related_name='loc_code')
    filename = models.CharField(max_length=255)
    status = models.CharField(max_length=1,choices=STATUS_CHOICES,default=NEW)
    error_message = models.CharField(max_length=1000,null=True,blank=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    last_update_date = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name_plural = 'files transferred'
    def __str__(self):
        return "%s: %s" % (self.location.location_code, self.filename)
