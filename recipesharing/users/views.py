from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UserRegisterForm, UserUpdateForm
from .models import Profile  # Import the Profile model
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.contrib.auth import login, authenticate

# View for user registration
def register(request):
    if request.method == 'POST':  # If the form is submitted
        form = UserRegisterForm(request.POST)  # Bind the form with the POST data
        if form.is_valid():
            try:
                # Save the user instance but don't commit yet (to modify it before saving)
                user = form.save(commit=False)
                user.is_active = True  # Ensure the user is active
                user.save()  # Save the user to the database

                # Create the profile for the user if it doesn't exist
                Profile.objects.get_or_create(user=user)

                # Authenticate the new user using the username and password from the form
                new_user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password1'])

                if new_user is not None:
                    # Log the user in after registration
                    login(request, new_user)
                    messages.success(request, 'Your account has been created and you are now logged in.')
                    # Redirect to the recipe index (home) page
                    return redirect('recipe_index')
                else:
                    messages.error(request, 'There was an issue logging you in. Please try again.')
                    return redirect('login')
            
            # Handle the case where a profile already exists for the user (database integrity error)
            except IntegrityError:
                messages.error(request, 'A profile already exists for this user.')
                return redirect('register')
    else:
        form = UserRegisterForm()  # If the request is GET, show a blank registration form

    return render(request, 'users/register.html', {'form': form})  # Render the registration page


# View for the user profile page (login required)
@login_required  # Ensure the user is logged in before accessing this view
def profile(request):
    user_favorites = request.user.favorite_recipes.all()  # Fetch the user's favorited recipes
    if request.method == 'POST':  # If the form is submitted
        form = UserUpdateForm(request.POST, instance=request.user)  # Bind the form with POST data and current user instance
        if form.is_valid():
            form.save()  # Save the updated user details
            messages.success(request, 'Your profile has been updated!')  # Show a success message
            return redirect('profile')  # Redirect to the profile page after update
    else:
        form = UserUpdateForm(instance=request.user)  # If GET request, pre-fill the form with user data
    return render(request, 'users/profile.html', {'form': form, 'favorites': user_favorites})  # Render the profile page


# View for displaying the privacy policy
def privacy_policy(request):
    return render(request, 'users/privacy_policy.html')  # Render the privacy policy page