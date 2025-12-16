from django.db.models import Q
import django_filters
from taggit.models import Tag
from .models import Question


class QuestionFilter(django_filters.FilterSet):
    question = django_filters.CharFilter(
        method='filter_question',
    )

    tag = django_filters.ModelChoiceFilter(
        queryset=Tag.objects.all().order_by('name'),
        method='filter_tag',
        empty_label='All Tags',
        required=False,
    )

    class Meta:
        model = Question
        fields = ['question', 'tag']

    def filter_question(self, queryset, name, value):
        if value:
            return queryset.filter(
                Q(title__icontains=value) |
                Q(description__icontains=value)
            )
        return queryset

    def filter_tag(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(tags__in=[value])