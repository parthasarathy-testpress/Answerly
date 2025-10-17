from django.views.generic import ListView
from django.db.models import Sum
from .models import Question, Vote

class QuestionListView(ListView):
    model = Question
    template_name = 'qa/question_list.html'
    context_object_name = 'questions'
    paginate_by = 10

    def get_queryset(self):
        return Question.objects.annotate(
            total_votes=Sum('votes__vote_type', default=0)
        ).order_by('-created_at')
