from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from forum.models import Question,Vote,Answer,Comment
from django.contrib.contenttypes.models import ContentType
from forum.forms import CommentForm
from django.utils import timezone
from taggit.models import Tag

User = get_user_model()

class TestQuestionListView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='pass123')
        self.user2 = User.objects.create_user(username='otheruser', email='test1@example.com', password='pass123')

        for i in range(15):
            Question.objects.create(
                title=f'Question {i}',
                description='Test description',
                author=self.user
            )

        question1 = Question.objects.latest('created_at')
        question1.votes.create(user=self.user, vote_type=1)
        question1.votes.create(user=self.user2, vote_type=-1)

    def test_should_render_question_list_and_return_status_200(self):
        response = self.client.get(reverse('question_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'forum/question_list.html')

    def test_should_include_questions_with_total_votes_in_context(self):
        response = self.client.get(reverse('question_list'))
        self.assertIn('questions', response.context)
        first_question = response.context['questions'][0]
        self.assertTrue(hasattr(first_question, 'total_votes'))
        self.assertEqual(first_question.total_votes, 0)

    def test_should_paginate_questions(self):
        response = self.client.get(reverse('question_list'))
        self.assertEqual(len(response.context['questions']), 10)

        response_page2 = self.client.get(reverse('question_list') + '?page=2')
        self.assertEqual(len(response_page2.context['questions']), 5)

class TestQuestionCreateView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='pass123')
        self.url = reverse('question_post')

    def test_should_redirect_anonymous_to_login_for_question_create(self):
        response = self.client.get(self.url)
        expected_url = reverse('login') + '?next=' + self.url
        self.assertRedirects(response, expected_url)

    def test_should_display_question_create_form(self):
        self.client.login(username='testuser', password='pass123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<form')

    def test_should_create_question_and_assign_tags(self):
        self.client.login(username='testuser', password='pass123')
        data = {
            'title': 'New Question',
            'description': 'Question description',
            'tags': 'django, python'
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(response, reverse('question_list'))
        question = Question.objects.get(title='New Question')
        self.assertEqual(question.author, self.user)
        tag_names = [tag.name for tag in question.tags.all()]
        self.assertIn('django', tag_names)
        self.assertIn('python', tag_names)


class TestQuestionUpdateView(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(username='author', email='test@example.com', password='pass1234')
        self.other_user = User.objects.create_user(username='other', email='test1@example.com', password='pass1234')

        self.question = Question.objects.create(
            title='Original Title',
            description='Original description',
            author=self.author
        )
        self.question.tags.add('django', 'python')

        self.url = reverse('question_edit', kwargs={'question_id': self.question.pk})

    def test_should_redirect_anonymous_to_login_for_question_update(self):
        response = self.client.get(self.url)
        expected_url = reverse('login') + '?next=' + self.url
        self.assertRedirects(response, expected_url)

    def test_should_forbid_non_author_from_editing_question(self):
        self.client.login(username='other', password='pass1234')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_should_allow_author_to_access_update_view(self):
        self.client.login(username='author', password='pass1234')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Original Title')

class TestQuestionDeleteView(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(username='author', email='test@example.com', password='pass1234')
        self.other_user = User.objects.create_user(username='other', email='test1@example.com', password='pass1234')

        self.question = Question.objects.create(
            title='Original Title',
            description='Original description',
            author=self.author
        )
        
        self.url = reverse('question_delete', args=[self.question.pk])

    def test_should_allow_author_to_delete_question(self):
        self.client.login(username='author', password='pass1234')
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse('question_list'))
        self.assertFalse(Question.objects.filter(id=self.question.pk).exists())

    def test_should_forbid_non_author_from_deleting_question(self):
        self.client.login(username='other', password='pass1234')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Question.objects.filter(id=self.question.pk).exists())

    def test_should_redirect_anonymous_to_login_for_question_delete(self):
        response = self.client.post(self.url)
        login_url = reverse('login')
        self.assertRedirects(response, f'{login_url}?next={self.url}')
        self.assertTrue(Question.objects.filter(id=self.question.pk).exists())
    
    def test_should_show_delete_confirmation_page_to_author(self):
        self.client.login(username='author', password='pass1234')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'forum/question_confirm_delete.html')
        self.assertContains(response, 'Are you sure you want to delete this question?')

class TestQuestionDetailView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username="user1", email='test@example.com', password="pass123")
        self.user2 = User.objects.create_user(username="user2", email='test1@example.com', password="pass123")
        self.question = Question.objects.create(
            title="Test Question",
            description="Test Description",
            author=self.user1
        )
        self.detail_url = reverse("question_detail", kwargs={"question_id": self.question.pk})
        
    def test_should_render_question_detail_and_return_200(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.question.title)
        self.assertContains(response, self.question.description)

    def test_should_include_vote_counts_in_question_context(self):
        Vote.objects.create(user=self.user1, content_object=self.question, vote_type=1)
        Vote.objects.create(user=self.user2, content_object=self.question, vote_type=-1)
        
        response = self.client.get(self.detail_url)
        self.assertEqual(response.context["question_upvotes"], 1)
        self.assertEqual(response.context["question_downvotes"], 1)
        
class TestAnswerPartialListView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="user1", email='test@example.com', password="pass123")
        self.question = Question.objects.create(
            title="Question for Pagination Test",
            description="Testing answers pagination",
            author=self.user
        )
        
        for i in range(7):
            Answer.objects.create(
                question=self.question,
                author=self.user,
                content=f"Answer {i+1}"
            )

        self.url = reverse(
            "answer-list-partial",
            kwargs={"question_id": self.question.pk},
        )

    def test_should_return_first_page_of_answers(self):
        response = self.client.get(self.url)
        answers = response.context["answers"]
        self.assertEqual(len(answers), 3)
        self.assertTrue(response.context["is_paginated"])
        self.assertEqual(response.context["page_obj"].number, 1)

    def test_should_return_second_page_of_answers(self):
        response = self.client.get(f"{self.url}?page=2")
        answers = response.context["answers"]
        self.assertEqual(len(answers), 3)
        self.assertTrue(response.context["is_paginated"])
        self.assertEqual(response.context["page_obj"].number, 2)

    def test_should_return_third_page_of_answers(self):
        response = self.client.get(f"{self.url}?page=3")
        answers = response.context["answers"]
        self.assertEqual(len(answers), 1)
        self.assertTrue(response.context["is_paginated"])
        self.assertEqual(response.context["page_obj"].number, 3)

    def test_should_return_404_for_invalid_answer_page(self):
        response = self.client.get(f"{self.url}?page=999")
        self.assertEqual(response.status_code, 404)

    def test_should_return_answers_partial_for_htmx(self):
        response = self.client.get(
            self.url,
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "forum/partials/answer_list.html",
        )

class TestAnswerCreateView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", email='test@example.com', password="pass123")
        self.other_user = User.objects.create_user(username="otheruser", email='test1@example.com', password="pass123")
        self.question = Question.objects.create(
            title="Test Question",
            description="Test Description",
            author=self.user
        )
        self.url = reverse("answer_post", kwargs={"question_id": self.question.pk})

    def test_should_redirect_anonymous_to_login_for_answer_create(self):
        response = self.client.get(self.url)
        login_url = reverse("login") + f"?next={self.url}"
        self.assertRedirects(response, login_url)

    def test_should_display_answer_form_to_logged_in_user(self):
        self.client.login(username="testuser", password="pass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "forum/answer_form.html")

    def test_should_create_answer_on_valid_post(self):
        self.client.login(username="testuser", password="pass123")
        data = {"content": "This is a test answer"}
        response = self.client.post(self.url, data)
        self.assertEqual(Answer.objects.count(), 1)
        answer = Answer.objects.first()
        self.assertEqual(answer.content, "This is a test answer")
        self.assertEqual(answer.author, self.user)
        self.assertEqual(answer.question, self.question)
        expected_url = reverse("question_detail", kwargs={"question_id": self.question.pk})
        self.assertRedirects(response, expected_url)

    def test_should_show_errors_on_invalid_answer_post(self):
        self.client.login(username="testuser", password="pass123")
        data = {"content": ""}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")
        self.assertEqual(Answer.objects.count(), 0)

    def test_should_include_question_in_answer_view_context(self):
        self.client.login(username="testuser", password="pass123")
        response = self.client.get(self.url)
        self.assertEqual(response.context["question"], self.question)

class TestAnswerUpdateView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username="user1", email='test@example.com', password="pass123")
        self.user2 = User.objects.create_user(username="user2", email='test1@example.com', password="pass123")
        self.question = Question.objects.create(
            title="Test Question",
            description="Test Description",
            author=self.user1
        )
        self.answer = Answer.objects.create(
            question=self.question,
            author=self.user1,
            content="Original Answer"
        )
        self.update_url = reverse("answer_update", kwargs={"answer_id": self.answer.pk})

    def test_should_redirect_anonymous_to_login_for_answer_update(self):
        response = self.client.get(self.update_url)
        expected_url = f"{reverse('login')}?next={self.update_url}"
        self.assertRedirects(response, expected_url)

    def test_should_forbid_non_author_from_updating_answer(self):
        self.client.login(username="user2", password="pass123")
        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 403)

    def test_should_allow_author_to_view_answer_update_form(self):
        self.client.login(username="user1", password="pass123")
        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Original Answer")
        self.assertTemplateUsed(response, "forum/answer_update_form.html")

    def test_should_update_answer_on_valid_post(self):
        self.client.login(username="user1", password="pass123")
        response = self.client.post(self.update_url, {"content": "Updated Answer"})
        self.answer.refresh_from_db()
        self.assertEqual(self.answer.content, "Updated Answer")
        expected_url = reverse("question_detail", kwargs={"question_id": self.question.pk})
        self.assertRedirects(response, expected_url)

    def test_should_include_answer_in_update_view_context(self):
        self.client.login(username="user1", password="pass123")
        response = self.client.get(self.update_url)
        self.assertEqual(response.context["answer"], self.answer)

class TestAnswerDeleteView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username="user1", email='test@example.com', password="pass123")
        self.user2 = User.objects.create_user(username="user2", email='test1@example.com', password="pass123")
        self.question = Question.objects.create(
            title="Test Question",
            description="Test Description",
            author=self.user1
        )
        self.answer = Answer.objects.create(
            question=self.question,
            author=self.user1,
            content="Answer to be deleted"
        )
        self.delete_url = reverse("answer_delete", kwargs={"answer_id": self.answer.pk})

    def test_should_redirect_anonymous_to_login_for_answer_delete(self):
        response = self.client.get(self.delete_url)
        self.assertNotEqual(response.status_code, 200)
        self.assertIn("/login/", response.url)

    def test_should_forbid_non_author_from_deleting_answer(self):
        self.client.login(username="user2", password="pass123")
        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, 403)

    def test_should_show_answer_delete_confirmation_to_author(self):
        self.client.login(username="user1", password="pass123")
        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Are you sure you want to delete")
        self.assertContains(response, self.answer.content)
        self.assertTemplateUsed(response, "forum/answer_confirm_delete.html")

    def test_should_delete_answer_on_post_by_author(self):
        self.client.login(username="user1", password="pass123")
        response = self.client.post(self.delete_url)
        with self.assertRaises(Answer.DoesNotExist):
            Answer.objects.get(pk=self.answer.pk)
        expected_url = reverse("question_detail", kwargs={"question_id": self.question.pk})
        self.assertRedirects(response, expected_url)

    def test_should_include_answer_in_delete_view_context(self):
        self.client.login(username="user1", password="pass123")
        response = self.client.get(self.delete_url)
        self.assertEqual(response.context["answer"], self.answer)

class TestAnswerDetailView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username="user1", email='test1@example.com', password="pass123")
        self.user2 = User.objects.create_user(username="user2", email='test@example.com', password="pass123")
        
        self.question = Question.objects.create(
            title="Test Question",
            description="Test Description",
            author=self.user1
        )
        
        self.answer = Answer.objects.create(
            question=self.question,
            author=self.user2,
            content="This is a test answer"
        )
        
        self.detail_url = reverse("answer_detail", kwargs={"answer_id": self.answer.pk})

    def test_should_allow_access_to_answer_detail_without_login(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)

    def test_should_render_answer_detail_template(self):
        response = self.client.get(self.detail_url)
        self.assertTemplateUsed(response, "forum/answer_detail.html")
        self.assertContains(response, self.answer.content)
        self.assertContains(response, self.question.title)

    def test_should_include_answer_and_question_in_detail_context(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.context["answer"], self.answer)
        self.assertEqual(response.context["question"], self.question)

    def test_should_include_vote_counts_in_answer_context(self):
        answer_ct = ContentType.objects.get_for_model(self.answer)
    
        Vote.objects.create(content_type=answer_ct, object_id=self.answer.pk, user=self.user1, vote_type=1)
        Vote.objects.create(content_type=answer_ct, object_id=self.answer.pk, user=self.user2, vote_type=-1)
    
        response = self.client.get(self.detail_url)
        self.assertEqual(response.context["answer_upvotes"], 1)
        self.assertEqual(response.context["answer_downvotes"], 1)

    def test_should_invalid_answer_returns_404(self):
        invalid_url = reverse("answer_detail", kwargs={"answer_id": 9999})
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, 404)
        
    def test_should_comments_paginated(self):
        self.client.login(username="user1", password="pass123")

        comments = [
            Comment.objects.create(
                author=self.user1,
                content=f"Comment {i}",
                content_object=self.answer,
            )
            for i in range(5)
        ]

        partial_url = reverse("answer-comments-partial", kwargs={"answer_id": self.answer.pk})

        response_page1 = self.client.get(partial_url)
        response_page2 = self.client.get(partial_url + "?page=2")

        self.assertEqual(response_page1.status_code, 200)
        self.assertTrue(response_page1.context["is_paginated"])
        self.assertEqual(len(response_page1.context["comments"]), 3)
        self.assertEqual(len(response_page2.context["comments"]), 2)

    def test_should_comment_count_displayed_in_template(self):
        Comment.objects.create(
            author=self.user1, content="First", content_object=self.answer
        )
        Comment.objects.create(
            author=self.user2, content="Second", content_object=self.answer
        )

        partial_url = reverse("answer-comments-partial", kwargs={"answer_id": self.answer.pk})
        response = self.client.get(partial_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("comments", response.context)
        self.assertEqual(response.context["paginator"].count, 2)

    
    def test_should_authenticated_user_can_post_valid_comment(self):
        self.client.login(username="user1", password="pass123")
        data = {"content": "Nice explanation!"}
        response = self.client.post(self.detail_url, data, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Comment.objects.filter(content="Nice explanation!").exists())

        comment = Comment.objects.get(content="Nice explanation!")
        self.assertEqual(comment.author, self.user1)
        self.assertEqual(comment.content_object, self.answer)
        # the detail page loads comments via HTMX; fetch the comments partial
        partial_url = reverse("answer-comments-partial", kwargs={"answer_id": self.answer.pk})
        partial_resp = self.client.get(partial_url)
        self.assertContains(partial_resp, "Nice explanation!")

    def test_should_anonymous_user_cannot_post_comment(self):
        data = {"content": "Should not work!"}
        response = self.client.post(self.detail_url, data)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)
        self.assertFalse(Comment.objects.filter(content="Should not work!").exists())

    def test_should_invalid_comment_form_rerenders_template(self):
        self.client.login(username="user1", password="pass123")
        data = {"content": ""}
        response = self.client.post(self.detail_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "forum/answer_detail.html")
        self.assertEqual(Comment.objects.count(), 0)


class TestCommentUpdateView(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(username="author", email='test@example.com', password="testpass123")
        self.other_user = User.objects.create_user(username="other", email='test1@example.com', password="testpass123")

        self.question = Question.objects.create(
            title="Sample Question", description="Desc", author=self.author
        )
        self.answer = Answer.objects.create(
            question=self.question, content="Sample Answer", author=self.author
        )

        self.comment = Comment.objects.create(
            content="Original Comment",
            author=self.author,
            content_object=self.answer
        )

        self.url = reverse("comment_update", kwargs={"comment_id": self.comment.id})

    def test_should_login_required(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_should_author_can_view_update_form(self):
        self.client.login(username="author", password="testpass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "forum/comment_update_form.html")
        self.assertIsInstance(response.context["form"], CommentForm)
        self.assertEqual(response.context["comment"], self.comment)

    def test_should_non_author_cannot_edit_comment(self):
        self.client.login(username="other", password="testpass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_should_author_can_update_comment(self):
        self.client.login(username="author", password="testpass123")
        response = self.client.post(self.url, {"content": "Updated Comment"})
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, "Updated Comment")
        self.assertRedirects(
            response,
            reverse("answer_detail", kwargs={"answer_id": self.answer.id})
        )

class TestCommentDeleteView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user1', email='test1@example.com', password='pass')
        self.other_user = User.objects.create_user(username='user2', email='test@example.com', password='pass')

        self.question = Question.objects.create(
            title="Test Question", description="desc", author=self.user
        )
        self.answer = Answer.objects.create(
            question=self.question, content="Answer content", author=self.user
        )
        self.comment = Comment.objects.create(
            content_object=self.answer, author=self.user, content="A comment"
        )
        self.url = reverse('comment_delete', kwargs={'comment_id': self.comment.id})

    def test_should_redirect_if_not_logged_in(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f'/accounts/login/?next={self.url}')

    def test_should_forbidden_if_not_author(self):
        self.client.login(username='user2', password='pass')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_should_delete_own_comment(self):
        self.client.login(username='user1', password='pass')
        response = self.client.post(self.url, follow=True)
        self.assertRedirects(
            response,
            reverse('answer_detail', kwargs={'answer_id': self.answer.id})
        )
        self.assertFalse(Comment.objects.filter(id=self.comment.id).exists())

    def test_should_delete_confirmation_page_loads(self):
        self.client.login(username='user1', password='pass')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Are you sure you want to delete this comment?")

class TestCommentReplyView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="john", email='test@example.com', password="pass123")
        self.question = Question.objects.create(
            title="Sample Question",
            description="This is a question body.",
            author=self.user,
        )
        self.answer = Answer.objects.create(
            question=self.question,
            content="This is an answer.",
            author=self.user,
        )
        self.parent_comment = Comment.objects.create(
            content_object=self.answer,
            author=self.user,
            content="This is a parent comment.",
        )
        self.url = reverse("answer_detail", args=[self.answer.id])

    def test_should_authenticated_user_can_post_reply(self):
        self.client.login(username="john", password="pass123")
        response = self.client.post(
            self.url,
            {
                "content": "This is a reply comment.",
                "parent": self.parent_comment.id,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        reply = Comment.objects.filter(parent=self.parent_comment).first()
        self.assertIsNotNone(reply)
        self.assertEqual(reply.content, "This is a reply comment.")
        self.assertEqual(reply.author, self.user)
        self.assertEqual(reply.content_object, self.answer)


    def test_should_invalid_reply_comment_empty_content(self):
        content_type = ContentType.objects.get_for_model(Answer)
        url = reverse("answer_detail", kwargs={"answer_id": self.answer.pk})

        data = {
            "content": "",
            "parent": self.parent_comment.id,
        }

        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), 1)

        replies = Comment.objects.filter(parent=self.parent_comment)
        self.assertEqual(replies.count(), 0)

    def test_should_anonymous_user_cannot_reply(self):
        response = self.client.post(
            self.url,
            {"content": "Anonymous reply", "parent": self.parent_comment.id},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)
        self.assertEqual(Comment.objects.count(), 1)

    def test_should_reply_is_associated_with_correct_parent(self):
        self.client.login(username="john", password="pass123")
        self.client.post(
            self.url,
            {"content": "Child reply", "parent": self.parent_comment.id},
        )
        reply = Comment.objects.filter(parent=self.parent_comment).first()
        self.assertIsNotNone(reply)
        self.assertEqual(reply.parent, self.parent_comment)
        self.assertEqual(reply.content_object, self.answer)

class TestQuestionFilter(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="tester", email='test@example.com', password="pass123")

        self.q1 = Question.objects.create(
            title="Learn Django", description="Django basics", author=self.user, created_at=timezone.now() - timezone.timedelta(days=2)
        )
        self.q2 = Question.objects.create(
            title="Python Tips", description="Advanced Python topics", author=self.user, created_at=timezone.now() - timezone.timedelta(days=1)
        )
        self.q3 = Question.objects.create(
            title="Web Development", description="Using Django and Flask", author=self.user, created_at=timezone.now()
        )

        self.q1.tags.add("django")
        self.q2.tags.add("python")
        self.q3.tags.add("django", "python")

        self.tag_django = Tag.objects.get(name="django")
        self.tag_python = Tag.objects.get(name="python")

        self.url = reverse('question_list')

    def test_should_search_questions_by_title_or_description(self):
        response = self.client.get(self.url, {"question": "django"})
        self.assertIn(self.q1, response.context['questions'])
        self.assertIn(self.q3, response.context['questions'])
        self.assertNotIn(self.q2, response.context['questions'])

    def test_should_filter_questions_by_tag_id(self):
        response = self.client.get(self.url, {"tag": self.tag_python.id})
        self.assertIn(self.q2, response.context["questions"])
        self.assertIn(self.q3, response.context["questions"])
        self.assertNotIn(self.q1, response.context["questions"])

    def test_should_clear_search_and_filter_when_no_params(self):
        response = self.client.get(self.url)
        self.assertCountEqual(response.context['questions'], [self.q1, self.q2, self.q3])

    def test_should_order_by_most_liked_when_vote_type_upvote(self):
        user2 = User.objects.create_user(username="voter2", email="v2@example.com", password="pass123")
        user3 = User.objects.create_user(username="voter3", email="v3@example.com", password="pass123")

        # q1: 1 upvote, q2: 2 upvotes, q3: 0 upvotes
        Vote.objects.create(user=self.user, content_object=self.q1, vote_type=Vote.VoteType.UPVOTE)
        Vote.objects.create(user=self.user, content_object=self.q2, vote_type=Vote.VoteType.UPVOTE)
        Vote.objects.create(user=user2, content_object=self.q2, vote_type=Vote.VoteType.UPVOTE)

        response = self.client.get(self.url, {"vote_type": Vote.VoteType.UPVOTE})
        questions = list(response.context["questions"])

        self.assertEqual(questions[0], self.q2)
        self.assertEqual(questions[1], self.q1)
        self.assertEqual(questions[2], self.q3)

    def test_should_order_by_least_liked_when_vote_type_downvote(self):
        user2 = User.objects.create_user(username="voter2", email="v2@example.com", password="pass123")
        user3 = User.objects.create_user(username="voter3", email="v3@example.com", password="pass123")

        # q1: 2 downvotes, q2: 1 downvote, q3: 0 downvotes
        Vote.objects.create(user=self.user, content_object=self.q1, vote_type=Vote.VoteType.DOWNVOTE)
        Vote.objects.create(user=user2, content_object=self.q1, vote_type=Vote.VoteType.DOWNVOTE)
        Vote.objects.create(user=user3, content_object=self.q2, vote_type=Vote.VoteType.DOWNVOTE)

        response = self.client.get(self.url, {"vote_type": Vote.VoteType.DOWNVOTE})
        questions = list(response.context["questions"])

        self.assertEqual(questions[0], self.q1)
        self.assertEqual(questions[1], self.q2)
        self.assertEqual(questions[2], self.q3)
