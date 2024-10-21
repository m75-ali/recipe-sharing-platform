from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UserRegisterForm, UserUpdateForm
from .models import Profile  # Import the Profile model
from django.contrib.auth.models import User
from django.db import IntegrityError

from django.contrib.auth import login
from django.contrib.auth import authenticate

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            try:
                # Save the user instance
                user = form.save(commit=False)
                user.is_active = True  # Ensure the user is active
                user.save()

                # Create the profile only if it doesn't already exist
                Profile.objects.get_or_create(user=user)

                # Authenticate the user to log them in
                new_user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password1'])

                if new_user is not None:
                    # Log the user in automatically after registration
                    login(request, new_user)
                    messages.success(request, 'Your account has been created and you are now logged in.')
                    # Redirect to the home page after login
                    return redirect('recipe_index')
                else:
                    messages.error(request, 'There was an issue logging you in. Please try again.')
                    return redirect('login')
                
            except IntegrityError:
                # Handle the case where the profile already exists for the user
                messages.error(request, 'A profile already exists for this user.')
                return redirect('register')
    else:
        form = UserRegisterForm()

    return render(request, 'users/register.html', {'form': form})



def profile(request):
    user_favorites = request.user.favorite_recipes.all()  # Fetch the user's favorited recipes
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        form = UserUpdateForm(instance=request.user)
    return render(request, 'users/profile.html', {'form': form, 'favorites': user_favorites})

def privacy_policy(request):
    return render(request, 'users/privacy_policy.html')