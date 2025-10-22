from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from .models import Question, Answer, Comment, Vote

class VoteInline(GenericTabularInline):
    model = Vote
    extra = 0
    readonly_fields = ("user", "vote_type", "created_at")

class CommentInline(GenericTabularInline):
    model = Comment
    extra = 0
    fields = ("author", "content", "parent", "created_at")
    readonly_fields = ("created_at",)

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    fields = ("author", "content", "created_at")
    readonly_fields = ("created_at",)

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "created_at")
    inlines = [AnswerInline, VoteInline]

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("question", "author", "created_at")
    inlines = [CommentInline, VoteInline]

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("content_object", "author", "parent", "created_at")
    inlines = [CommentInline,VoteInline]

@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ("content_object", "user", "vote_type", "created_at")
