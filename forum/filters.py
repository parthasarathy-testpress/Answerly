from django import forms
from django.db.models import Q
import django_filters
from taggit.models import Tag

from .models import Question


class QuestionFilter(django_filters.FilterSet):

    question = django_filters.CharFilter(method='filter_question', label='',
                                          widget=forms.TextInput(attrs={
                                              'class': 'form-control rounded-pill px-4 py-3',
                                              'placeholder': 'Enter a keyword...'
                                          }))

    tag = django_filters.CharFilter(field_name='tags__name', lookup_expr='iexact', label='',
                                    widget=forms.Select(attrs={'class': 'form-select rounded-pill px-4 py-3'}))

    class Meta:
        model = Question
        fields = ['question', 'tag']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tags = Tag.objects.all().order_by('name')
        choices = [('', 'All Tags')] + [(t.name, t.name) for t in tags]
        try:
            self.filters['tag'].field.choices = choices
        except Exception:
            pass

    def filter_question(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(Q(title__icontains=value) | Q(description__icontains=value))
