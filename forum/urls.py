from django.urls import path
from .views import QuestionListView,QuestionCreateView,\
    QuestionUpdateView,QuestionDeleteView,QuestionDetailView,\
    AnswerCreateView,AnswerUpdateView,AnswerDeleteView

urlpatterns = [
    path('', QuestionListView.as_view(), name='question_list'),
    path('post/', QuestionCreateView.as_view(), name='question_post'),
    path('question/<int:question_id>/edit/', QuestionUpdateView.as_view(), name='question_edit'),
    path('question/<int:question_id>/delete/', QuestionDeleteView.as_view(), name='question_delete'),
    path('question/<int:question_id>/answer/', AnswerCreateView.as_view(), name='answer_post'),
    path('question/<int:question_id>/', QuestionDetailView.as_view(), name='question_detail'),
    path('answer/<int:answer_id>/edit/', AnswerUpdateView.as_view(), name='answer_update'),
    path('answer/<int:answer_id>/delete/', AnswerDeleteView.as_view(), name='answer_delete'),
]
