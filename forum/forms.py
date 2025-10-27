from django import forms
from .models import Question,Answer
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

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['content']
