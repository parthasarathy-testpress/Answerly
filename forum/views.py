from django.views.generic import ListView
from django.db.models import Count, Q
from .models import Question, Vote

class QuestionListView(ListView):
    model = Question
    template_name = 'questions/question_list.html'
    context_object_name = 'questions'
    ordering = ['-created_at']
    paginate_by = 10

    def get_queryset(self):
        return Question.objects.annotate(
            total_votes=Count('votes', filter=Q(votes__vote_type=1)) - Count('votes', filter=Q(votes__vote_type=-1))
        ).order_by('-created_at')
