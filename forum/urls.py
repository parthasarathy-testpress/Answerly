from django.urls import path
from forum.views import QuestionListView,QuestionCreateView,\
    QuestionUpdateView,QuestionDeleteView,QuestionDetailView,\
    AnswerCreateView,AnswerUpdateView,AnswerDeleteView,AnswerDetailView,\
    CommentUpdateView,CommentDeleteView
from forum.views.vote_views import QuestionVoteView, AnswerVoteView, CommentVoteView

urlpatterns = [
    path('', QuestionListView.as_view(), name='question_list'),
    path('post/', QuestionCreateView.as_view(), name='question_post'),
    path('question/<int:question_id>/edit/', QuestionUpdateView.as_view(), name='question_edit'),
    path('question/<int:question_id>/delete/', QuestionDeleteView.as_view(), name='question_delete'),
    path('question/<int:question_id>/answer/', AnswerCreateView.as_view(), name='answer_post'),
    path('question/<int:question_id>/', QuestionDetailView.as_view(), name='question_detail'),
    path('answer/<int:answer_id>/edit/', AnswerUpdateView.as_view(), name='answer_update'),
    path('answer/<int:answer_id>/delete/', AnswerDeleteView.as_view(), name='answer_delete'),
    path('answers/<int:answer_id>/', AnswerDetailView.as_view(), name='answer_detail'),
    path('comment/<int:comment_id>/edit/', CommentUpdateView.as_view(), name='comment_update'),
    path('comment/<int:comment_id>/delete/', CommentDeleteView.as_view(), name='comment_delete'),

    path('question/<int:question_id>/vote/', QuestionVoteView.as_view(), name='question_vote'),
    path('answer/<int:answer_id>/vote/', AnswerVoteView.as_view(), name='answer_vote'),
    path('comment/<int:comment_id>/vote/', CommentVoteView.as_view(), name='comment_vote'),
]
