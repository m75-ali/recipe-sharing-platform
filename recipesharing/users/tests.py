from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from .forms import UserRegisterForm, UserUpdateForm

class UserRegistrationTest(TestCase):
    def test_register_view_get(self):
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/register.html")

    def test_register_view_post_valid_data(self):
        response = self.client.post(reverse("register"), {
            "username": "newuser",
            "password1": "testpassword123",
            "password2": "testpassword123",
            "email": "newuser@example.com",
        })
        self.assertRedirects(response, reverse("recipe_index"))
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_register_view_post_invalid_data(self):
        response = self.client.post(reverse("register"), {
            "username": "newuser",
            "password1": "password",
            "password2": "differentpassword",
            "email": "invalidemail",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, "form", "password2", "The two password fields didn’t match.")

class UserLoginTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpassword123")

    def test_login_view_get(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/login.html")

    def test_login_view_post_valid_data(self):
        response = self.client.post(reverse("login"), {
            "username": "testuser",
            "password": "testpassword123",
        })
        self.assertRedirects(response, reverse("recipe_index"))

    def test_login_view_post_invalid_data(self):
        response = self.client.post(reverse("login"), {
            "username": "testuser",
            "password": "wrongpassword",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter a correct username and password.")

class UserProfileUpdateTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpassword123")
        self.client.login(username="testuser", password="testpassword123")

    def test_profile_view_get(self):
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/profile.html")

    def test_profile_update_post_valid_data(self):
        response = self.client.post(reverse("profile"), {
            "username": "updateduser",
            "email": "updateduser@example.com",
        })
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "updateduser")
        self.assertEqual(self.user.email, "updateduser@example.com")
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Your profile has been updated!")

    def test_profile_update_post_invalid_data(self):
        response = self.client.post(reverse("profile"), {
            "username": "",  # Invalid data
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, "form", "username", "This field is required.")