from django import template

register = template.Library()


@register.simple_tag
def get_user_vote(obj, user):
    """Return the vote type (1, -1 or 0) for `user` on `obj`.

    Safe to call from templates. Returns 0 for anonymous users or on error.
    """
    try:
        if not getattr(user, "is_authenticated", False):
            return 0
        if obj is None:
            return 0
        return obj.get_user_voted_type(user)
    except Exception:
        return 0
