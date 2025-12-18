from django.views.generic import CreateView, UpdateView, DeleteView, DetailView
from django.db.models import Sum, Count, Q
from django.urls import reverse_lazy
from django.core.paginator import Paginator
import json

from forum.models import Question
from forum.forms import QuestionForm
from forum.views.mixins import AuthorRequiredMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django_filters.views import FilterView
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
            total_votes=Sum('votes__vote_type', default=0),
            upvotes=Count('votes', filter=Q(votes__vote_type=1)),
            downvotes=Count('votes', filter=Q(votes__vote_type=-1)),
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tags_json'] = self.get_tags_as_json()
        context['selected_tag_ids'] = self.get_selected_tag_ids_as_json()
        return context

    def get_tags_as_json(self):
        tags_queryset = Tag.objects.all().order_by('name')
        tags_data = [{'id': tag.id, 'name': tag.name} for tag in tags_queryset]
        return json.dumps(tags_data)

    def get_selected_tag_ids_as_json(self):
        selected_tag_ids = [
            int(tag_id)
            for tag_id in self.request.GET.getlist('tag')
            if tag_id.isdigit()
        ]
        return json.dumps(selected_tag_ids)


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


class QuestionDetailView(DetailView):
    model = Question
    template_name = "forum/question_detail.html"
    context_object_name = "question"
    pk_url_kwarg = 'question_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        question = self.get_object()
        context.update(self.get_question_vote_context(question))
        return context

    def get_question_vote_context(self, question):
        vote_counts = question.get_vote_counts()
        user = self.request.user
        user_vote = question.get_user_voted_type(user) if user.is_authenticated else 0
        return {
            "question_upvotes": vote_counts["upvotes"],
            "question_downvotes": vote_counts["downvotes"],
            "question_user_vote": user_vote,
        }
