from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.contrib.contenttypes.models import ContentType
from ..models import Answer, Comment,Question

class AuthorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        obj = self.get_object()
        return self.request.user == obj.author


class QuestionFilterMixin:

    def get_filtered_queryset(self):
        queryset = Question.objects.all()
        search_query = self.request.GET.get('question')
        tag_filter = self.request.GET.get('tag')
        
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query)
            )

        if tag_filter:
            queryset = queryset.filter(tags__name__iexact=tag_filter)

        return queryset.distinct()


class CommentNavigationMixin:
    _success_url = None

    def get_success_url(self):
        if self._success_url is None:
            root = self.object
            while root.parent is not None:
                root = root.parent
            answer = root.content_object
            self._success_url = reverse_lazy('answer_detail', kwargs={'answer_id': answer.pk})
        return self._success_url

class CommentMetaMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self, "get_success_url"):
            context["cancel_url"] = self.get_success_url()
        return context


class AnswerNavigationMixin:
    def get_success_url(self):
        return reverse_lazy('question_detail', kwargs={'question_id': self.object.question.pk})

class AnswerMetaMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['answer'] = self.object
        return context


class VoteContextMixin:
    def get_single_object_vote_context(self, obj, prefix):
        vote_counts = obj.get_vote_counts()
        return {
            f"{prefix}_upvotes": vote_counts["upvotes"],
            f"{prefix}_downvotes": vote_counts["downvotes"],
        }

class PaginationMixin:
    paginate_by = None

    def get_paginated_context(self, queryset, key):
        paginator = Paginator(queryset, self.paginate_by)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        return {
            key: page_obj,
            "paginator": paginator,
            "page_obj": page_obj,
            "is_paginated": page_obj.has_other_pages(),
        }


class QuestionDetailMixin(VoteContextMixin, PaginationMixin):
    paginate_by = 3

    def get_question_vote_context(self, question):
        return self.get_single_object_vote_context(question, "question")

    def get_paginated_answers_context(self, question):
        answers_qs = (
            question.answers.annotate(
                upvotes=Count('votes', filter=Q(votes__vote_type=1)),
                downvotes=Count('votes', filter=Q(votes__vote_type=-1))
            )
            .order_by('-created_at')
        )
        return self.get_paginated_context(answers_qs, "answers")


class AnswerDetailMixin(VoteContextMixin, PaginationMixin):
    paginate_by = 3

    def get_answer_vote_context(self, answer):
        return self.get_single_object_vote_context(answer, "answer")

    def get_paginated_comments_context(self, answer):
        comments_qs = self.get_vote_annotated_comments(answer)
        return self.get_paginated_context(comments_qs, "comments")

    def get_vote_annotated_comments(self, answer):
        comments = (
            Comment.objects.filter(
                content_type=ContentType.objects.get_for_model(Answer),
                object_id=answer.pk,
                parent__isnull=True
            )
            .select_related("author")
            .annotate(
                upvotes=Count("votes", filter=Q(votes__vote_type=1)),
                downvotes=Count("votes", filter=Q(votes__vote_type=-1)),
            )
            .order_by("-created_at")
        )

        for comment in comments:
            comment.replies_cached = list(self.get_vote_annotated_replies(comment))

        return comments
    
    def get_vote_annotated_replies(self,comment):
        replies = (
            comment.replies.select_related("author")
            .annotate(
                upvotes=Count("votes", filter=Q(votes__vote_type=1)),
                downvotes=Count("votes", filter=Q(votes__vote_type=-1)),
            )
            .order_by("-created_at")
        )
        for reply in replies:
            reply.replies_cached = list(self.get_vote_annotated_replies(reply))
        return replies
