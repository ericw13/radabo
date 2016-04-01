from django import forms
from .models import FileTransfer
from django.forms.fields import DateField
from django.forms.extras.widgets import SelectDateWidget

class SearchForm(forms.Form):
    class Meta:
        model = FileTransfer
    filename = forms.CharField(label="File Name", max_length=255, required=False)
    #start_date = forms.DateField(widget=SelectDateWidget(),label="Start Date", required=False)
    status = forms.CharField(label="Transfer Status", max_length=1, required=False)
