from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

class LoginViewTests(TestCase):

    def setUp(self):
        self.url = reverse('login')
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='StrongPass123!')

    def test_login_page_loads(self):
        """GET request should render login page"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_login_success(self):
        """POST valid credentials should log in user and redirect"""
        data = {
            'username': 'testuser',
            'password': 'StrongPass123!'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)
        self.assertEqual(response.status_code, 302)

    def test_login_invalid_credentials(self):
        """POST invalid credentials should re-render form with non-field errors"""
        data = {
            'username': 'testuser',
            'password': 'WrongPassword'
        }
        response = self.client.post(self.url, data)
        response.render()  # type: ignore
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertContains(response, "Please enter a correct username and password")

class SignupViewTests(TestCase):

    def setUp(self):
        self.url = reverse('signup')

    def test_signup_page_loads(self):
        """GET request should render the signup page"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/signup.html')

    def test_signup_success(self):
        """POST valid data should create a user and redirect"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!'
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(response, reverse('question_list'))
        self.assertTrue(User.objects.filter(username='testuser').exists())

    def test_signup_invalid(self):
        """POST invalid data should re-render form with errors"""
        data = {
            'username': '',
            'email': 'invalid-email',
            'password1': '123',
            'password2': '456'
        }
        response = self.client.post(self.url, data)
        response.render()  # type: ignore
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required") 
        self.assertContains(response, "Enter a valid email address") 