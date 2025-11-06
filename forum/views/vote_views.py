from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View
from django.shortcuts import get_object_or_404
from ..models import Question, Answer, Comment, Vote


class VoteViewMixin(LoginRequiredMixin):

    def post(self, request, *args, **kwargs):
        raw_vote_value = self.get_vote_type_from_request(request)
        result = self.validate_vote_type(raw_vote_value)

        if isinstance(result, JsonResponse):
            return result
        vote_type = result

        obj = self.get_object(request, **kwargs)

        user_vote = self.apply_vote(obj, vote_type, request.user)

        counts = obj.get_vote_counts()
        return JsonResponse({
            'upvotes': counts['upvotes'],
            'downvotes': counts['downvotes'],
            'user_vote': user_vote,
        })

    def apply_vote(self, obj, vote_type, user):
        existing = obj.votes.filter(user=user).first()

        if existing:
            if existing.vote_type == vote_type:
                existing.delete()
                user_vote = 0
            else:
                existing.vote_type = vote_type
                existing.save()
                user_vote = vote_type
        else:
            obj.votes.create(user=user, vote_type=vote_type)
            user_vote = vote_type

        return user_vote

    def validate_vote_type(self, raw_value):
        try:
            return self.clean_vote_type(raw_value)
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)

    def get_vote_type_from_request(self, request):
        return request.POST.get("vote_type")

    def clean_vote_type(self, vote_type_raw):
        try:
            vote_type = int(vote_type_raw)
        except (TypeError, ValueError):
            raise ValueError("Invalid vote_type")

        if vote_type not in (1, -1):
            raise ValueError("vote_type must be 1 or -1")

        return vote_type


class QuestionVoteView(VoteViewMixin, View):
    model = Question

    def get_object(self, request, **kwargs):
        return get_object_or_404(Question, pk=kwargs['question_id'])


class AnswerVoteView(VoteViewMixin, View):
    model = Answer

    def get_object(self, request, **kwargs):
        return get_object_or_404(Answer, pk=kwargs['answer_id'])


class CommentVoteView(VoteViewMixin, View):
    model = Comment

    def get_object(self, request, **kwargs):
        return get_object_or_404(Comment, pk=kwargs['comment_id'])
