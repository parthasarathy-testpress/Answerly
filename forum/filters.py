from django.db.models import Q
import django_filters
from taggit.models import Tag
from .models import Question


class QuestionFilter(django_filters.FilterSet):
    question = django_filters.CharFilter(
        method='filter_question',
    )

    tag = django_filters.ChoiceFilter(
        method='filter_tag',
        choices=[],
        empty_label=None,
    )

    class Meta:
        model = Question
        fields = ['question', 'tag']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tags = Tag.objects.all().order_by('name')
        choices = [('All', 'All Tags')] + [(t.name, t.name) for t in tags]
        self.filters['tag'].field.choices = choices

    def filter_question(self, queryset, name, value):
        if value:
            return queryset.filter(
                Q(title__icontains=value) |
                Q(description__icontains=value)
            )
        return queryset

    def filter_tag(self, queryset, name, value):
        if not value or value == 'All':
            return queryset
        return queryset.filter(tags__name__iexact=value)
