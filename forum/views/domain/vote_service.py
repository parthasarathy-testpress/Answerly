from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404

from forum.models import Vote


def process_vote(request, model, object_id, vote_type):
    try:
        vote_type = int(vote_type)
        if vote_type not in (1, -1):
            raise ValueError
    except (TypeError, ValueError):
        return HttpResponseBadRequest("vote_type must be 1 or -1.")

    target = get_object_or_404(model, pk=object_id)
    content_type = ContentType.objects.get_for_model(model)

    vote, created = Vote.objects.get_or_create(
        user=request.user,
        content_type=content_type,
        object_id=object_id,
        defaults={"vote_type": vote_type},
    )

    if created:
        status = "created"
    else:
        if vote.vote_type == vote_type:
            vote.delete()
            status = "removed"
            vote_type = 0
        else:
            vote.vote_type = vote_type
            vote.save(update_fields=["vote_type"])
            status = "updated"

    vote_counts = target.get_vote_counts()

    return JsonResponse(
        {
            "status": status,
            "upvotes": vote_counts["upvotes"],
            "downvotes": vote_counts["downvotes"],
            "user_vote": vote_type,
        }
    )
