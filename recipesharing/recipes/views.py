from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt  # Add this import
from .forms import RecipeForm
from .models import Recipe, Rating, Category
from django.db.models import Avg
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render
from .models import Recipe, Allergen
from .models import find_recipes_by_ingredients
from .forms import IngredientSearchForm
import random
import json
import re 
from django.db.models import Q
from difflib import get_close_matches
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.shortcuts import render
from django.http import JsonResponse
import json
from .groq_integration import generate_recipe

from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Avg
from django.template.loader import render_to_string
from .models import Recipe, Category, Allergen, Rating

def index(request):
    # Get selected filters from query parameters
    selected_category = request.GET.get('category', None)
    selected_allergens = request.GET.getlist('allergens')  # Gets allergens as a list

    # Start with all recipes
    recipes = Recipe.objects.all()

    # Filter by category if selected
    if selected_category:
        recipes = recipes.filter(category__name=selected_category)

    # Exclude recipes that are allergen-free for selected allergens
    if selected_allergens:
        recipes = recipes.exclude(allergen_free__in=selected_allergens)

    # Calculate average rating for each recipe
    for recipe in recipes:
        average_rating = recipe.ratings.aggregate(Avg('rating'))['rating__avg']
        recipe.average_rating = average_rating if average_rating is not None else None

    # Handle AJAX requests for dynamic filtering
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('recipes/partials/recipe_list.html', {'recipes': recipes})
        return JsonResponse({'html': html})

    # Fetch categories and allergens for dropdowns
    categories = Category.objects.all()
    allergens = Allergen.objects.all()

    return render(request, 'recipes/index.html', {
        'recipes': recipes,
        'categories': categories,
        'allergens': allergens,
        'selected_category': selected_category,
        'selected_allergens': selected_allergens,
    })


# View to add a new recipe (login required)

@login_required
def add_recipe(request):
    if request.method == "POST":
        form = RecipeForm(request.POST, request.FILES)
        if form.is_valid():
            recipe = form.save(commit=False)
            recipe.creator = request.user
            # No need to manually process ingredients here
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
    recipe = get_object_or_404(Recipe, id=recipe_id)

    if recipe.creator != request.user:
        messages.error(request, "You cannot edit someone else's recipe.")
        return redirect('recipe_detail', recipe_id=recipe.id)

    if request.method == 'POST':
        form = RecipeForm(request.POST, request.FILES, instance=recipe)
        if form.is_valid():
            recipe = form.save(commit=False)
            recipe.save()
            form.save_m2m()  # Save many-to-many data
            messages.success(request, 'Recipe updated successfully.')
            return redirect('recipe_detail', recipe_id=recipe.id)
        else:
            # Print form errors for debugging
            print(form.errors)
    else:
        form = RecipeForm(instance=recipe)

    allergens = Allergen.objects.all()
    return render(request, 'recipes/edit_recipe.html', {
        'form': form,
        'recipe': recipe,
        'allergens': allergens,
    })
    
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
    
    
def random_recipe(request):
    # Get all recipe IDs
    recipe_ids = Recipe.objects.values_list('id', flat=True)
    if recipe_ids:
        random_id = random.choice(recipe_ids)
        recipe = get_object_or_404(Recipe, id=random_id)
        return render(request, 'recipes/recipe_detail.html', {'recipe': recipe})  # Adjust template name
    return render(request, 'index.html', {'error': 'No recipes available'})  # Fallback if no recipes exist


def recipe_generator_page(request):
    """Render the recipe generator page"""
    return render(request, 'recipes/recipe_generator.html')

@csrf_exempt
def generate_recipe_api(request):
    """API endpoint to generate a recipe"""
    if request.method == 'POST':
        try:
            # Parse the JSON data from the request
            data = json.loads(request.body)
            
            # Extract ingredients and dietary preferences
            ingredients = data.get('ingredients', [])
            dietary_preferences = data.get('dietary_preferences', None)
            
            # Validate ingredients
            if not ingredients or not isinstance(ingredients, list):
                return JsonResponse({'error': 'Please provide a valid list of ingredients'}, status=400)
            
            # Generate the recipe
            result = generate_recipe(ingredients, dietary_preferences)
            
            if result.get('success', False):
                return JsonResponse({'recipe': result.get('recipe')})
            else:
                return JsonResponse({'error': result.get('error', 'Unknown error')}, status=500)
                
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Only POST requests are supported'}, status=405)