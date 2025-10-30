from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView,CreateView,UpdateView,DeleteView,DetailView
from django.db.models import Sum,Count,Q
from .models import Question, Vote,Answer,Comment
from django.contrib.auth.mixins import LoginRequiredMixin,UserPassesTestMixin
from django.urls import reverse_lazy
from .forms import QuestionForm,AnswerForm,CommentForm
from django.core.paginator import Paginator
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.views import redirect_to_login
from django.utils.decorators import method_decorator
from django.views import View
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from taggit.models import Tag

class QuestionListView(ListView):
    model = Question
    template_name = 'forum/question_list.html'
    context_object_name = 'questions'
    paginate_by = 10

    def get_queryset(self):
        queryset = Question.objects.all()
        search_query = self.request.GET.get('question')
        tag_filter = self.request.GET.get('tag')
        
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query)
            )
            
        if tag_filter:
            queryset = queryset.filter(tags__name__iexact=tag_filter)

        queryset = queryset.annotate(
            total_votes=Sum('votes__vote_type', default=0)
        ).order_by('-created_at')
        
        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tags'] = Tag.objects.all().order_by('name')
        context['search_query'] = self.request.GET.get('question', '')
        context['selected_tag'] = self.request.GET.get('tag', '')
        return context

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

        if self.request.user.is_authenticated:
            try:
                q_ct = ContentType.objects.get_for_model(Question)
                qvote = Vote.objects.get(user=self.request.user, content_type=q_ct, object_id=question.pk)
                context['question_user_vote'] = qvote.vote_type
            except Vote.DoesNotExist:
                context['question_user_vote'] = 0
        else:
            context['question_user_vote'] = 0
        return context

    def get_question_vote_context(self, question):
        vote_counts = question.get_vote_counts()
        return {
            "question_upvotes": vote_counts["upvotes"],
            "question_downvotes": vote_counts["downvotes"],
        }
        
    def get_paginated_answers_context(self, question):
        answers_qs = self.get_annotated_answers(question)
        if self.request.user.is_authenticated:
            answer_ids = [a.pk for a in answers_qs]
            if answer_ids:
                answer_ct = ContentType.objects.get_for_model(Answer)
                votes = Vote.objects.filter(user=self.request.user, content_type=answer_ct, object_id__in=answer_ids)
                votes_map = {v.object_id: v.vote_type for v in votes}
            else:
                votes_map = {}
            for a in answers_qs:
                a.user_vote = votes_map.get(a.pk, 0)
        else:
            for a in answers_qs:
                a.user_vote = 0

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
            context["comment_form"] = kwargs.get("comment_form", CommentForm())

            if self.request.user.is_authenticated:
                try:
                    a_ct = ContentType.objects.get_for_model(Answer)
                    avote = Vote.objects.get(user=self.request.user, content_type=a_ct, object_id=answer.pk)
                    context['answer_user_vote'] = avote.vote_type
                except Vote.DoesNotExist:
                    context['answer_user_vote'] = 0
            else:
                context['answer_user_vote'] = 0

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

        if hasattr(self, 'request') and self.request.user.is_authenticated:
            # collect all comment ids
            def collect_ids(comment):
                ids = [comment.pk]
                for r in getattr(comment, 'replies_cached', []):
                    ids.extend(collect_ids(r))
                return ids

            all_ids = []
            for c in comments:
                all_ids.extend(collect_ids(c))

            if all_ids:
                comment_ct = ContentType.objects.get_for_model(Comment)
                votes = Vote.objects.filter(user=self.request.user, content_type=comment_ct, object_id__in=all_ids)
                votes_map = {v.object_id: v.vote_type for v in votes}
            else:
                votes_map = {}

            def assign_votes(comment):
                comment.user_vote = votes_map.get(comment.pk, 0)
                for r in getattr(comment, 'replies_cached', []):
                    assign_votes(r)

            for c in comments:
                assign_votes(c)
        else:
            for c in comments:
                def set_zero(comment):
                    comment.user_vote = 0
                    for r in getattr(comment, 'replies_cached', []):
                        set_zero(r)
                set_zero(c)
    
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


class CommentUpdateView(LoginRequiredMixin, AuthorRequiredMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = "forum/comment_update_form.html"
    pk_url_kwarg = 'comment_id'
    _success_url = None

    def get_success_url(self):
        if self._success_url is None:
            root = self.object
            while root.parent is not None:
                root = root.parent
            answer = root.content_object
            self._success_url = reverse_lazy('answer_detail', kwargs={'answer_id': answer.pk})
        return self._success_url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = self.get_success_url()
        return context

class CommentDeleteView(LoginRequiredMixin, AuthorRequiredMixin, DeleteView):
    model = Comment
    template_name = "forum/comment_confirm_delete.html"
    pk_url_kwarg = 'comment_id'
    _success_url = None

    def get_success_url(self):
        if self._success_url is None:
            root = self.object
            while root.parent is not None:
                root = root.parent
            answer = root.content_object
            self._success_url = reverse_lazy('answer_detail', kwargs={'answer_id': answer.pk})
        return self._success_url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = self.get_success_url()
        return context

@method_decorator(login_required, name='dispatch')
class VoteView(View):
    model_map = {
        "question": Question,
        "answer": Answer,
        "comment": Comment,
    }

    def post(self, request, *args, **kwargs):
        model = request.POST.get("model")
        obj_id = request.POST.get("id")
        vtype = request.POST.get("type")

        if not (model and obj_id and vtype):
            return HttpResponseBadRequest("Missing parameters")

        try:
            vote_type = self.validate_vote_type(vtype)
        except ValueError as e:
            return HttpResponseBadRequest(str(e))

        try:
            obj, ct = self.get_object_and_contenttype(model, obj_id)
        except ValueError as e:
            return HttpResponseBadRequest(str(e))

        action = self.process_vote(request.user, obj, ct, vote_type)

        upvotes, downvotes = self.get_vote_counts(obj)
        current_vote = self.get_current_vote(request.user, ct, obj)

        return JsonResponse({
            "upvotes": upvotes,
            "downvotes": downvotes,
            "action": action,
            "current_vote": current_vote,
        })

    def validate_vote_type(self, vtype):
        try:
            vote_type = int(vtype)
        except ValueError:
            raise ValueError(f"Invalid vote type: {vtype}")
        if vote_type not in (1, -1):
            raise ValueError(f"Invalid vote type: {vote_type}. Vote type must be 1 or -1.")
        return vote_type

    def get_object_and_contenttype(self, model_name, obj_id):
        ModelClass = self.model_map.get(model_name.lower())
        if ModelClass is None:
            raise ValueError(f"Invalid model name: {model_name}")

        obj = get_object_or_404(ModelClass, pk=obj_id)
        ct = ContentType.objects.get_for_model(ModelClass)
        return obj, ct

    def process_vote(self, user, obj, ct, vote_type):

        try:
            vote = Vote.objects.get(user=user, content_type=ct, object_id=obj.pk)
        except Vote.DoesNotExist:
            vote = None

        if vote is None:
            Vote.objects.create(user=user, content_object=obj, vote_type=vote_type)
            return "created"
        elif vote.vote_type == vote_type:
            vote.delete()
            return "deleted"
        else:
            vote.vote_type = vote_type
            vote.save()
            return "updated"

    def get_vote_counts(self, obj):
        upvotes = obj.votes.filter(vote_type=1).count()
        downvotes = obj.votes.filter(vote_type=-1).count()
        return upvotes, downvotes

    def get_current_vote(self, user, ct, obj):
        try:
            current = Vote.objects.get(user=user, content_type=ct, object_id=obj.pk)
            return current.vote_type
        except Vote.DoesNotExist:
            return 0
