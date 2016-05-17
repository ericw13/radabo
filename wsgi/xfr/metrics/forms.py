from django import forms
from metrics.models import Story

class SearchForm(forms.Form):
    class Meta:
        model = Story
    story = forms.CharField(label="User Story", max_length=50, required=True)
