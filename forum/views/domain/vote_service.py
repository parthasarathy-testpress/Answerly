from django.http import JsonResponse


def update_votes(request, model_object, vote_type, vote=None, created=None):
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

    vote_counts = model_object.get_vote_counts()

    return JsonResponse(
        {
            "status": status,
            "upvotes": vote_counts["upvotes"],
            "downvotes": vote_counts["downvotes"],
            "user_vote": vote_type,
        }
    )
