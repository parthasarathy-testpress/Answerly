from django.shortcuts import get_object_or_404, redirect
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.contrib.contenttypes.models import ContentType

from forum.models import Answer, Question, Comment
from forum.forms import AnswerForm, CommentForm
from forum.views.mixins import AuthorRequiredMixin


class AnswerCreateView(LoginRequiredMixin, CreateView):
    model = Answer
    form_class = AnswerForm
    template_name = "forum/answer_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.question = get_object_or_404(Question, pk=self.kwargs.get("question_id"))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.question = self.question
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('question_detail', kwargs={'question_id': self.object.question_id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['question'] = self.question
        return context


class AnswerUpdateView(LoginRequiredMixin, AuthorRequiredMixin, UpdateView):
    model = Answer
    form_class = AnswerForm
    template_name = "forum/answer_update_form.html"
    pk_url_kwarg = 'answer_id'
    
    def get_success_url(self):
        return reverse_lazy('question_detail', kwargs={'question_id': self.object.question.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['answer'] = self.object
        return context


class AnswerDeleteView(LoginRequiredMixin, AuthorRequiredMixin, DeleteView):
    model = Answer
    template_name = "forum/answer_confirm_delete.html"
    pk_url_kwarg = 'answer_id'
    
    def get_success_url(self):
        return reverse_lazy('question_detail', kwargs={'question_id': self.object.question.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['answer'] = self.object
        return context


class AnswerDetailView(DetailView):
    model = Answer
    template_name = "forum/answer_detail.html"
    pk_url_kwarg = 'answer_id'
    context_object_name = 'answer'
    paginate_comments_by = 3

    def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            answer = self.object
            context.update(self.get_answer_vote_context(answer))
            context.update(self.get_paginated_comments_context(answer))
            context["question"] = answer.question
            context["comment_form"] = kwargs.get("comment_form", CommentForm())
            return context

    def get_answer_vote_context(self, answer):
        vote_counts = answer.get_vote_counts()
        return {
            "answer_upvotes": vote_counts["upvotes"],
            "answer_downvotes": vote_counts["downvotes"],
        }

    def get_paginated_comments_context(self, answer):
        comments_qs = self.get_annotated_comments(answer)
        paginator = Paginator(comments_qs, self.paginate_comments_by)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        return {
            "comments": page_obj,
            "paginator": paginator,
            "page_obj": page_obj,
            "is_paginated": page_obj.has_other_pages(),
        }

    def get_annotated_comments(self, answer):
        comments = (
            Comment.objects.filter(
                content_type=ContentType.objects.get_for_model(Answer),
                object_id=answer.pk,
                parent__isnull=True
            )
            .select_related("author")
            .annotate(
                upvotes=Count("votes", filter=Q(votes__vote_type=1)),
                downvotes=Count("votes", filter=Q(votes__vote_type=-1)),
            )
            .order_by("-created_at")
        )
    
        def annotate_replies(comment):
            replies = (
                comment.replies.select_related("author")
                .annotate(
                    upvotes=Count("votes", filter=Q(votes__vote_type=1)),
                    downvotes=Count("votes", filter=Q(votes__vote_type=-1)),
                )
                .order_by("-created_at")
            )
            for reply in replies:
                reply.replies_cached = list(annotate_replies(reply))
            return replies
    
        for c in comments:
            c.replies_cached = list(annotate_replies(c))
    
        return comments


    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())

        self.object = self.get_object()
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.content_object = self.object
            comment.save()
            return redirect("answer_detail", answer_id=self.object.pk)

        context = self.get_context_data(comment_form=form)
        return self.render_to_response(context)
