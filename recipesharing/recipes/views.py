from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from .forms import RecipeForm
from .models import Recipe
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
    recipe = get_object_or_404(Recipe, id=recipe_id)  # Fetch recipe using the 'recipe_id'
    return render(request, 'recipes/recipe_detail.html', {'recipe': recipe})


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