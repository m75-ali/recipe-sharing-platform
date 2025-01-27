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
from django.db.models import Q
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
    if request.method == "POST":
        form = RecipeForm(request.POST, request.FILES)
        if form.is_valid():
            recipe = form.save(commit=False)
            recipe.creator = request.user
            # Process ingredients: split by commas and save as newline-separated
            recipe.ingredients = "\n".join([ingredient.strip() for ingredient in request.POST['ingredients'].split(",")])
            recipe.save()
            messages.success(request, "Recipe added successfully!")
            return redirect("recipe_index")
        else:
            messages.error(request, f"Form validation errors: {form.errors}")
    else:
        form = RecipeForm()

    categories = Category.objects.all()
    return render(request, "recipes/add_recipe.html", {"form": form, "categories": categories})

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

    # Handle the ingredients field as a comma-separated string
    if isinstance(recipe.ingredients, str):  # If it's a comma-separated string
        ingredients = [ingredient.strip() for ingredient in recipe.ingredients.split(',')]
    else:
        ingredients = []  # In case the ingredients are empty or not in string format

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
        return redirect('recipe_detail', recipe_id=recipe.id)  # Redirect to the recipe details page

    # Handle form submission
    if request.method == 'POST':
        form = RecipeForm(request.POST, instance=recipe)
        if form.is_valid():
            form.save()  # Save the updated recipe
            messages.success(request, 'Recipe updated successfully.')  # Success message
            return redirect('recipe_detail', recipe_id=recipe.id)  # Redirect to the recipe details page
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
def ingredient_search(request):
    results = []
    form = IngredientSearchForm()
    suggestions = set()

    if request.method == 'POST':
        form = IngredientSearchForm(request.POST)
        if form.is_valid():
            user_ingredients = [
                ingredient.strip().lower().strip('"') for ingredient in form.cleaned_data['ingredients'].split(",")
            ]

            # Require a minimum match threshold (e.g., 50% of searched ingredients)
            min_matches_required = max(1, len(user_ingredients) // 2)

            for recipe in Recipe.objects.all():
                if isinstance(recipe.ingredients, str):
                    recipe_ingredients = recipe.ingredients.replace('[', '').replace(']', '').replace('"', '').split(",")
                else:
                    recipe_ingredients = []

                recipe_ingredients = [ingredient.strip().lower() for ingredient in recipe_ingredients]

                matching_ingredients = [
                    ingredient for ingredient in user_ingredients if ingredient in recipe_ingredients
                ]

                # Only include recipes that match the minimum threshold
                if len(matching_ingredients) >= min_matches_required:
                    missing_ingredients = [
                        ingredient for ingredient in recipe_ingredients if ingredient not in user_ingredients
                    ]
                    results.append({
                        'recipe': recipe,
                        'matching_ingredients': matching_ingredients,
                        'missing_ingredients': missing_ingredients,
                    })
                else:
                    for user_ingredient in user_ingredients:
                        close_matches = get_close_matches(user_ingredient, recipe_ingredients, n=3, cutoff=0.6)
                        if close_matches:
                            suggestions.update(close_matches)

    return render(request, 'recipes/ingredient_search.html', {
        'form': form,
        'results': results,
        'suggestions': suggestions,
    })