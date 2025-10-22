from django.urls import path
from .views import QuestionListView,QuestionCreateView,QuestionUpdateView

urlpatterns = [
    path('', QuestionListView.as_view(), name='question_list'),
    path('post/', QuestionCreateView.as_view(), name='question_post'),
    path('question/<int:question_id>/edit/', QuestionUpdateView.as_view(), name='question_edit'),
]
