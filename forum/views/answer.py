from django.shortcuts import get_object_or_404, redirect
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.db.models import Count, Q
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django_filters.views import FilterView

from forum.models import Answer, Question,Vote
from forum.forms import AnswerForm, CommentForm
from forum.views.mixins import AuthorRequiredMixin
from forum.filters import AnswerFilter
from django.contrib.contenttypes.models import ContentType

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
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        answer = self.object
        context.update(self.get_answer_vote_context(answer))
        context["question"] = answer.question
        return context

    def get_answer_vote_context(self, answer):
        vote_counts = answer.get_vote_counts()
        user = self.request.user
        user_vote = answer.get_user_voted_type(user) if user.is_authenticated else 0
        return {
            "answer_upvotes": vote_counts["upvotes"],
            "answer_downvotes": vote_counts["downvotes"],
            "answer_user_vote": user_vote,
        }


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

class AnswerListPartialView(FilterView):
    model = Answer
    template_name = "forum/partials/answer_list.html"
    context_object_name = "answers"
    paginate_by = 3
    filterset_class = AnswerFilter

    def get_queryset(self):
        self.question = get_object_or_404(
            Question,
            pk=self.kwargs["question_id"]
        )
        return (
            self.question.answers.select_related("author")
            .annotate(
                upvotes=Count("votes", filter=Q(votes__vote_type=1)),
                downvotes=Count("votes", filter=Q(votes__vote_type=-1)),
            )
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["htmx_target"] = "#answer-list"
        base_url = self.request.path
        
        # Build URL with current query parameters for pagination (excluding page)
        query_params = self.request.GET.copy()
        if 'page' in query_params:
            del query_params['page']
        query_string = query_params.urlencode()
        
        context["partial_url"] = f"{base_url}?{query_string}" if query_string else base_url
        context["base_url"] = base_url
        context["filter_query_string"] = query_string
        
        return context

