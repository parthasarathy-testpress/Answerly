from django.shortcuts import get_object_or_404
from ..models import Question, Vote,Answer,Comment
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.views import View
from django.http import JsonResponse, HttpResponseBadRequest


class VoteView(LoginRequiredMixin,View):
    model_map = {
        "question": Question,
        "answer": Answer,
        "comment": Comment,
    }

    def post(self, request, *args, **kwargs):
        model = request.POST.get("model")
        obj_id = request.POST.get("id")
        vote_type = request.POST.get("type")

        if not (model and obj_id and vote_type):
            return HttpResponseBadRequest("Missing parameters")

        try:
            vote_type = self.validate_vote_type(vote_type)
        except ValueError as e:
            return HttpResponseBadRequest(str(e))

        try:
            obj, content_type = self.get_object_and_contenttype(model, obj_id)
        except ValueError as e:
            return HttpResponseBadRequest(str(e))

        action, current_vote = self.process_vote(request.user, obj, content_type, vote_type)

        upvotes, downvotes = self.get_vote_counts(obj)

        return JsonResponse({
            "upvotes": upvotes,
            "downvotes": downvotes,
            "action": action,
            "current_vote": current_vote,
        })

    def validate_vote_type(self, vtype):
        try:
            vote_type = int(vtype)
        except ValueError:
            raise ValueError(f"Invalid vote type: {vtype}")
        if vote_type not in (1, -1):
            raise ValueError(f"Invalid vote type: {vote_type}. Vote type must be 1 or -1.")
        return vote_type

    def get_object_and_contenttype(self, model_name, obj_id):
        ModelClass = self.model_map.get(model_name.lower())
        if ModelClass is None:
            raise ValueError(f"Invalid model name: {model_name}")

        obj = get_object_or_404(ModelClass, pk=obj_id)
        content_type = ContentType.objects.get_for_model(ModelClass)
        return obj, content_type

    def process_vote(self, user, obj, content_type, vote_type):

        try:
            vote = Vote.objects.get(user=user, content_type=content_type, object_id=obj.pk)
        except Vote.DoesNotExist:
            vote = None

        if vote is None:
            Vote.objects.create(user=user, content_object=obj, vote_type=vote_type)
            return "created", vote_type
        elif vote.vote_type == vote_type:
            vote.delete()
            return "deleted", 0
        else:
            vote.vote_type = vote_type
            vote.save()
            return "updated", vote_type

    def get_vote_counts(self, obj):
        counts = obj.get_vote_counts()
        return counts["upvotes"], counts["downvotes"]
