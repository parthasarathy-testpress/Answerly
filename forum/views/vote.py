from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from forum.models import Question, Answer, Comment, Vote
from forum.domain.vote import update_votes

class QuestionVoteView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        object_id = kwargs.get("object_id")
        vote_type = request.GET.get("vote_type")
        vote_type = int(vote_type)
        content_type = ContentType.objects.get_for_model(Question)

        vote, created = Vote.objects.get_or_create(
            user=request.user,
            content_type=content_type,
            object_id=object_id,
            defaults={"vote_type": vote_type},
        )
        question=get_object_or_404(Question, pk=object_id)

        return update_votes(request,question,vote_type, vote=vote, created=created)


class AnswerVoteView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        object_id = kwargs.get("object_id")
        vote_type = request.GET.get("vote_type")
        vote_type = int(vote_type)
        content_type = ContentType.objects.get_for_model(Answer)

        vote, created = Vote.objects.get_or_create(
            user=request.user,
            content_type=content_type,
            object_id=object_id,
            defaults={"vote_type": vote_type},
        )
        answer=get_object_or_404(Answer, pk=object_id)

        return update_votes(request,answer,vote_type, vote=vote, created=created)


class CommentVoteView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        object_id = kwargs.get("object_id")
        vote_type = request.GET.get("vote_type")
        vote_type = int(vote_type)
        content_type = ContentType.objects.get_for_model(Comment)

        vote, created = Vote.objects.get_or_create(
            user=request.user,
            content_type=content_type,
            object_id=object_id,
            defaults={"vote_type": vote_type},
        )
        comment=get_object_or_404(Comment, pk=object_id)

        return update_votes(request,comment,vote_type, vote=vote, created=created)
