from django import forms
from django.contrib import admin
from radabo.models import Module, Blog

# Register your models here.
class ModuleAdmin(admin.ModelAdmin):
    model = Module
    search_fields = ['moduleName']
    ordering = ('moduleName',)

class BlogAdmin(admin.ModelAdmin):
    """
    Need to override the default widget for the Blog entry to use a Textarea.
    This will make it easier to edit information.
    """
    def formfield_for_dbfield(self, db_field, **kwargs):
        formfield = (super(BlogAdmin, self)
                    .formfield_for_dbfield(db_field, **kwargs))
        if db_field.name == 'note':
            formfield.widget = forms.Textarea(attrs=formfield.widget.attrs)
        return formfield

    model = Blog
    fieldsets = [
     (None, {'fields': ['noteType','note']}),
    ]

admin.site.register(Blog, BlogAdmin)
admin.site.register(Module, ModuleAdmin)
