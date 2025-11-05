from django.views.generic import CreateView, UpdateView, DeleteView, DetailView
from django_filters.views import FilterView
from django.db.models import Sum
from django.urls import reverse_lazy
from ..models import Question
from ..forms import QuestionForm
from django.contrib.auth.mixins import LoginRequiredMixin
from .mixins import AuthorRequiredMixin,QuestionDetailMixin
from ..filters import QuestionFilter

from taggit.models import Tag

class QuestionListView(FilterView):
    model = Question
    template_name = 'forum/question_list.html'
    context_object_name = 'questions'
    paginate_by = 10
    filterset_class = QuestionFilter

    def get_queryset(self):
        return Question.objects.annotate(
            total_votes=Sum('votes__vote_type', default=0)
        ).order_by('-created_at')


class QuestionCreateView(LoginRequiredMixin, CreateView):
    model = Question
    form_class = QuestionForm
    template_name = 'forum/question_form.html'
    success_url = reverse_lazy('question_list')
    login_url = reverse_lazy('login')

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class QuestionUpdateView(LoginRequiredMixin, AuthorRequiredMixin, UpdateView):
    model = Question
    form_class = QuestionForm
    template_name = 'forum/question_edit.html'
    pk_url_kwarg = 'question_id'
    success_url = reverse_lazy('question_list')


class QuestionDeleteView(LoginRequiredMixin, AuthorRequiredMixin, DeleteView):
    model = Question
    template_name = 'forum/question_confirm_delete.html'
    context_object_name = 'question'
    pk_url_kwarg = 'question_id'
    success_url = reverse_lazy('question_list')


class QuestionDetailView(QuestionDetailMixin, DetailView):
    model = Question
    template_name = "forum/question_detail.html"
    context_object_name = "question"
    pk_url_kwarg = 'question_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        question = self.object
        context.update(self.get_question_vote_context(question))
        context.update(self.get_paginated_answers_context(question))
        return context
