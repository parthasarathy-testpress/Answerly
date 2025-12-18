from django import template
import json

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


@register.simple_tag
def query_string_exclude_page(request):
    """Build query string from request.GET excluding 'page' parameter."""
    if not request or not hasattr(request, 'GET'):
        return ""
    
    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']
    
    return query_params.urlencode()


@register.filter
def tags_to_json(queryset):
    """Convert a tag queryset to JSON array format."""
    if not queryset:
        return '[]'
    tags_data = [{'id': tag.id, 'name': tag.name} for tag in queryset]
    return json.dumps(tags_data)


@register.simple_tag
def get_selected_tag_ids(request):
    """Get selected tag IDs from request.GET as JSON array."""
    if not request or not hasattr(request, 'GET'):
        return '[]'
    selected_tag_ids = [int(tag_id) for tag_id in request.GET.getlist('tag') if tag_id.isdigit()]
    return json.dumps(selected_tag_ids)
