from django.shortcuts import get_object_or_404, redirect
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from ..models import Question, Answer
from ..forms import AnswerForm, CommentForm
from .mixins import AuthorRequiredMixin,AnswerMetaMixin,AnswerNavigationMixin,AnswerDetailMixin

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


class AnswerUpdateView(LoginRequiredMixin, AuthorRequiredMixin,AnswerNavigationMixin,AnswerMetaMixin, UpdateView):
    model = Answer
    form_class = AnswerForm
    template_name = "forum/answer_update_form.html"
    pk_url_kwarg = 'answer_id'


class AnswerDeleteView(LoginRequiredMixin, AuthorRequiredMixin,AnswerNavigationMixin,AnswerMetaMixin, DeleteView):
    model = Answer
    template_name = "forum/answer_confirm_delete.html"
    pk_url_kwarg = 'answer_id'


class AnswerDetailView(AnswerDetailMixin, DetailView):
    model = Answer
    template_name = "forum/answer_detail.html"
    pk_url_kwarg = 'answer_id'
    context_object_name = 'answer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        answer = self.object
        context.update(self.get_answer_vote_context(answer))
        context.update(self.get_paginated_comments_context(answer))
        context["question"] = answer.question
        context["comment_form"] = kwargs.get("comment_form", CommentForm())
        return context

    def post(self, request, *args, **kwargs):
        # For posting comments
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
