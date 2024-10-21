from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from .forms import RecipeForm
from .models import Recipe, Rating
from django.db.models import Avg
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse

# Create your views here.
def index(request):
    recipes = Recipe.objects.all()  # Fetch all recipes from the database
    return render(request, 'recipes/index.html', {'recipes': recipes})

@login_required
def add_recipe(request):
    if request.method == 'POST':
        form = RecipeForm(request.POST)
        if form.is_valid():
            recipe = form.save(commit=False)
            recipe.creator = request.user  # Assign the logged-in user as the creator
            recipe.save()
            messages.success(request, 'Recipe added successfully.')
            return redirect('recipe_index')
    else:
        form = RecipeForm()
    return render(request, 'recipes/add_recipe.html', {'form': form})


@login_required
def recipe_detail(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)  # Fetch the recipe by ID
    user_rating = None

    # Handle rating submission
    if request.method == 'POST' and 'rating' in request.POST:
        rating_value = int(request.POST.get('rating'))
        # Check if the user has already rated this recipe
        rating, created = Rating.objects.get_or_create(user=request.user, recipe=recipe, defaults={'rating': rating_value})

        if not created:
            # Update existing rating
            rating.rating = rating_value
            rating.save()

        messages.success(request, f'Thank you for rating {recipe.title}!')
        return redirect('recipe_detail', recipe_id=recipe.id)

    # Get the user's rating if it exists
    if request.user.is_authenticated:
        user_rating = Rating.objects.filter(user=request.user, recipe=recipe).first()

    # Get the average rating for the recipe
    average_rating = recipe.ratings.aggregate(Avg('rating'))['rating__avg'] or 0

    return render(request, 'recipes/recipe_detail.html', {
        'recipe': recipe,
        'user_rating': user_rating,
        'average_rating': average_rating
    })

@login_required
def edit_recipe(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    
    # Check if the current user is the creator of the recipe
    if recipe.creator != request.user:
        messages.error(request, 'You are not authorized to edit this recipe.')
        return redirect('recipe_detail', recipe_id=recipe.id)

    if request.method == 'POST':
        form = RecipeForm(request.POST, instance=recipe)
        if form.is_valid():
            form.save()
            messages.success(request, 'Recipe updated successfully.')
            return redirect('recipe_detail', recipe_id=recipe.id)
    else:
        form = RecipeForm(instance=recipe)

    return render(request, 'recipes/edit_recipe.html', {'form': form, 'recipe': recipe})


@login_required
def delete_recipe(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)

    # Check if the current user is the creator of the recipe
    if recipe.creator != request.user:
        messages.error(request, 'You are not authorized to delete this recipe.')
        return redirect('recipe_detail', recipe_id=recipe.id)

    if request.method == 'POST':
        recipe.delete()
        messages.success(request, 'Recipe deleted successfully.')
        return redirect('recipe_index')

    return render(request, 'recipes/delete_recipe.html', {'recipe': recipe})

@login_required
def favorite_recipe(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    if recipe.favorites.filter(id=request.user.id).exists():
        recipe.favorites.remove(request.user)  # Unfavorite
    else:
        recipe.favorites.add(request.user)  # Favorite
    return HttpResponseRedirect(reverse('recipe_detail', args=[recipe_id]))