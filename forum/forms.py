from django import forms
from .models import Question
from taggit.forms import TagField

class QuestionForm(forms.ModelForm):
    tags = TagField(
        label="Tags",
        required=False,
        help_text="Enter comma-separated tags (e.g. django, python)."
    )

    class Meta:
        model = Question
        fields = ['title', 'description', 'tags']
