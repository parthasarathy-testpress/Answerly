from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.views import View

from forum.models import Question, Answer, Comment, Vote


class VoteView(LoginRequiredMixin, View):
    login_url = None

    model_map = {
        "question": Question,
        "answer": Answer,
        "comment": Comment,
    }

    def handle_no_permission(self):
        return JsonResponse({"error": "Authentication required."}, status=401)

    def post(self, request, *args, **kwargs):
        model_key = kwargs.get("model")
        object_id = kwargs.get("object_id")
        vote_type = request.POST.get("vote_type")

        model_cls = self.model_map.get(model_key)
        if model_cls is None:
            return HttpResponseBadRequest("Invalid target type.")

        try:
            vote_value = int(vote_type)
        except (TypeError, ValueError):
            return HttpResponseBadRequest("vote_type must be 1 or -1.")

        if vote_value not in (1, -1):
            return HttpResponseBadRequest("vote_type must be 1 or -1.")

        target = get_object_or_404(model_cls, pk=object_id)
        content_type = ContentType.objects.get_for_model(model_cls)

        vote, created = Vote.objects.get_or_create(
            user=request.user,
            content_type=content_type,
            object_id=object_id,
            defaults={"vote_type": vote_value},
        )

        if created:
            status = "created"
        else:
            if vote.vote_type == vote_value:
                vote.delete()
                status = "removed"
                vote_value = 0
            else:
                vote.vote_type = vote_value
                vote.save(update_fields=["vote_type", "updated_at"])
                status = "updated"

        vote_counts = target.get_vote_counts()

        return JsonResponse(
            {
                "status": status,
                "upvotes": vote_counts["upvotes"],
                "downvotes": vote_counts["downvotes"],
                "user_vote": vote_value,
            }
        )

