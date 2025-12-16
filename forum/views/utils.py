from django.contrib.contenttypes.models import ContentType
from forum.models import Vote


def attach_user_votes(user, objects):
    objs = list(objects)
    if not objs:
        return objs

    for obj in objs:
        obj.user_vote = 0

    if not user.is_authenticated:
        return objs

    content_type = ContentType.objects.get_for_model(objs[0].__class__)
    ids = [obj.id for obj in objs]

    votes = Vote.objects.filter(
        user=user,
        content_type=content_type,
        object_id__in=ids,
    ).values_list("object_id", "vote_type")

    vote_map = dict(votes)

    for obj in objs:
        obj.user_vote = vote_map.get(obj.id, 0)

    return objs
