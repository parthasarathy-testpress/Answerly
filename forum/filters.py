from django.db.models import Q, Count
import django_filters
from taggit.models import Tag
from .models import Question, Answer, Comment, Vote

from django.db import models

class PopularityChoice(models.IntegerChoices):
    MOST_LIKED = Vote.VoteType.UPVOTE, "Most liked"
    LEAST_LIKED = Vote.VoteType.DOWNVOTE, "Least liked"

class VoteTypeFilterMixin(django_filters.FilterSet):
    vote_type = django_filters.ChoiceFilter(
        choices=PopularityChoice.choices,
        method="filter_vote_type",
        empty_label='Filter By Votes', 
        required=False,
        label="Popularity",
    )

    def filter_vote_type(self, queryset, name, value):
        if not value:
            return queryset

        value_int = int(value)
        if value_int == Vote.VoteType.UPVOTE:
            return queryset.order_by("-upvotes", "-created_at")
        elif value_int == Vote.VoteType.DOWNVOTE:
            return queryset.order_by("-downvotes", "-created_at")
        else:
            return queryset

class QuestionFilter(VoteTypeFilterMixin):
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
        fields = ['question', 'tag', 'vote_type']

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


class AnswerFilter(VoteTypeFilterMixin):
    class Meta:
        model = Answer
        fields = ['vote_type']


class CommentFilter(VoteTypeFilterMixin):
    class Meta:
        model = Comment
        fields = ['vote_type']
