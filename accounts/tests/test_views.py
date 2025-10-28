from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

class LoginViewTests(TestCase):

    def setUp(self):
        self.url = reverse('login')
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='StrongPass123!') # type: ignore

    def test_login_page_loads(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_login_success(self):
        data = {
            'username': 'testuser',
            'password': 'StrongPass123!'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)
        self.assertEqual(response.status_code, 302)

    def test_login_invalid_credentials(self):
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
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/signup.html')

    def test_signup_success(self):
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!'
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(response,"/")
        self.assertTrue(User.objects.filter(username='testuser').exists())

    def test_signup_invalid(self):
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
        self.assertContains(response, "The two password fields didn’t match.")
         
class UserProfileEditTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="john_doe",
            email="john@example.com",
            password="strongpassword123"
        )
        self.client.login(username="john_doe", password="strongpassword123")
        self.url = reverse("profile")

    def test_profile_edit_view_renders_form(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Edit Your Profile")
        self.assertContains(response, "name=\"username\"")
        self.assertContains(response, "name=\"email\"")

    def test_profile_edit_requires_login(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)

    def test_valid_profile_update(self):
        data = {
            "username": "new_john",
            "first_name": "John",
            "last_name": "Smith",
            "email": "newjohn@example.com",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)

        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "new_john")
        self.assertEqual(self.user.first_name, "John")
        self.assertEqual(self.user.last_name, "Smith")
        self.assertEqual(self.user.email, "newjohn@example.com")

    def test_invalid_email_rejected(self):
        data = {
            "username": "john_doe",
            "email": "invalid_email",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enter a valid email address")

    def test_duplicate_email_rejected(self):
        User.objects.create_user(
            username="jane",
            email="jane@example.com",
            password="pass123"
        )
        data = {
            "username": "john_doe",
            "email": "jane@example.com",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already exists")

    def test_blank_username_rejected(self):
        data = {
            "username": "",
            "email": "john@example.com",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")
