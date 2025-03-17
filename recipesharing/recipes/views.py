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

    # Handle the ingredients field - properly handle newline-separated ingredients
    if recipe.ingredients:
        # First try to split by newlines (preferred format)
        ingredients = [ingredient.strip() for ingredient in recipe.ingredients.splitlines() if ingredient.strip()]
        
        # If that doesn't work, try comma separation as fallback
        if len(ingredients) <= 1 and ',' in recipe.ingredients:
            ingredients = [ingredient.strip() for ingredient in recipe.ingredients.split(',') if ingredient.strip()]
    else:
        ingredients = []  # In case the ingredients are empty
    
    # Process instructions - more thorough cleaning
    if recipe.instructions:
        # Use the parser to clean the instructions if there's any metadata
        parsed_data = parse_ai_recipe_content(recipe.instructions)
        clean_instructions = parsed_data['clean_content']
        
        # Find the instructions section - look for a line with "Instructions:" or similar
        lines = clean_instructions.splitlines()
        instruction_start_idx = -1
        
        for i, line in enumerate(lines):
            if re.search(r'^\*?\*?Instructions:?\*?\*?$|^\*?\*?Steps:?\*?\*?$|^\*?\*?Directions:?\*?\*?$', 
                        line.strip(), re.IGNORECASE):
                instruction_start_idx = i + 1  # Start after this line
                break
        
        # If we can't find an explicit "Instructions" header, try to find where ingredients end
        if instruction_start_idx == -1:
            for i, line in enumerate(lines):
                if re.search(r'^\*?\*?Ingredients:?\*?\*?$', line.strip(), re.IGNORECASE):
                    # Find where ingredients section ends
                    for j in range(i+1, len(lines)):
                        # If line is empty or looks like a header, it might be the end of ingredients
                        if not lines[j].strip() or re.search(r'^\*?\*?.*:\*?\*?$', lines[j].strip()):
                            instruction_start_idx = j
                            # If it's an empty line, move to the next line
                            if not lines[j].strip():
                                instruction_start_idx += 1
                            break
        
        # If we still can't find a clear start, use the entire content
        if instruction_start_idx == -1 or instruction_start_idx >= len(lines):
            instruction_start_idx = 0
        
        # Extract just the instruction steps
        instruction_lines = lines[instruction_start_idx:]
        instructions = []
        
        for line in instruction_lines:
            line = line.strip()
            
            # Skip empty lines, section headers, or ingredient lines
            if not line or re.search(r'^\*?\*?.*:\*?\*?$', line) or "Ingredient" in line:
                continue
            
            # Completely remove any numbering, including numbers at the beginning
            clean_line = re.sub(r'^\d+[\.\)\-]?\s*', '', line)
            
            # Remove "Step X:" patterns
            clean_line = re.sub(r'^Step\s+\d+:?\s*', '', clean_line, re.IGNORECASE)
            
            # Skip if the line became empty or is just a single character
            if len(clean_line) <= 1:
                continue
                
            # Add to instructions if not empty
            instructions.append(clean_line)
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

def recipe_generator_debug(request):
    """Debug page for recipe generator"""
    return render(request, 'recipes/recipe_generator_debug.html')


@login_required
@csrf_exempt
def save_recipe_api(request):
    """API endpoint to save a generated recipe to the database"""
    if request.method == 'POST':
        try:
            # Parse the JSON data from the request
            data = json.loads(request.body)
            
            # Extract recipe data
            recipe_title = data.get('title', 'Untitled Recipe')
            recipe_content = data.get('content', '')
            ingredients_list = data.get('ingredients', [])
            dietary_preference = data.get('dietary_preference', '')
            
            # Extract description from recipe content (first paragraph or default)
            # This is a basic extraction - you might want to improve this logic
            description_lines = [line.strip() for line in recipe_content.split('\n') if line.strip()]
            description = description_lines[0] if description_lines else "AI-generated recipe based on your ingredients."
            
            # Convert ingredients list to newline-separated string (as expected by your model)
            ingredients = "\n".join(ingredients_list)
            
            # Extract instructions from recipe content
            # This is a simplified approach - you might need to adjust based on your AI's output format
            instructions = recipe_content
            
            # Get default category (you might want to add logic to determine the right category)
            try:
                category = Category.objects.get(name="Other")
            except Category.DoesNotExist:
                # Create a default category if it doesn't exist
                category = Category.objects.create(name="Other")
                
            # Create a new Recipe instance
            recipe = Recipe(
                title=recipe_title,
                description=description,
                ingredients=ingredients,
                instructions=instructions,
                category=category,
                creator=request.user,
                # No image for AI-generated recipes by default
            )
            
            # Save the recipe
            recipe.save()
            
            # Handle allergens based on dietary preference if needed
            if dietary_preference:
                if dietary_preference == "gluten-free":
                    try:
                        gluten_allergen = Allergen.objects.get(name="Gluten")
                        recipe.allergen_free.add(gluten_allergen)
                    except Allergen.DoesNotExist:
                        pass
                elif dietary_preference == "dairy-free":
                    try:
                        dairy_allergen = Allergen.objects.get(name="Dairy")
                        recipe.allergen_free.add(dairy_allergen)
                    except Allergen.DoesNotExist:
                        pass
                # Add similar handlers for other dietary preferences
            
            return JsonResponse({
                'success': True, 
                'message': 'Recipe saved successfully',
                'recipe_id': recipe.id
            })
                
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Only POST requests are supported'}, status=405)

def parse_ai_recipe_content(content):
    """
    Parse AI-generated recipe content and extract metadata while removing it from the final display
    
    Args:
        content (str): The raw AI-generated recipe text
        
    Returns:
        dict: Dictionary with title, clean content, category, and allergens
    """
    import re
    
    # Initialize results dictionary
    result = {
        'title': '',
        'category': 'Other',
        'allergens': [],
        'prep_time': '',
        'cook_time': '',
        'difficulty': '',
        'servings': '',
        'clean_content': ''
    }
    
    # Extract title - look for **TITLE** format
    title_match = re.search(r'\*\*(.*?)\*\*', content)
    if title_match:
        result['title'] = title_match.group(1).strip()
    
    # Find metadata section boundaries
    metadata_pattern = re.compile(r'\*\*METADATA\*\*(.*?)(?=\*\*Ingredients|\*\*INGREDIENTS|\Z)', re.DOTALL | re.IGNORECASE)
    metadata_match = metadata_pattern.search(content)
    
    if metadata_match:
        # We found a clearly marked metadata section
        metadata_text = metadata_match.group(1).strip()
        metadata_start = content.find('**METADATA**')
        metadata_end = metadata_start + len('**METADATA**') + len(metadata_text)
        
        # Extract metadata fields
        category_match = re.search(r'Category:\s*(.*?)(?:\n|$)', metadata_text, re.IGNORECASE)
        if category_match:
            result['category'] = category_match.group(1).strip()
        
        allergens_match = re.search(r'Allergens:\s*(.*?)(?:\n|$)', metadata_text, re.IGNORECASE)
        if allergens_match:
            allergens_text = allergens_match.group(1).strip()
            if allergens_text.lower() not in ['none', 'n/a']:
                allergens = re.split(r',|\sand\s|;', allergens_text)
                result['allergens'] = [a.strip() for a in allergens if a.strip()]
        
        prep_time_match = re.search(r'Prep Time:\s*(.*?)(?:\n|$)', metadata_text, re.IGNORECASE)
        if prep_time_match:
            result['prep_time'] = prep_time_match.group(1).strip()
            
        cook_time_match = re.search(r'Cook Time:\s*(.*?)(?:\n|$)', metadata_text, re.IGNORECASE)
        if cook_time_match:
            result['cook_time'] = cook_time_match.group(1).strip()
            
        difficulty_match = re.search(r'Difficulty:\s*(.*?)(?:\n|$)', metadata_text, re.IGNORECASE)
        if difficulty_match:
            result['difficulty'] = difficulty_match.group(1).strip()
            
        servings_match = re.search(r'Servings:\s*(.*?)(?:\n|$)', metadata_text, re.IGNORECASE)
        if servings_match:
            result['servings'] = servings_match.group(1).strip()
        
        # Remove the entire metadata section from content
        content_before = content[:metadata_start].strip()
        content_after = content[metadata_end:].strip()
        
        # Combine parts ensuring proper spacing
        if content_before and content_after:
            result['clean_content'] = content_before + "\n\n" + content_after
        elif content_after:
            result['clean_content'] = content_after
        else:
            result['clean_content'] = content_before
    else:
        # No clearly marked metadata section, look for individual metadata lines
        lines = content.split('\n')
        metadata_lines = []
        
        for i, line in enumerate(lines):
            # Check for common metadata patterns
            if re.search(r'^Category:', line, re.IGNORECASE):
                metadata_lines.append(i)
                category_value = line.split(':', 1)[1].strip()
                result['category'] = category_value
            elif re.search(r'^Allergens:', line, re.IGNORECASE):
                metadata_lines.append(i)
                allergens_text = line.split(':', 1)[1].strip()
                if allergens_text.lower() not in ['none', 'n/a']:
                    allergens = re.split(r',|\sand\s|;', allergens_text)
                    result['allergens'] = [a.strip() for a in allergens if a.strip()]
            elif re.search(r'^Prep Time:', line, re.IGNORECASE):
                metadata_lines.append(i)
                result['prep_time'] = line.split(':', 1)[1].strip()
            elif re.search(r'^Cook Time:', line, re.IGNORECASE):
                metadata_lines.append(i)
                result['cook_time'] = line.split(':', 1)[1].strip()
            elif re.search(r'^Difficulty:', line, re.IGNORECASE):
                metadata_lines.append(i)
                result['difficulty'] = line.split(':', 1)[1].strip()
            elif re.search(r'^Servings:', line, re.IGNORECASE):
                metadata_lines.append(i)
                result['servings'] = line.split(':', 1)[1].strip()
        
        # Remove metadata lines from content
        if metadata_lines:
            clean_lines = [line for i, line in enumerate(lines) if i not in metadata_lines]
            result['clean_content'] = '\n'.join(clean_lines)
        else:
            # If no metadata found, use original content
            result['clean_content'] = content
    
    # If still no clean content, use original
    if not result['clean_content']:
        result['clean_content'] = content
    
    return result
    

def map_category_to_db_category(category_name):
    """
    Maps an AI-generated category to one of the fixed categories in the database
    
    Args:
        category_name (str): Category name from the AI
        
    Returns:
        str: Mapped category name matching one in the database
    """
    category_name = category_name.lower().strip()
    
    # Direct matches for common categories
    category_mapping = {
        'breakfast': 'Breakfast',
        'brunch': 'Breakfast',
        'lunch': 'Lunch',
        'dinner': 'Dinner',
        'main': 'Dinner',
        'main course': 'Dinner',
        'main dish': 'Dinner',
        'dessert': 'Dessert',
        'appetizer': 'Appetizer',
        'starter': 'Appetizer',
        'snack': 'Snack',
        'side': 'Side',
        'side dish': 'Side'
    }
    
    # Check for direct matches
    for key, value in category_mapping.items():
        if key == category_name:
            return value
    
    # Check for partial matches
    for key, value in category_mapping.items():
        if key in category_name:
            return value
    
    # Default to 'Other' if no match
    return 'Other'

def map_allergens_to_db_allergens(allergens_list):
    """
    Maps AI-identified allergens to database allergen names
    
    Args:
        allergens_list (list): List of allergen strings from AI
        
    Returns:
        list: List of standardized allergen names
    """
    # Common allergen mappings to standardized names
    allergen_mapping = {
        'milk': 'Milk',
        'dairy': 'Milk',
        'lactose': 'Milk',
        
        'eggs': 'Eggs',
        'egg': 'Eggs',
        
        'fish': 'Fish',
        
        'shellfish': 'Shellfish',
        'shrimp': 'Shellfish',
        'crab': 'Shellfish',
        'lobster': 'Shellfish',
        
        'tree nuts': 'Tree nuts',
        'nuts': 'Tree nuts',
        'almonds': 'Tree nuts',
        'walnuts': 'Tree nuts',
        'cashews': 'Tree nuts',
        'pecans': 'Tree nuts',
        'pistachios': 'Tree nuts',
        
        'peanuts': 'Peanuts',
        'peanut': 'Peanuts',
        
        'wheat': 'Wheat',
        'gluten': 'Wheat',
        
        'soybeans': 'Soybeans',
        'soy': 'Soybeans',
        
        'sesame': 'Sesame',
        'sesame seeds': 'Sesame'
    }
    
    standardized_allergens = []
    
    for allergen in allergens_list:
        allergen_lower = allergen.lower().strip()
        matched = False
        
        # Check exact match first
        if allergen_lower in allergen_mapping:
            standardized_allergens.append(allergen_mapping[allergen_lower])
            matched = True
        else:
            # Check for partial matches
            for key, value in allergen_mapping.items():
                if key in allergen_lower:
                    standardized_allergens.append(value)
                    matched = True
                    break
        
        # If no match found, use original with first letter capitalized
        if not matched and allergen.strip():
            standardized_allergens.append(allergen.strip().capitalize())
    
    # Remove duplicates and return
    return list(set(standardized_allergens))


@login_required
@csrf_exempt
def save_recipe_api(request):
    if request.method == 'POST':
        try:
            # Parse request data
            data = json.loads(request.body)
            
            # Extract recipe data
            recipe_title = data.get('title', 'Untitled Recipe')
            recipe_content = data.get('content', '')
            ingredients_list = data.get('ingredients', [])
            dietary_preference = data.get('dietary_preference', '')
            
            # Parse metadata and clean content
            parsed_data = parse_ai_recipe_content(recipe_content)
            if parsed_data['title']:
                recipe_title = parsed_data['title']
            
            # Use clean content (metadata removed)
            clean_content = parsed_data['clean_content']
            
            # Basic description
            description = f"Recipe using {', '.join(ingredients_list[:3])}"
            if len(ingredients_list) > 3:
                description += f" and more"
            
            # Format ingredients
            ingredients = "\n".join(ingredients_list)
            
            # Determine category - focus on specific keywords
            category_lower = parsed_data['category'].lower()
            
            # Simple direct matching
            if "breakfast" in category_lower:
                category = Category.objects.get(name="Breakfast")
            elif "lunch" in category_lower:
                category = Category.objects.get(name="Lunch")
            elif "dinner" in category_lower or "main" in category_lower:
                category = Category.objects.get(name="Dinner")
            elif "dessert" in category_lower:
                category = Category.objects.get(name="Dessert")
            elif "snack" in category_lower:
                category = Category.objects.get(name="Snack")
            else:
                category = Category.objects.get(name="Other")
            
            # Create recipe
            recipe = Recipe(
                title=recipe_title,
                description=description,
                ingredients=ingredients,
                instructions=clean_content,
                category=category,
                creator=request.user,
            )
            recipe.save()
            
            # Simple, direct allergen check based on parsed allergens
            recipe_allergens = [a.lower() for a in parsed_data['allergens']]
            
            # Only set specific allergen-free flags when we know for sure
            allergen_map = {
                "milk": ["milk", "dairy"],
                "eggs": ["egg", "eggs"],
                "fish": ["fish"],
                "shellfish": ["shellfish", "crab", "shrimp", "lobster"],
                "tree nuts": ["tree nuts", "nuts", "almond", "walnut"],
                "peanuts": ["peanut", "peanuts"],
                "wheat": ["wheat", "gluten"],
                "soybeans": ["soy", "soybeans"],
                "sesame": ["sesame"]
            }
            
            # Get all available allergens
            all_allergens = Allergen.objects.all()
            
            # Only mark allergens as "free from" if they're not in the ingredients or metadata
            for allergen in all_allergens:
                # Check if this allergen is mentioned in the recipe's allergens
                is_in_recipe = False
                for term in allergen_map.get(allergen.name.lower(), []):
                    if any(term in a_item for a_item in recipe_allergens):
                        is_in_recipe = True
                        break
                
                # If the allergen is not in the recipe, mark as allergen-free
                if not is_in_recipe:
                    recipe.allergen_free.add(allergen)
            
            # Return success
            return JsonResponse({
                'success': True, 
                'message': 'Recipe saved successfully',
                'recipe_id': recipe.id
            })
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Only POST requests are supported'}, status=405)