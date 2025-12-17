from forum.views.question import (
    QuestionListView,
    QuestionCreateView,
    QuestionUpdateView,
    QuestionDeleteView,
    QuestionDetailView,
)

from forum.views.answer import (
    AnswerCreateView,
    AnswerUpdateView,
    AnswerDeleteView,
    AnswerDetailView,
    AnswerListPartialView,
)

from forum.views.comment import (
    CommentUpdateView,
    CommentDeleteView,
    CommentsPartialListView,
)

from forum.views.vote import QuestionVoteView,AnswerVoteView,CommentVoteView
