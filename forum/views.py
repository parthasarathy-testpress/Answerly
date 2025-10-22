from django.views.generic import ListView,CreateView,UpdateView
from django.db.models import Sum
from .models import Question, Vote
from django.contrib.auth.mixins import LoginRequiredMixin,UserPassesTestMixin
from django.urls import reverse_lazy
from .forms import QuestionForm
from taggit.models import Tag

class QuestionListView(ListView):
    model = Question
    template_name = 'forum/question_list.html'
    context_object_name = 'questions'
    paginate_by = 10

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

class QuestionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Question
    form_class = QuestionForm
    template_name = 'forum/question_edit.html'

    def get_success_url(self):
        return reverse_lazy('question_list')

    def test_func(self):
        question = self.get_object()
        return self.request.user == question.author
