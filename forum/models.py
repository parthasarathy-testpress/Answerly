from django.db import models
from django.contrib.auth.models import User
from taggit.managers import TaggableManager
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.db.models import Sum, Case, When, IntegerField


class TimeStampedModel(models.Model):
    """
    Abstract base model that provides common timestamp fields.
    """

    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time when the object was created.")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time when the object was last updated.")

    class Meta:
        abstract = True

class VoteCountMixin:
    def get_vote_counts(self):
        votes = self.votes.aggregate(
            upvotes=Sum(
                Case(
                    When(vote_type=1, then=1),
                    default=0,
                    output_field=IntegerField()
                )
            ),
            downvotes=Sum(
                Case(
                    When(vote_type=-1, then=1),
                    default=0,
                    output_field=IntegerField()
                )
            )
        )
        return {
            "upvotes": votes.get('upvotes') or 0,
            "downvotes": votes.get('downvotes') or 0,
        }

class Question(VoteCountMixin,TimeStampedModel):
    """
    Represents a question posted by a user in the Q&A platform.
    """

    title = models.CharField(
        max_length=255,
        help_text="Enter a concise title for your question (max 255 characters).",
    )
    description = models.TextField(
        help_text="Provide a detailed explanation of your question."
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="questions",
        help_text="Select the user who is posting this question.",
    )
    tags = TaggableManager(help_text="Add relevant tags to categorize and improve discoverability of your question.")
    votes = GenericRelation("Vote", related_query_name="questions", help_text="All votes (upvotes/downvotes) associated with this question.")

    def __str__(self):
        return self.title


class Answer(TimeStampedModel):
    """
    Represents an answer posted to a question.
    """

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="answers",
        help_text="The question this answer belongs to.",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="answers",
        help_text="Select the user who is posting this answer.",
    )
    content = models.TextField(help_text="Write your answer here.")
    votes = GenericRelation("Vote", related_query_name="answers", help_text="All votes (upvotes/downvotes) associated with this answer.")

    def __str__(self):
        return f"Answer by {self.author.username} to '{self.question.title}'"


class Comment(TimeStampedModel):
    """
    Represents a comment on a question, answer, or another comment.
    """

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text="The type of object this comment is attached to (Question, Answer, or Comment).",
    )
    object_id = models.PositiveIntegerField(
        help_text="The ID of the object this comment is attached to."
    )
    content_object = GenericForeignKey("content_type", "object_id")

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments",
        help_text="Select the user who is posting this comment.",
    )
    content = models.TextField(help_text="Write the content of your comment here.")
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="replies",
        help_text="If this is a reply, select the parent comment.",
    )
    votes = GenericRelation(
        "Vote",
        related_query_name="comments",
        help_text="All votes (upvotes/downvotes) associated with this comment.",
    )

    def __str__(self):
        return f"Comment by {self.author.username}"


class Vote(TimeStampedModel):
    """
    Represents a vote (upvote or downvote) on a question, answer, or comment.
    """

    class VoteType(models.IntegerChoices):
        UPVOTE = 1, "Upvote"
        DOWNVOTE = -1, "Downvote"

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, help_text="Select the user who is casting this vote."
    )

    vote_type = models.SmallIntegerField(
        choices=VoteType.choices, help_text="Choose 'Upvote' for +1 or 'Downvote' for -1."
    )

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text="The type of object being voted on (Question, Answer, or Comment).",
    )
    object_id = models.PositiveIntegerField(help_text="The ID of the object being voted on.")
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        unique_together = ("user", "content_type", "object_id")

    def __str__(self):
        return f"{self.get_vote_type_display()} by {self.user.username}"
