from django import forms
from radabo.models import Story

class SearchForm(forms.Form):
    """
    Defines the form for the Sync Story function
    """
    class Meta:
        model = Story

    story = forms.CharField(
              label="User Story", 
              max_length=50, 
              help_text="User story format should match US12345",
              required=True
            )
