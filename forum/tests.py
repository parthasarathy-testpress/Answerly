from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from forum.models import Question,Vote,Answer,Comment
from django.contrib.contenttypes.models import ContentType

class QuestionListViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='pass123')
        self.user2 = User.objects.create_user(username='otheruser', password='pass123')

        for i in range(15):
            Question.objects.create(
                title=f'Question {i}',
                description='Test description',
                author=self.user
            )

        question1 = Question.objects.latest('created_at')
        question1.votes.create(user=self.user, vote_type=1)
        question1.votes.create(user=self.user2, vote_type=-1)

    def test_question_list_view_status_and_template(self):
        """Check that the list view returns 200 and uses correct template"""
        response = self.client.get(reverse('question_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'forum/question_list.html')

    def test_question_list_context(self):
        """Check that the context contains questions and total_votes is annotated"""
        response = self.client.get(reverse('question_list'))
        self.assertIn('questions', response.context)
        first_question = response.context['questions'][0]
        self.assertTrue(hasattr(first_question, 'total_votes'))
        # total_votes = 1 upvote - 1 downvote = 0
        self.assertEqual(first_question.total_votes, 0)

    def test_pagination(self):
        """Check that pagination works (paginate_by = 10)"""
        response = self.client.get(reverse('question_list'))
        self.assertEqual(len(response.context['questions']), 10)

        response_page2 = self.client.get(reverse('question_list') + '?page=2')
        self.assertEqual(len(response_page2.context['questions']), 5)

class QuestionCreateViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='pass123')
        self.url = reverse('question_post')

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(self.url)
        expected_url = reverse('login') + '?next=' + self.url
        self.assertRedirects(response, expected_url)

    def test_form_display(self):
        self.client.login(username='testuser', password='pass123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<form')

    def test_create_question_with_tags(self):
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


class QuestionUpdateViewTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(username='author', password='pass1234')
        self.other_user = User.objects.create_user(username='other', password='pass1234')

        self.question = Question.objects.create(
            title='Original Title',
            description='Original description',
            author=self.author
        )
        self.question.tags.add('django', 'python')

        self.url = reverse('question_edit', kwargs={'question_id': self.question.pk})

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(self.url)
        expected_url = reverse('login') + '?next=' + self.url
        self.assertRedirects(response, expected_url)

    def test_access_denied_if_not_author(self):
        self.client.login(username='other', password='pass1234')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_get_update_view_as_author(self):
        self.client.login(username='author', password='pass1234')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Original Title')

class QuestionDeleteViewTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(username='author', password='pass1234')
        self.other_user = User.objects.create_user(username='other', password='pass1234')

        self.question = Question.objects.create(
            title='Original Title',
            description='Original description',
            author=self.author
        )
        
        self.url = reverse('question_delete', args=[self.question.pk])

    def test_author_can_delete_question(self):
        self.client.login(username='author', password='pass1234')
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse('question_list'))
        self.assertFalse(Question.objects.filter(id=self.question.pk).exists())

    def test_non_author_cannot_delete_question(self):
        self.client.login(username='other', password='pass1234')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Question.objects.filter(id=self.question.pk).exists())

    def test_anonymous_user_redirected_to_login(self):
        response = self.client.post(self.url)
        login_url = reverse('login')
        self.assertRedirects(response, f'{login_url}?next={self.url}')
        self.assertTrue(Question.objects.filter(id=self.question.pk).exists())
    
    def test_get_delete_confirmation_page(self):
        self.client.login(username='author', password='pass1234')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'forum/question_confirm_delete.html')
        self.assertContains(response, 'Are you sure you want to delete this question?')

class QuestionDetailViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username="user1", password="pass123")
        self.user2 = User.objects.create_user(username="user2", password="pass123")
        self.question = Question.objects.create(
            title="Test Question",
            description="Test Description",
            author=self.user1
        )
        self.detail_url = reverse("question_detail", kwargs={"question_id": self.question.pk})
        
    def test_detail_view_renders(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.question.title)
        self.assertContains(response, self.question.description)

    def test_votes_count_in_context(self):
        Vote.objects.create(user=self.user1, content_object=self.question, vote_type=1)
        Vote.objects.create(user=self.user2, content_object=self.question, vote_type=-1)
        
        response = self.client.get(self.detail_url)
        self.assertEqual(response.context["question_upvotes"], 1)
        self.assertEqual(response.context["question_downvotes"], 1)
        
class AnswerListPaginationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="user1", password="pass123")
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

        self.url = reverse("question_detail", kwargs={"question_id": self.question.pk})

    def test_first_page_answers_count(self):
        response = self.client.get(self.url)
        answers = response.context["answers"]
        self.assertEqual(len(answers), 3)
        self.assertTrue(response.context["is_paginated"])
        self.assertEqual(response.context["page_obj"].number, 1)

    def test_second_page_answers_count(self):
        response = self.client.get(f"{self.url}?page=2")
        answers = response.context["answers"]
        self.assertEqual(len(answers), 3)
        self.assertTrue(response.context["is_paginated"])
        self.assertEqual(response.context["page_obj"].number, 2)

    def test_third_page_answers_count(self):
        response = self.client.get(f"{self.url}?page=3")
        answers = response.context["answers"]
        self.assertEqual(len(answers), 1)
        self.assertTrue(response.context["is_paginated"])
        self.assertEqual(response.context["page_obj"].number, 3)

    def test_invalid_page_number(self):
        response = self.client.get(f"{self.url}?page=999")
        answers = response.context["answers"]
        self.assertEqual(len(answers), 1)
        self.assertEqual(response.context["page_obj"].number, 3)

class AnswerCreateViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="pass123")
        self.other_user = User.objects.create_user(username="otheruser", password="pass123")
        self.question = Question.objects.create(
            title="Test Question",
            description="Test Description",
            author=self.user
        )
        self.url = reverse("answer_post", kwargs={"question_id": self.question.pk})

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(self.url)
        login_url = reverse("login") + f"?next={self.url}"
        self.assertRedirects(response, login_url)

    def test_view_renders_for_logged_in_user(self):
        self.client.login(username="testuser", password="pass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "forum/answer_form.html")

    def test_post_valid_answer_creates_object(self):
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

    def test_post_invalid_answer_shows_errors(self):
        self.client.login(username="testuser", password="pass123")
        data = {"content": ""}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")
        self.assertEqual(Answer.objects.count(), 0)

    def test_context_contains_question(self):
        self.client.login(username="testuser", password="pass123")
        response = self.client.get(self.url)
        self.assertEqual(response.context["question"], self.question)

class AnswerUpdateViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username="user1", password="pass123")
        self.user2 = User.objects.create_user(username="user2", password="pass123")
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

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(self.update_url)
        expected_url = f"{reverse('login')}?next={self.update_url}"
        self.assertRedirects(response, expected_url)

    def test_access_by_non_author_forbidden(self):
        self.client.login(username="user2", password="pass123")
        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 403)

    def test_access_by_author_renders_form(self):
        self.client.login(username="user1", password="pass123")
        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Original Answer")
        self.assertTemplateUsed(response, "forum/answer_update_form.html")

    def test_successful_answer_update(self):
        self.client.login(username="user1", password="pass123")
        response = self.client.post(self.update_url, {"content": "Updated Answer"})
        self.answer.refresh_from_db()
        self.assertEqual(self.answer.content, "Updated Answer")
        expected_url = reverse("question_detail", kwargs={"question_id": self.question.pk})
        self.assertRedirects(response, expected_url)

    def test_context_contains_answer(self):
        self.client.login(username="user1", password="pass123")
        response = self.client.get(self.update_url)
        self.assertEqual(response.context["answer"], self.answer)

class AnswerDeleteViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username="user1", password="pass123")
        self.user2 = User.objects.create_user(username="user2", password="pass123")
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

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(self.delete_url)
        self.assertNotEqual(response.status_code, 200)
        self.assertIn("/login/", response.url)

    def test_access_by_non_author_forbidden(self):
        self.client.login(username="user2", password="pass123")
        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, 403)

    def test_access_by_author_renders_confirmation_page(self):
        self.client.login(username="user1", password="pass123")
        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Are you sure you want to delete")
        self.assertContains(response, self.answer.content)
        self.assertTemplateUsed(response, "forum/answer_confirm_delete.html")

    def test_successful_answer_deletion(self):
        self.client.login(username="user1", password="pass123")
        response = self.client.post(self.delete_url)
        with self.assertRaises(Answer.DoesNotExist):
            Answer.objects.get(pk=self.answer.pk)
        expected_url = reverse("question_detail", kwargs={"question_id": self.question.pk})
        self.assertRedirects(response, expected_url)

    def test_context_contains_answer(self):
        self.client.login(username="user1", password="pass123")
        response = self.client.get(self.delete_url)
        self.assertEqual(response.context["answer"], self.answer)

class AnswerDetailViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username="user1", password="pass123")
        self.user2 = User.objects.create_user(username="user2", password="pass123")
        
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

    def test_detail_view_is_accessible_without_login(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)

    def test_detail_view_renders_correct_template(self):
        response = self.client.get(self.detail_url)
        self.assertTemplateUsed(response, "forum/answer_detail.html")
        self.assertContains(response, self.answer.content)
        self.assertContains(response, self.question.title)

    def test_context_contains_answer_and_question(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.context["answer"], self.answer)
        self.assertEqual(response.context["question"], self.question)

    def test_vote_counts_in_context(self):
        answer_ct = ContentType.objects.get_for_model(self.answer)
    
        Vote.objects.create(content_type=answer_ct, object_id=self.answer.pk, user=self.user1, vote_type=1)
        Vote.objects.create(content_type=answer_ct, object_id=self.answer.pk, user=self.user2, vote_type=-1)
    
        response = self.client.get(self.detail_url)
        self.assertEqual(response.context["answer_upvotes"], 1)
        self.assertEqual(response.context["answer_downvotes"], 1)

    def test_invalid_answer_returns_404(self):
        invalid_url = reverse("answer_detail", kwargs={"answer_id": 9999})
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, 404)
        
    def test_comments_paginated(self):
        self.client.login(username="user1", password="pass123")

        comments = [
            Comment.objects.create(
                author=self.user1,
                content=f"Comment {i}",
                content_object=self.answer,
            )
            for i in range(5)
        ]

        response_page1 = self.client.get(self.detail_url)
        response_page2 = self.client.get(self.detail_url + "?page=2")

        self.assertEqual(response_page1.status_code, 200)
        self.assertTrue(response_page1.context["is_paginated"])
        self.assertEqual(len(response_page1.context["comments"]), 3)
        self.assertEqual(len(response_page2.context["comments"]), 2)

    def test_comment_count_displayed_in_template(self):
        Comment.objects.create(
            author=self.user1, content="First", content_object=self.answer
        )
        Comment.objects.create(
            author=self.user2, content="Second", content_object=self.answer
        )

        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("comments", response.context)
        self.assertEqual(response.context["comments"].paginator.count, 2)

    
    def test_authenticated_user_can_post_valid_comment(self):
        self.client.login(username="user1", password="pass123")
        data = {"content": "Nice explanation!"}
        response = self.client.post(self.detail_url, data, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Comment.objects.filter(content="Nice explanation!").exists())

        comment = Comment.objects.get(content="Nice explanation!")
        self.assertEqual(comment.author, self.user1)
        self.assertEqual(comment.content_object, self.answer)
        self.assertContains(response, "Nice explanation!")

    def test_anonymous_user_cannot_post_comment(self):
        data = {"content": "Should not work!"}
        response = self.client.post(self.detail_url, data)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)
        self.assertFalse(Comment.objects.filter(content="Should not work!").exists())

    def test_invalid_comment_form_rerenders_template(self):
        self.client.login(username="user1", password="pass123")
        data = {"content": ""}
        response = self.client.post(self.detail_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "forum/answer_detail.html")
        self.assertEqual(Comment.objects.count(), 0)

class AnswerDetailNestedRepliesTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="pass123")

        self.question = Question.objects.create(
            title="Q1",
            description="This is a sample question",
            author=self.user,
        )

        self.answer = Answer.objects.create(
            question=self.question,
            author=self.user,
            content="This is a sample answer",
        )

        self.answer_ct = ContentType.objects.get_for_model(Answer)
        self.comment_ct = ContentType.objects.get_for_model(Comment)

        self.comment = Comment.objects.create(
            author=self.user,
            content_type=self.answer_ct,
            object_id=self.answer.pk,
            content="Top-level comment",
        )

        self.reply1 = Comment.objects.create(
            author=self.user,
            content_type=self.comment_ct,
            object_id=self.comment.pk,
            parent=self.comment,
            content="Reply level 1",
        )
        self.reply2 = Comment.objects.create(
            author=self.user,
            content_type=self.comment_ct,
            object_id=self.reply1.pk,
            parent=self.reply1,
            content="Reply level 2",
        )
        self.reply3 = Comment.objects.create(
            author=self.user,
            content_type=self.comment_ct,
            object_id=self.reply2.pk,
            parent=self.reply2,
            content="Reply level 3",
        )

        for c in [self.comment, self.reply1, self.reply2, self.reply3]:
            Vote.objects.create(
                user=self.user,
                vote_type=1,
                content_type=ContentType.objects.get_for_model(Comment),
                object_id=c.pk,
            )

        self.url = reverse("answer_detail", kwargs={"answer_id": self.answer.pk})

    def test_nested_replies_in_context(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        comments = response.context["comments"]
        self.assertEqual(len(comments), 1, "Expected one top-level comment")

        top_comment = comments[0]
        self.assertTrue(hasattr(top_comment, "replies_cached"))

        self.assertEqual(len(top_comment.replies_cached), 1)
        level1 = top_comment.replies_cached[0]

        self.assertEqual(len(level1.replies_cached), 1)
        level2 = level1.replies_cached[0]

        self.assertEqual(len(level2.replies_cached), 1)
        level3 = level2.replies_cached[0]

        self.assertEqual(level3.content, "Reply level 3")

    def test_vote_counts_for_nested_replies(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        comments = response.context["comments"]
        top_comment = comments[0]

        self.assertEqual(top_comment.upvotes, 1)

        reply1 = top_comment.replies_cached[0]
        reply2 = reply1.replies_cached[0]
        reply3 = reply2.replies_cached[0]

        self.assertEqual(reply1.upvotes, 1)
        self.assertEqual(reply2.upvotes, 1)
        self.assertEqual(reply3.upvotes, 1)

    def test_pagination_applies_only_to_top_level_comments(self):
        for i in range(5):
            Comment.objects.create(
                author=self.user,
                content_type=self.answer_ct,
                object_id=self.answer.pk,
                content=f"Extra top comment {i}",
            )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        self.assertTrue(response.context["is_paginated"])
        self.assertEqual(
            len(response.context["comments"]),
            3,
            "Expected only 3 top-level comments per page",
        )

        for comment in response.context["comments"]:
            self.assertTrue(hasattr(comment, "replies_cached"))
