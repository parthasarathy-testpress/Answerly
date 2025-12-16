from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View

from forum.models import Question, Answer, Comment
from forum.views.domain.vote_service import process_vote

class QuestionVoteView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        object_id = kwargs.get("object_id")
        vote_type = request.POST.get("vote_type")
        return process_vote(request, Question, object_id, vote_type)


class AnswerVoteView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        object_id = kwargs.get("object_id")
        vote_type = request.POST.get("vote_type")
        return process_vote(request, Answer, object_id, vote_type)


class CommentVoteView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        object_id = kwargs.get("object_id")
        vote_type = request.POST.get("vote_type")
        return process_vote(request, Comment, object_id, vote_type)
