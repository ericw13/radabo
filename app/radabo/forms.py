from django import forms
from radabo.models import Story

class SearchForm(forms.Form):
    class Meta:
        model = Story

    story = forms.CharField(label="User Story", max_length=50, help_text="User story format should match US12345",required=True)
