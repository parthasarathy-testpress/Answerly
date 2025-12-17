from django.db.models import Q, Count
import django_filters
from taggit.models import Tag
from .models import Question, Vote


class VoteTypeFilterMixin(django_filters.FilterSet):
    vote_type = django_filters.ChoiceFilter(
        choices=Vote.VoteType.choices,
        method="filter_vote_type",
        empty_label="All votes",
        required=False,
        label="Vote type",
    )

    def filter_vote_type(self, queryset, name, value):
        if not value:
            return queryset
    
        if int(value) == Vote.VoteType.UPVOTE:
            return queryset.annotate(
                upvotes=Count(
                    "votes",
                    filter=Q(votes__vote_type=Vote.VoteType.UPVOTE),
                )
            ).filter(upvotes__gte=0).order_by("-upvotes", "-created_at")
    
        if int(value) == Vote.VoteType.DOWNVOTE:
            return queryset.annotate(
                downvotes=Count(
                    "votes",
                    filter=Q(votes__vote_type=Vote.VoteType.DOWNVOTE),
                )
            ).filter(downvotes__gte=0).order_by("-downvotes", "-created_at")
    
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
