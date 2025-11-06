from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View
from django.shortcuts import get_object_or_404
from ..models import Question, Answer, Comment, Vote


class VoteViewMixin(LoginRequiredMixin):
    model = None

    def post(self, request, *args, **kwargs):
        raw_vote_value = self.get_vote_type_from_request(request)
        result = self.validate_vote_type(raw_vote_value)

        if isinstance(result, JsonResponse):
            return result
        vote_type = result

        param_name = {
            Question: 'question_id',
            Answer: 'answer_id',
            Comment: 'comment_id'
        }[self.model]
        
        obj = get_object_or_404(self.model, pk=kwargs[param_name])
        existing = obj.votes.filter(user=request.user).first()

        if existing:
            if existing.vote_type == vote_type:
                existing.delete()
                user_vote = 0
            else:
                existing.vote_type = vote_type
                existing.save()
                user_vote = vote_type
        else:
            obj.votes.create(user=request.user, vote_type=vote_type)
            user_vote = vote_type

        counts = obj.get_vote_counts()
        return JsonResponse({
            'upvotes': counts['upvotes'],
            'downvotes': counts['downvotes'],
            'user_vote': user_vote,
        })

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


class AnswerVoteView(VoteViewMixin, View):
    model = Answer


class CommentVoteView(VoteViewMixin, View):
    model = Comment
