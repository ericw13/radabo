from django.contrib import admin
from metrics.models import Module

# Register your models here.
class ModuleAdmin(admin.ModelAdmin):
    model = Module
    search_fields = ['moduleName']
    ordering = ('moduleName',)

admin.site.register(Module, ModuleAdmin)
