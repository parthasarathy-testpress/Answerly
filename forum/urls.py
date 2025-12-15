from django.urls import path
from .views import QuestionListView,QuestionCreateView,\
    QuestionUpdateView,QuestionDeleteView,QuestionDetailView,\
    AnswerCreateView,AnswerUpdateView,AnswerDeleteView,AnswerDetailView,\
    CommentUpdateView,CommentDeleteView,AnswerListPartialView,AnswerCommentsPartialView

urlpatterns = [
    path('', QuestionListView.as_view(), name='question_list'),
    path('post/', QuestionCreateView.as_view(), name='question_post'),
    path('question/<int:question_id>/edit/', QuestionUpdateView.as_view(), name='question_edit'),
    path('question/<int:question_id>/delete/', QuestionDeleteView.as_view(), name='question_delete'),
    path('question/<int:question_id>/answer/', AnswerCreateView.as_view(), name='answer_post'),
    path("questions/<int:question_id>/answers/",AnswerListPartialView.as_view(),name='answer-list-partial'),
    path('question/<int:question_id>/', QuestionDetailView.as_view(), name='question_detail'),
    path('answer/<int:answer_id>/edit/', AnswerUpdateView.as_view(), name='answer_update'),
    path('answer/<int:answer_id>/delete/', AnswerDeleteView.as_view(), name='answer_delete'),
    path('answers/<int:answer_id>/', AnswerDetailView.as_view(), name='answer_detail'),
    path('answers/<int:answer_id>/comments/', AnswerCommentsPartialView.as_view(), name='answer-comments-partial'),
    path('comment/<int:comment_id>/edit/', CommentUpdateView.as_view(), name='comment_update'),
    path('comment/<int:comment_id>/delete/', CommentDeleteView.as_view(), name='comment_delete'),
]
