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

        vote_type = int(value)
        if vote_type == Vote.VoteType.UPVOTE:
            annotation_name = 'upvotes'
        elif vote_type == Vote.VoteType.DOWNVOTE:
            annotation_name = 'downvotes'
        else:
            return queryset

        return queryset.annotate(
            **{annotation_name: Count("votes", filter=Q(votes__vote_type=vote_type))}
        ).order_by(f"-{annotation_name}", "-created_at")


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
