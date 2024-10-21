from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile  # Import the Profile model

# A form for registering new users, extending the built-in UserCreationForm
class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()  # Add an email field to the form

    # Meta class to specify the model and fields that the form works with
    class Meta:
        model = User  # Use the built-in User model
        fields = ['username', 'email', 'password1', 'password2']  # Fields shown in the form

    # Override the save method to create the associated Profile model after saving the user
    def save(self, commit=True):
        user = super().save(commit=False)  # Call the parent class's save method but don't commit yet
        if commit:
            user.save()  # Save the user instance
            # Automatically create a Profile for the new user with 'agree_to_privacy_policy' set to True
            Profile.objects.create(user=user, agree_to_privacy_policy=True)
        return user  # Return the saved user instance


# A form for updating user details (username and email)
class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()  # Add an email field to the form

    # Meta class to specify the model and fields that the form works with
    class Meta:
        model = User  # Use the built-in User model
        fields = ['username', 'email']  # Fields shown in the form