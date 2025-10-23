from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from forum.models import Question,Vote

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
