from django import forms
from .models import Question
from taggit.forms import TagField

class QuestionForm(forms.ModelForm):
    tags = TagField(
        required=False,
        help_text="Enter comma-separated tags (e.g. django, python).",
        widget=forms.TextInput(attrs={"placeholder": "e.g. django, python"})
    )

    class Meta:
        model = Question
        fields = ['title', 'description', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter question title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Describe your question'}),
        }
