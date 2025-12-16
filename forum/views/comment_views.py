from django.views.generic import UpdateView, DeleteView, ListView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin

from forum.models import Comment, Answer
from forum.forms import CommentForm
from forum.views.mixins import AuthorRequiredMixin

from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from django.contrib.contenttypes.models import ContentType
from forum.views.utils import attach_user_votes


class CommentUpdateView(LoginRequiredMixin, AuthorRequiredMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = "forum/comment_update_form.html"
    pk_url_kwarg = 'comment_id'

    def get_success_url(self):
        answer=self.object.content_object
        return reverse_lazy('answer_detail', kwargs={'answer_id': answer.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        answer=self.object.content_object
        context['cancel_url'] = reverse_lazy('answer_detail', kwargs={'answer_id': answer.pk})
        return context


class CommentDeleteView(LoginRequiredMixin, AuthorRequiredMixin, DeleteView):
    model = Comment
    template_name = "forum/comment_confirm_delete.html"
    pk_url_kwarg = 'comment_id'

    def get_success_url(self):
        answer=self.object.content_object
        return reverse_lazy('answer_detail', kwargs={'answer_id': answer.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        answer=self.object.content_object
        context['cancel_url'] = reverse_lazy('answer_detail', kwargs={'answer_id': answer.pk})
        return context

class CommentsPartialListView(ListView):
    model = Comment
    template_name = "forum/partials/comment_list.html"
    context_object_name = "comments"
    paginate_by = 3

    def dispatch(self, request, *args, **kwargs):
        self.answer = get_object_or_404(Answer, pk=self.kwargs.get("answer_id"))
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return (
            Comment.objects.filter(
                content_type=ContentType.objects.get_for_model(Answer),
                object_id=self.answer.pk,
                parent__isnull=True,
            )
            .select_related("author")
            .annotate(
                upvotes=Count("votes", filter=Q(votes__vote_type=1)),
                downvotes=Count("votes", filter=Q(votes__vote_type=-1)),
            )
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        attach_user_votes(self.request.user, context["comments"])
        context["htmx_target"] = "#comment-list"
        context["partial_url"] = self.request.path
        context["answer"] = self.answer
        return context
