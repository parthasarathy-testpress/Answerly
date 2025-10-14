from django.db import models
from django.contrib.auth.models import User
from taggit.managers import TaggableManager
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation


class BaseModel(models.Model):
    """
    Abstract base model that provides common timestamp fields.

    Fields:
        created_at (DateTimeField): Timestamp when the object was created.
        updated_at (DateTimeField): Timestamp when the object was last updated.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Question(BaseModel):
    """
    Represents a question posted by a user in the Q&A platform.

    Fields:
        title (CharField): The title of the question.
        description (TextField): Detailed description of the question.
        author (ForeignKey): The user who posted the question.
        tags (TaggableManager): Tags associated with the question.
        votes (GenericRelation): Votes associated with the question.
    """

    title = models.CharField(
        max_length=255,
        help_text="Enter the title of the question (max 255 characters).",
    )
    description = models.TextField(
        help_text="Provide a detailed description of your question."
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="questions",
        help_text="The user who is posting this question.",
    )
    tags = TaggableManager(help_text="Add tags to categorize your question.")
    votes = GenericRelation("Vote", related_query_name="questions")

    def __str__(self):
        """
        Return a human-readable representation of the question.
        """
        return self.title


class Answer(BaseModel):
    """
    Represents an answer posted to a question.

    Fields:
        question (ForeignKey): The question this answer belongs to.
        author (ForeignKey): User who posted the answer.
        content (TextField): The text content of the answer.
        votes (GenericRelation): Votes associated with this answer.
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
        help_text="The user who posted this answer.",
    )
    content = models.TextField(help_text="Write the content of your answer here.")
    votes = GenericRelation("Vote", related_query_name="answers")

    def __str__(self):
        """
        Return a human-readable representation of the answer.
        """
        return f"Answer by {self.author.username} to '{self.question.title}'"


class Comment(BaseModel):
    """
    Represents a comment on a question, answer, or another comment.

    Fields:
        content_type (ForeignKey): The type of object this comment is attached to.
        object_id (PositiveIntegerField): The ID of the object this comment is attached to.
        content_object (GenericForeignKey): Generic relation to the object being commented on.
        author (ForeignKey): User who posted the comment.
        content (TextField): The text content of the comment.
        parent (ForeignKey): Optional parent comment for threaded replies.
        votes (GenericRelation): Votes associated with this comment.
    """

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text="The type of object this comment is attached to.",
    )
    object_id = models.PositiveIntegerField(
        help_text="The ID of the object this comment is attached to."
    )
    content_object = GenericForeignKey("content_type", "object_id")

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments",
        help_text="The user who posted this comment.",
    )
    content = models.TextField(help_text="Write the content of your comment here.")
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="replies",
        help_text="Parent comment if this is a reply.",
    )
    votes = GenericRelation(
        "Vote",
        related_query_name="comments",
        help_text="Votes associated with this comment.",
    )

    def __str__(self):
        """
        Return a human-readable representation of the comment.
        """
        return f"Comment by {self.author.username}"


class Vote(BaseModel):
    """
    Represents a vote (upvote or downvote) on a question, answer, or comment.

    Fields:
        user (ForeignKey): User who cast the vote.
        vote_type (SmallIntegerField): Type of vote (1 for upvote, -1 for downvote).
        content_type (ForeignKey): Type of object being voted on.
        object_id (PositiveIntegerField): ID of the object being voted on.
        content_object (GenericForeignKey): Generic relation to the object being voted on.

    Constraints:
        unique_together: Ensures a user can vote only once per object.
    """

    class VoteType(models.IntegerChoices):
        UPVOTE = 1, "Upvote"
        DOWNVOTE = -1, "Downvote"

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, help_text="The user who cast this vote."
    )

    vote_type = models.SmallIntegerField(
        choices=VoteType.choices, help_text="Select 1 for Upvote or -1 for Downvote."
    )

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text="The type of object being voted on.",
    )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        unique_together = ("user", "content_type", "object_id")

    def __str__(self):
        """
        Return a human-readable representation of the vote.
        """
        return f"{self.get_vote_type_display()} by {self.user.username}"
