from django.urls import path
from .views import QuestionListView,QuestionCreateView

urlpatterns = [
    path('', QuestionListView.as_view(), name='question_list'),
    path('post/', QuestionCreateView.as_view(), name='question_post'),
]
