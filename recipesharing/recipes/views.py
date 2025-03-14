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
    Parse AI-generated recipe content to extract structured information
    
    Args:
        content (str): The raw AI-generated recipe text
        
    Returns:
        dict: Dictionary with title, description, instructions
    """
    import re
    
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    result = {
        'title': '',
        'description': '',
        'instructions': content  # Default to full content
    }
    
    # If we have no lines, return default values
    if not lines:
        result['title'] = "Delicious Recipe"
        return result
    
    # First, check if the first line is an introduction
    intro_patterns = [
        r"what an interesting combination", 
        r"here'?s a recipe", 
        r"i've created", 
        r"i'll create",
        r"let me create",
        r"let's create",
        r"you can make",
        r"this recipe",
        r"here'?s how",
        r"delicious way",
        r"brings these"
    ]
    
    is_first_line_intro = any(re.search(pattern, lines[0].lower()) for pattern in intro_patterns)
    
    # If the first line is an introduction, look for a title in the next few lines
    if is_first_line_intro and len(lines) > 1:
        # The best candidate for a title is often the line immediately after the intro
        title_candidate = lines[1]
        
        # Check if this looks like a valid title (not too long, not a regular sentence)
        if len(title_candidate) < 80 and not title_candidate.endswith('.'):
            result['title'] = title_candidate
        else:
            # If the second line doesn't look like a title, look at the next few lines
            for i in range(2, min(5, len(lines))):
                line = lines[i]
                # Stop if we hit a section header
                if any(section in line.lower() for section in ['ingredients:', 'instructions:', 'preparation:']):
                    break
                    
                # Check if this line looks like a title
                if len(line) < 80 and not line.endswith('.') and not line.lower().startswith('this'):
                    result['title'] = line
                    break
            
            # If we still don't have a title, use a fallback
            if not result['title']:
                # Create a title from ingredients if intro mentions them
                if "ingredients" in lines[0].lower():
                    result['title'] = "Recipe with " + ", ".join(lines[0].lower().split("ingredients")[1].strip().split(", ")[:3])
                else:
                    # Use a shortened version of the intro as title
                    words = lines[0].split()
                    if len(words) > 5:
                        result['title'] = " ".join(words[:5]) + "..."
                    else:
                        result['title'] = "Delicious Recipe"
    else:
        # If the first line is not an intro, it might be the title
        if len(lines[0]) < 80 and not lines[0].endswith('.'):
            result['title'] = lines[0]
        else:
            # Look for a title in the next few lines
            title_found = False
            for i in range(1, min(5, len(lines))):
                line = lines[i]
                # Stop if we hit a section header
                if any(section in line.lower() for section in ['ingredients:', 'instructions:', 'preparation:']):
                    break
                    
                # Check if this line looks like a title
                if len(line) < 80 and not line.endswith('.'):
                    result['title'] = line
                    title_found = True
                    break
            
            if not title_found:
                # We couldn't find a good title, use the first line (shortened if needed)
                if len(lines[0]) > 50:
                    result['title'] = " ".join(lines[0].split()[:7]) + "..."
                else:
                    result['title'] = lines[0]
    
    # Clean up the title
    # Remove any leading indicators like "Recipe: "
    result['title'] = re.sub(r'^(recipe|dish|meal):\s*', '', result['title'], flags=re.IGNORECASE)
    # Remove any trailing punctuation
    result['title'] = re.sub(r'[.:!?]+$', '', result['title'])
    
    # Rest of the function for description and instructions stays the same
    # Try to identify description (usually a paragraph after the title line)
    description_lines = []
    description_started = False
    instruction_markers = ['ingredients:', 'instructions:', 'steps:', 'directions:']
    
    title_line_idx = -1
    for i, line in enumerate(lines):
        if line == result['title']:
            title_line_idx = i
            break
    
    # Start looking for description after the title line
    start_idx = title_line_idx + 1 if title_line_idx >= 0 else 1
    
    for i in range(start_idx, len(lines)):
        line_lower = lines[i].lower()
        
        # Stop collecting description if we hit a section header
        if any(marker in line_lower for pattern in instruction_markers for marker in [pattern, pattern.title()]):
            break
            
        # Start collecting description
        if not description_started:
            description_started = True
            
        # Collect description lines
        if description_started:
            description_lines.append(lines[i])
            # Stop at empty line or if line is too short to be part of description
            if not lines[i] or len(lines[i]) < 5:
                break
    
    if description_lines:
        result['description'] = ' '.join(description_lines)
    
    # Try to extract just the instructions part
    instructions_part = []
    ingredients_started = False
    instructions_started = False
    tips_started = False
    
    for line in content.split('\n'):
        line_lower = line.lower().strip()
        
        # Check for ingredients section
        if not ingredients_started and any(marker in line_lower for marker in ['ingredients:', 'ingredients']):
            ingredients_started = True
            instructions_part.append(line)
            continue
            
        # Check for instructions section
        if ingredients_started and not instructions_started and any(marker in line_lower for marker in ['instructions:', 'steps:', 'directions:', 'method:', 'instructions']):
            instructions_started = True
            instructions_part.append(line)
            continue
            
        # Check for tips section
        if instructions_started and any(marker in line_lower for marker in ['tips:', 'variations:', 'tips and variations']):
            tips_started = True
            instructions_part.append("Tips and Variations:")
            continue
        
        # Format tip lines without bullet points
        if tips_started:
            if line.strip() and line.strip()[0] in ['•', '*', '-']:
                tip_text = line.strip()[1:].strip()
                instructions_part.append(tip_text)
            elif line.strip():
                instructions_part.append(line.strip())
            continue
            
        # Add line to instructions if in relevant section
        if ingredients_started:
            instructions_part.append(line)
    
    # If we found instructions section, use it
    if instructions_part:
        result['instructions'] = '\n'.join(instructions_part)
    
    return result

# Then, the complete save_recipe_api function
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
            
            # Parse the AI-generated content to extract structured information
            parsed_content = parse_ai_recipe_content(recipe_content)
            
            # Use parsed content or fallback to provided data
            if parsed_content['title']:
                recipe_title = parsed_content['title']
                
            description = parsed_content['description']
            if not description:
                description = f"AI-generated recipe using {', '.join(ingredients_list[:3])}"
                if len(ingredients_list) > 3:
                    description += f" and {len(ingredients_list) - 3} more ingredients"
            
            # Use the parsed instructions or the full content as fallback
            instructions = parsed_content['instructions']
            
            # Convert ingredients list to newline-separated string as expected by your model
            # Make sure each ingredient is on its own line
            # Replace this part in your save_recipe_api function:

            # Convert ingredients list to newline-separated string as expected by your model
            # Make sure each ingredient is on its own line
            ingredients = ""
            if ingredients_list:
                # First check if ingredients is a proper list of separate items
                if len(ingredients_list) > 1:
                    # Add each ingredient on its own line
                    ingredients = "\n".join(ingredient.strip() for ingredient in ingredients_list if ingredient.strip())
                else:
                    # If there's only one item, it might be a space-separated or comma-separated string
                    # Try to split it properly
                    single_item = ingredients_list[0] if ingredients_list else ""
                    if "," in single_item:
                        # Split by commas
                        split_ingredients = [i.strip() for i in single_item.split(",") if i.strip()]
                        ingredients = "\n".join(split_ingredients)
                    elif len(single_item.split()) > 2:
                        # It's probably multiple ingredients in one string - try to extract from content
                        ingredients = ""  # We'll extract from content below
                    else:
                        # It's a single ingredient
                        ingredients = single_item

                # If we still don't have proper ingredients, try to extract from content
                if not ingredients or (len(ingredients.split("\n")) <= 1 and len(ingredients.split()) > 3):
                    import re

                    # Try to find ingredients section in the content
                    content_lower = recipe_content.lower()
                    ingredients_idx = content_lower.find("ingredients")
                    instructions_idx = content_lower.find("instructions")

                    if ingredients_idx != -1:
                        # Extract text between "ingredients" and "instructions"
                        start_idx = content_lower.find("\n", ingredients_idx) + 1  # Start after "ingredients" heading
                        if start_idx <= 0:  # If newline not found, use the "ingredients" line length
                            start_idx = ingredients_idx + len("ingredients") + 1

                        end_idx = instructions_idx if instructions_idx != -1 else len(recipe_content)

                        # Extract and clean ingredient items
                        ingredient_section = recipe_content[start_idx:end_idx].strip()

                        # Look for list items (numbered or bulleted)
                        ingredient_lines = []
                        for line in ingredient_section.split('\n'):
                            line = line.strip()
                            if not line:
                                continue

                            # Handle bulleted or numbered lists
                            if line.startswith('*') or line.startswith('-') or re.match(r'^\d+\.?\s', line):
                                # Extract the ingredient name without the bullet/number
                                ingredient_text = re.sub(r'^[\*\-\d\.\)]+\s*', '', line)
                                ingredient_lines.append(ingredient_text.strip())
                            elif not line.endswith(':') and not any(section in line.lower() for section in ['ingredients', 'instructions', 'directions', 'steps']):
                                ingredient_lines.append(line)

                        if ingredient_lines:
                            ingredients = "\n".join(ingredient_lines)
                    
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