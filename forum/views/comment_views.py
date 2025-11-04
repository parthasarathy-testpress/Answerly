from django.views.generic import UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from ..models import Comment
from ..forms import CommentForm
from .mixins import AuthorRequiredMixin,CommentNavigationMixin, CommentMetaMixin

class CommentUpdateView(LoginRequiredMixin, AuthorRequiredMixin, CommentMetaMixin, CommentNavigationMixin,UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = "forum/comment_update_form.html"
    pk_url_kwarg = 'comment_id'


class CommentDeleteView(LoginRequiredMixin, AuthorRequiredMixin, CommentMetaMixin, CommentNavigationMixin,DeleteView):
    model = Comment
    template_name = "forum/comment_confirm_delete.html"
    pk_url_kwarg = 'comment_id'
