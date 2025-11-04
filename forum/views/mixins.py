from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.contrib.contenttypes.models import ContentType
from ..models import Answer, Comment, Vote

class AuthorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        obj = self.get_object()
        return self.request.user == obj.author


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
        context = {
            f"{prefix}_upvotes": vote_counts["upvotes"],
            f"{prefix}_downvotes": vote_counts["downvotes"],
        }
    
        user = self.request.user
        if not user.is_authenticated:
            context[f"{prefix}_user_vote"] = 0
            return context
    
        try:
            content_type = ContentType.objects.get_for_model(obj.__class__)
            vote = Vote.objects.get(user=user, content_type=content_type, object_id=obj.pk)
            context[f"{prefix}_user_vote"] = vote.vote_type
        except Vote.DoesNotExist:
            context[f"{prefix}_user_vote"] = 0
    
        return context


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
   
     
class AssignUserVotesMixin:

    def assign_user_votes_to_queryset(self, queryset, user, model):
        if user.is_authenticated:
            ids = [obj.pk for obj in queryset]
            votes_map = self.get_user_votes_map(user, model, ids)
            for obj in queryset:
                obj.user_vote = votes_map.get(obj.pk, 0)
        else:
            for obj in queryset:
                obj.user_vote = 0
        return queryset 

    def assign_user_votes_to_nested_comments(self, comments, user):
        def collect_ids(comment):
            ids = [comment.pk]
            for reply in getattr(comment, 'replies_cached', []):
                ids.extend(collect_ids(reply))
            return ids

        all_ids = []
        for comment in comments:
            all_ids.extend(collect_ids(comment))

        votes_map = (
            self.get_user_votes_map(user, comments.model, all_ids)
            if user.is_authenticated else {}
        )

        def assign(comment):
            comment.user_vote = votes_map.get(comment.pk, 0)
            for reply in getattr(comment, 'replies_cached', []):
                assign(reply)

        for comment in comments:
            assign(comment)

        return comments

    def get_user_votes_map(self, user, model, object_ids):
        if not object_ids:
            return {}
        content_type = ContentType.objects.get_for_model(model)
        votes = Vote.objects.filter(
            user=user,
            content_type=content_type,
            object_id__in=object_ids
        )
        return {vote.object_id: vote.vote_type for vote in votes}



class QuestionDetailMixin(VoteContextMixin, PaginationMixin, AssignUserVotesMixin):
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
        answers_qs = self.assign_user_votes_to_queryset(answers_qs, self.request.user, Answer)
        return self.get_paginated_context(answers_qs, "answers")


class AnswerDetailMixin(VoteContextMixin, PaginationMixin, AssignUserVotesMixin):
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

        comments = self.assign_user_votes_to_nested_comments(comments, self.request.user)
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
