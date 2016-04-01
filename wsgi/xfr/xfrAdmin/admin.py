from django.contrib import admin
from django import forms
from .models import Host, Directory, Login, Process, Argument, User, NotificationList, NotificationUser, TransferLocation

# Register your models here.
class DirectoryInline(admin.TabularInline):
    model = Directory
    verbose_name = "directory"
    verbose_name_plural = "directories"
    extra = 1
    fieldsets = [
        ('Directory Information', {'fields': ['directory_path']}),
    ]

class LoginInline(admin.TabularInline):
    model = Login
    verbose_name = "login"
    verbose_name_plural = "logins"
    extra = 1
    fieldsets = [
         ('Login Information', {'fields': ['user_name', 'account_description', 'port', 'password']}),
    ]

class HostAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,                    {'fields': ['host_alias', 'host_name', 'description']}),
    ]
    inlines = [DirectoryInline, LoginInline]
    verbose_name = "host"
    verbose_name_plural = "hosts"
    list_filter = ['creation_date']
    search_fields = ['host_alias', 'host_name']

class ArgumentInline(admin.TabularInline):
    model = Argument
    extra = 2
    fieldsets = [
        ('Command Line Arguments', {'fields': ['command','options']}),
    ]

class ProcessAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Process', {'fields': ['process_name','script_location']}),
    ]
    inlines = [ArgumentInline]
    list_filter = ['creation_date']
    search_fields = ['process_name']
    verbose_name_plural = 'processes'

class NotifUserInline(admin.TabularInline):
    model = NotificationUser
    extra = 1

class NotifListAdmin(admin.ModelAdmin):
    inlines = [NotifUserInline]
    list_filter = ['creation_date']
    search_fields = ['list_name']

def loginform_factory(hostId):
    class LoginForm(forms.ModelForm):
        login_id = forms.ModelChoiceField(
           queryset=Logins.objects.filter(host=hostId)
        )
    return LoginForm

class LocationInlineForm(forms.ModelForm):
    def __init__(self,*args,**kwargs):
        super(LocationInlineForm, self).__init__(*args, **kwargs)
        self.fields['local_directory'].queryset = Directory.objects.filter(host=1)

class TransferLocationAdmin(admin.ModelAdmin):

    list_filter = ['creation_date']
    search_fields = ['location_code', 'remote_host']
    fieldsets = [
        (None, {'fields': [('location_code','transfer_direction'),('remote_host', 'login')] }),
        ('Directories', {'fields': [('local_directory', 'remote_directory', 'archive_directory')] }),
        ('Tasks', {'fields': [('process','notification_list')] }),
        ('Rename Capabilities', {'fields': [('current_suffix','local_rename_suffix','remote_rename_suffix')] }),
        ('Auto Transfer', {'fields': [('auto_transfer_enabled', 'filename_mask')] }),
    ]
    form = LocationInlineForm

admin.site.register(Host, HostAdmin)
admin.site.register(Process, ProcessAdmin)
admin.site.register(User)
admin.site.register(NotificationList, NotifListAdmin)
admin.site.register(TransferLocation, TransferLocationAdmin)
