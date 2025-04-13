# users/tests.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from users.models import Profile
from users.forms import UserRegisterForm, UserUpdateForm

class UserModelTest(TestCase):
    def setUp(self):
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
    
    def test_profile_creation(self):
        """Test that a profile is automatically created when a user is created"""
        self.assertTrue(hasattr(self.test_user, 'profile'))
        self.assertIsInstance(self.test_user.profile, Profile)
    
    def test_profile_str_method(self):
        """Test the string representation of a Profile"""
        self.assertEqual(str(self.test_user.profile), 'testuser Profile')
    
    def test_privacy_policy_default(self):
        """Test that the privacy policy agreement is False by default"""
        # Note: This depends on how your signal is set up - modify if needed
        self.assertFalse(self.test_user.profile.agree_to_privacy_policy)


class UserFormTest(TestCase):
    def test_user_register_form_valid(self):
        """Test that UserRegisterForm validates with correct data"""
        form_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'Complex_password123',
            'password2': 'Complex_password123'
        }
        form = UserRegisterForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_user_register_form_passwords_not_matching(self):
        """Test that form validation fails when passwords don't match"""
        form_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'Complex_password123',
            'password2': 'Different_password123'
        }
        form = UserRegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)
    
    def test_user_update_form_valid(self):
        """Test that UserUpdateForm validates with correct data"""
        user = User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='testpassword123'
        )
        
        form_data = {
            'username': 'updateduser',
            'email': 'updated@example.com'
        }
        form = UserUpdateForm(data=form_data, instance=user)
        self.assertTrue(form.is_valid())


class UserViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.profile_url = reverse('profile')
        self.privacy_url = reverse('privacy_policy')
        
        # Create a test user
        self.test_user = User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='testpassword123'
        )
    
    def test_register_view_get(self):
        """Test that register view returns a form on GET"""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/register.html')
        self.assertIsInstance(response.context['form'], UserRegisterForm)
    
    def test_register_view_post_success(self):
        """Test successful user registration"""
        user_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'Complex_password123',
            'password2': 'Complex_password123'
        }
        response = self.client.post(self.register_url, user_data)
        
        # Should redirect to home page after successful registration
        self.assertRedirects(response, reverse('recipe_index'))
        
        # Check that the user was created
        self.assertTrue(User.objects.filter(username='newuser').exists())
        
        # Check that a profile was created
        user = User.objects.get(username='newuser')
        self.assertTrue(hasattr(user, 'profile'))
    
    def test_register_view_post_failure(self):
        """Test registration failure with existing username"""
        user_data = {
            'username': 'existinguser',  # This username already exists
            'email': 'new@example.com',
            'password1': 'Complex_password123',
            'password2': 'Complex_password123'
        }
        response = self.client.post(self.register_url, user_data)
        
        # Should remain on the registration page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/register.html')
        
        # Form should have errors
        self.assertTrue(response.context['form'].errors)
    
    def test_profile_view_requires_login(self):
        """Test that profile view requires login"""
        # Try accessing profile page without login
        response = self.client.get(self.profile_url)
        
        # Should redirect to login page
        self.assertRedirects(response, f'{self.login_url}?next={self.profile_url}')
    
    def test_profile_view_get(self):
        """Test that profile view shows form with user data when logged in"""
        # Login
        self.client.login(username='existinguser', password='testpassword123')
        
        # Access profile page
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/profile.html')
        self.assertIsInstance(response.context['form'], UserUpdateForm)
        self.assertEqual(response.context['form'].instance, self.test_user)
    
    def test_profile_view_post(self):
        """Test profile update"""
        # Login
        self.client.login(username='existinguser', password='testpassword123')
        
        # Update profile data
        update_data = {
            'username': 'updateduser',
            'email': 'updated@example.com'
        }
        
        response = self.client.post(self.profile_url, update_data)
        
        # Should redirect to profile page after successful update
        self.assertRedirects(response, self.profile_url)
        
        # Check that the user data was updated
        self.test_user.refresh_from_db()
        self.assertEqual(self.test_user.username, 'updateduser')
        self.assertEqual(self.test_user.email, 'updated@example.com')
    
    def test_privacy_policy_view(self):
        """Test privacy policy view"""
        response = self.client.get(self.privacy_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/privacy_policy.html')


class UserIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.profile_url = reverse('profile')
        self.logout_url = reverse('logout')
    
    def test_user_registration_login_profile_update_logout(self):
        """Test the complete user flow"""
        # 1. Register a new user
        user_data = {
            'username': 'testintegration',
            'email': 'integration@example.com',
            'password1': 'Complex_password123',
            'password2': 'Complex_password123'
        }
        response = self.client.post(self.register_url, user_data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # User should be logged in automatically
        self.assertTrue(response.context['user'].is_authenticated)
        
        # 2. Test accessing profile
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        
        # 3. Update profile
        update_data = {
            'username': 'updatedintegration',
            'email': 'updated_integration@example.com'
        }
        response = self.client.post(self.profile_url, update_data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Check user data was updated
        user = User.objects.get(username='updatedintegration')
        self.assertEqual(user.email, 'updated_integration@example.com')
        
        # 4. Logout
        response = self.client.get(self.logout_url, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # User should be logged out
        self.assertFalse(response.context['user'].is_authenticated)
        
        # 5. Verify login works with new credentials
        login_successful = self.client.login(
            username='updatedintegration', 
            password='Complex_password123'
        )
        self.assertTrue(login_successful)