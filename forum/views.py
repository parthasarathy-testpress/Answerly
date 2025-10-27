from django.shortcuts import get_object_or_404
from django.views.generic import ListView,CreateView,UpdateView,DeleteView,DetailView
from django.db.models import Sum,Count,Q
from .models import Question, Vote,Answer,Comment
from django.contrib.auth.mixins import LoginRequiredMixin,UserPassesTestMixin
from django.urls import reverse_lazy
from .forms import QuestionForm,AnswerForm
from django.core.paginator import Paginator
from django.contrib.contenttypes.models import ContentType

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
    
class AuthorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        obj = self.get_object()
        return self.request.user == obj.author
    
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
    paginate_answers_by = 3

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        question = self.get_object()
        context.update(self.get_question_vote_context(question))
        context.update(self.get_paginated_answers_context(question))
        return context

    def get_question_vote_context(self, question):
        vote_counts = question.get_vote_counts()
        return {
            "question_upvotes": vote_counts["upvotes"],
            "question_downvotes": vote_counts["downvotes"],
        }
        
    def get_paginated_answers_context(self, question):
        answers_qs = self.get_annotated_answers(question)
        paginator = Paginator(answers_qs, self.paginate_answers_by)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return {
            "answers": page_obj,
            "paginator": paginator,
            "page_obj": page_obj,
            "is_paginated": page_obj.has_other_pages(),
        }

    def get_annotated_answers(self, question):
        return (
            question.answers.annotate(
                upvotes=Count('votes', filter=Q(votes__vote_type=1)),
                downvotes=Count('votes', filter=Q(votes__vote_type=-1))
            )
            .order_by('-created_at')
        )
    
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
        return (
            Comment.objects.filter(
                content_type=ContentType.objects.get_for_model(Answer), object_id=answer.pk
            )
            .annotate(
                upvotes=Count("votes", filter=Q(votes__vote_type=1)),
                downvotes=Count("votes", filter=Q(votes__vote_type=-1)),
            )
            .order_by("-created_at")
        )
