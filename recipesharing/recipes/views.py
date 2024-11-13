from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from .forms import RecipeForm
from .models import Recipe, Rating, Category
from django.db.models import Avg
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render
from .models import Recipe
from .models import find_recipes_by_ingredients
from .forms import IngredientSearchForm
import json
import re 
from difflib import get_close_matches
from django.http import JsonResponse
from django.template.loader import render_to_string

def index(request):
    # Get the selected category from the query parameters
    selected_category = request.GET.get('category', None)

    # Filter recipes by category or fetch all recipes
    if selected_category:
        recipes = Recipe.objects.filter(category__name=selected_category)
    else:
        recipes = Recipe.objects.all()

    # Calculate average rating for each recipe
    for recipe in recipes:
        average_rating = recipe.ratings.aggregate(Avg('rating'))['rating__avg']
        recipe.average_rating = average_rating if average_rating is not None else None

    # Handle AJAX request
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('recipes/partials/recipe_list.html', {'recipes': recipes})
        return JsonResponse({'html': html})

    # Fetch all categories for the dropdown
    categories = Category.objects.all()

    return render(request, 'recipes/index.html', {
        'recipes': recipes,
        'categories': categories,
        'selected_category': selected_category,
    })

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

import re

def recipe_detail(request, recipe_id):
    # Fetch the recipe by ID or return a 404 error if not found
    recipe = get_object_or_404(Recipe, id=recipe_id)
    user_rating = None  # To store the current user's rating

    # Handle rating submission (if the POST request includes a rating)
    if request.method == 'POST' and 'rating' in request.POST:
        if request.user.is_authenticated:  # Check if the user is logged in
            rating_value = int(request.POST.get('rating'))  # Get the rating from the form
            # Check if the user has already rated the recipe
            rating, created = Rating.objects.get_or_create(user=request.user, recipe=recipe, defaults={'rating': rating_value})

            if not created:
                # Update the rating if the user already rated this recipe
                rating.rating = rating_value
                rating.save()

            messages.success(request, f'Thank you for rating {recipe.title}!')  # Success message
            return redirect('recipe_detail', recipe_id=recipe.id)  # Redirect to the same page
        else:
            # If the user is not authenticated, show a message that they need to log in
            messages.warning(request, 'You must be logged in to rate this recipe.')

    # Check if the user has already rated the recipe
    if request.user.is_authenticated:
        user_rating = Rating.objects.filter(user=request.user, recipe=recipe).first()

    # Calculate the average rating for the recipe
    average_rating = recipe.ratings.aggregate(Avg('rating'))['rating__avg'] or 0

    # Handle the ingredients field to support JSON strings and lists
    if isinstance(recipe.ingredients, str):  # JSON string
        try:
            ingredients = json.loads(recipe.ingredients)
        except json.JSONDecodeError:
            ingredients = []  # Fallback if the JSON string is invalid
    elif isinstance(recipe.ingredients, list):  # Already a list
        ingredients = recipe.ingredients
    else:
        ingredients = []  # Handle unexpected types

    # Process instructions
    if recipe.instructions:
        # Split by lines and remove pre-existing numbering like "1.", "2."
        raw_steps = recipe.instructions.splitlines()
        instructions = [re.sub(r'^\d+\.\s*|\d+\.\s*$', '', step).strip() for step in raw_steps]
    else:
        instructions = []

    # Render the recipe details page
    return render(request, 'recipes/recipe_detail.html', {
        'recipe': recipe,
        'user_rating': user_rating,
        'average_rating': average_rating,
        'ingredients': ingredients,
        'instructions': instructions,  # Pass cleaned instructions as a list
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
        form = RecipeForm(request.POST, request.FILES, instance=recipe)  # Include request.FILES for file uploads
        if form.is_valid():
            form.save()  # Save the updated recipe with the new image if provided
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

@login_required
# views.py
def ingredient_search(request):
    results = []
    form = IngredientSearchForm()
    suggestions = []

    if request.method == 'POST':
        form = IngredientSearchForm(request.POST)
        if form.is_valid():
            user_ingredients = [ingredient.strip().lower() for ingredient in form.cleaned_data['ingredients'].split(",")]
            print("Processed user ingredients for search:", user_ingredients)

            for recipe in Recipe.objects.all():
                print(f"Recipe '{recipe.title}' raw ingredients:", recipe.ingredients)

                # Check if ingredients are JSON-encoded
                if isinstance(recipe.ingredients, str) and recipe.ingredients.startswith("[") and recipe.ingredients.endswith("]"):
                    try:
                        recipe_ingredients = json.loads(recipe.ingredients)  # Parse JSON string to list
                        recipe_ingredients = [ingredient.strip().lower() for ingredient in recipe_ingredients]
                    except json.JSONDecodeError:
                        recipe_ingredients = recipe.ingredients.lower().replace(", ", ",").split(",")
                elif isinstance(recipe.ingredients, list):
                    recipe_ingredients = [ingredient.lower() for ingredient in recipe.ingredients]
                else:
                    recipe_ingredients = recipe.ingredients.lower().replace(", ", ",").split(",")

                print(f"Processed ingredients for recipe '{recipe.title}':", recipe_ingredients)

                # Exact or partial matches
                matching_ingredients = [
                    ingredient for ingredient in user_ingredients
                    if any(ingredient in recipe_ing for recipe_ing in recipe_ingredients)
                ]
                
                if matching_ingredients:
                    missing_ingredients = [ingredient for ingredient in recipe_ingredients if ingredient not in user_ingredients]
                    results.append({
                        'recipe': recipe,
                        'missing_ingredients': missing_ingredients
                    })

                # Collect suggestions for unmatched ingredients
                else:
                    for user_ingredient in user_ingredients:
                        close_matches = get_close_matches(user_ingredient, recipe_ingredients, n=3, cutoff=0.6)
                        if close_matches:
                            suggestions.extend(close_matches)

            print("Recipes matching ingredients and missing ingredients:", results)
            print("Suggested ingredients:", suggestions)

    return render(request, 'recipes/ingredient_search.html', {
        'form': form,
        'results': results,
        'suggestions': set(suggestions),  # Unique suggestions
    })
    
def find_recipes_by_ingredients(user_ingredients):
    matching_recipes = []

    # Retrieve all recipes to check for matching ingredients
    for recipe in Recipe.objects.all():
        # Load the ingredients safely
        recipe_ingredients = recipe.ingredients

        # Check if it's a string or list
        if isinstance(recipe_ingredients, str):
            # Attempt to load as JSON if it's a string
            try:
                recipe_ingredients = json.loads(recipe_ingredients)
            except json.JSONDecodeError:
                # If JSON fails, treat as plain string (fallback)
                recipe_ingredients = recipe_ingredients.lower().split(",")  # Splits by comma if stored as a string
        elif isinstance(recipe_ingredients, list):
            # If it's already a list, just ensure all are lowercased
            recipe_ingredients = [ingredient.lower() for ingredient in recipe_ingredients]
        else:
            # Handle unexpected types (optional logging)
            print(f"Unexpected type for recipe ingredients: {type(recipe_ingredients)}")
            continue  # Skip this recipe if the type is unexpected

        # Convert ingredients to lowercase for case-insensitive matching
        recipe_ingredients = [ingredient.strip().lower() for ingredient in recipe_ingredients]

        # Check if any of the user ingredients match ingredients in the recipe
        if any(user_ingredient in recipe_ingredients for user_ingredient in user_ingredients):
            matching_recipes.append(recipe)

    return matching_recipes