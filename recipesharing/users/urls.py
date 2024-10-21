from django.urls import path
from django.contrib.auth import views as auth_views
from . import views  # Import views from the current app

# URL patterns for the users app
urlpatterns = [
    # URL for the registration page, handled by the 'register' view
    path('register/', views.register, name='register'),

    # URL for the login page, using Django's built-in LoginView with a custom template
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),

    # URL for the logout functionality, using Django's built-in LogoutView
    path('logout/', auth_views.LogoutView.as_view(), name='users/logout'),

    # URL for the privacy policy page, handled by the 'privacy_policy' view
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),  # Custom view for privacy policy

    # URLs for the password reset functionality (Django built-in views)
    
    # Initiates the password reset process by sending an email to the user
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),

    # Confirmation page after the user submits their email for password reset
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),

    # URL for confirming the password reset using a token (sent via email)
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),

    # Final confirmation page after the password has been successfully reset
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # URL for the user profile page, handled by the 'profile' view
    path('profile/', views.profile, name='profile'),
]