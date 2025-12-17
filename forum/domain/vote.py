from django.http import JsonResponse


def update_votes(request, model_object, vote_type, vote=None, created=None):
    if not created:
        if vote.vote_type == vote_type:
            vote.delete()
            vote_type = 0
        else:
            vote.vote_type = vote_type
            vote.save(update_fields=["vote_type"])

    vote_counts = model_object.get_vote_counts()

    return JsonResponse(
        {
            "upvotes": vote_counts["upvotes"],
            "downvotes": vote_counts["downvotes"],
            "user_vote": vote_type,
        }
    )
