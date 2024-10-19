from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UserRegisterForm, UserUpdateForm
from .models import Profile  # Import the Profile model

from django.contrib.auth.models import User
from django.db import IntegrityError

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()  # Save the user instance
                # Create the profile only if it doesn't already exist
                Profile.objects.get_or_create(user=user)
                messages.success(request, 'Your account has been created! You can now log in.')
                return redirect('login')  # Redirect to login after registration
            except IntegrityError as e:
                # Handle the case where the profile already exists for the user
                messages.error(request, 'A profile already exists for this user.')
                return redirect('register')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})

@login_required
def profile(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        form = UserUpdateForm(instance=request.user)
    return render(request, 'users/profile.html', {'form': form})

@login_required
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