from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from .forms import RecipeForm
from .models import Recipe, Rating
from django.db.models import Avg
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse

# View to list all recipes with their average ratings
def index(request):
    # Fetch all recipes from the database
    recipes = Recipe.objects.all()

    # Loop through each recipe to calculate its average rating
    for recipe in recipes:
        average_rating = recipe.ratings.aggregate(Avg('rating'))['rating__avg']
        # Set the average rating, or None if there are no ratings
        recipe.average_rating = average_rating if average_rating is not None else None

    # Render the index page with the list of recipes
    return render(request, 'recipes/index.html', {'recipes': recipes})

# View to add a new recipe (login required)
@login_required
def add_recipe(request):
    # If the form is submitted (POST request)
    if request.method == 'POST':
        form = RecipeForm(request.POST)
        # If the form is valid, save the new recipe
        if form.is_valid():
            recipe = form.save(commit=False)
            recipe.creator = request.user  # Assign the logged-in user as the creator
            recipe.save()
            messages.success(request, 'Recipe added successfully.')  # Success message
            return redirect('recipe_index')  # Redirect to the index page
    else:
        form = RecipeForm()  # Show an empty form for GET request
    return render(request, 'recipes/add_recipe.html', {'form': form})

# View to show recipe details and allow users to rate it (login required for rating)
@login_required
def recipe_detail(request, recipe_id):
    # Fetch the recipe by ID or return a 404 error if not found
    recipe = get_object_or_404(Recipe, id=recipe_id)
    user_rating = None  # To store the current user's rating

    # Handle rating submission (if the POST request includes a rating)
    if request.method == 'POST' and 'rating' in request.POST:
        rating_value = int(request.POST.get('rating'))  # Get the rating from the form
        # Check if the user has already rated the recipe
        rating, created = Rating.objects.get_or_create(user=request.user, recipe=recipe, defaults={'rating': rating_value})

        if not created:
            # Update the rating if the user already rated this recipe
            rating.rating = rating_value
            rating.save()

        messages.success(request, f'Thank you for rating {recipe.title}!')  # Success message
        return redirect('recipe_detail', recipe_id=recipe.id)  # Redirect to the same page

    # Check if the user has already rated the recipe
    if request.user.is_authenticated:
        user_rating = Rating.objects.filter(user=request.user, recipe=recipe).first()

    # Calculate the average rating for the recipe
    average_rating = recipe.ratings.aggregate(Avg('rating'))['rating__avg'] or 0

    # Render the recipe details page with the user's rating and average rating
    return render(request, 'recipes/recipe_detail.html', {
        'recipe': recipe,
        'user_rating': user_rating,
        'average_rating': average_rating
    })

# View to edit a recipe (login required)
@login_required
def edit_recipe(request, recipe_id):
    # Fetch the recipe by ID or return a 404 error if not found
    recipe = get_object_or_404(Recipe, id=recipe_id)

    # Ensure that the user editing the recipe is its creator
    if recipe.creator != request.user:
        messages.error(request, "You cannot edit someone else's recipe.")  # Error message
        return redirect('recipe_detail', recipe_id=recipe_id)  # Redirect to the recipe details page

    # Handle form submission
    if request.method == 'POST':
        form = RecipeForm(request.POST, instance=recipe)
        if form.is_valid():
            form.save()  # Save the updated recipe
            messages.success(request, 'Recipe updated successfully.')  # Success message
            return redirect('recipe_detail', recipe_id=recipe_id)  # Redirect to the recipe details page
    else:
        form = RecipeForm(instance=recipe)  # Pre-fill the form with existing data

    # Render the edit recipe page with the form
    return render(request, 'recipes/edit_recipe.html', {'form': form, 'recipe': recipe})

# View to delete a recipe (login required)
@login_required
def delete_recipe(request, recipe_id):
    # Fetch the recipe by ID or return a 404 error if not found
    recipe = get_object_or_404(Recipe, id=recipe_id)

    # Ensure that the user deleting the recipe is its creator
    if recipe.creator != request.user:
        messages.error(request, 'You are not authorized to delete this recipe.')  # Error message
        return redirect('recipe_detail', recipe_id=recipe.id)  # Redirect to the recipe details page

    # Handle form submission (confirm deletion)
    if request.method == 'POST':
        recipe.delete()  # Delete the recipe
        messages.success(request, 'Recipe deleted successfully.')  # Success message
        return redirect('recipe_index')  # Redirect to the index page

    # Render the delete confirmation page
    return render(request, 'recipes/delete_recipe.html', {'recipe': recipe})

# View to mark/unmark a recipe as a favorite (login required)
@login_required
def favorite_recipe(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)  # Fetch the recipe by ID
    # Check if the recipe is already favorited by the user
    if recipe.favorites.filter(id=request.user.id).exists():
        recipe.favorites.remove(request.user)  # Unfavorite the recipe
    else:
        recipe.favorites.add(request.user)  # Favorite the recipe
    # Redirect to the recipe details page
    return HttpResponseRedirect(reverse('recipe_detail', args=[recipe_id]))