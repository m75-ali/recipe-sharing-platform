from django.shortcuts import render, get_object_or_404, redirect
from .forms import RecipeForm
from .models import Recipe
from django.contrib import messages

# Create your views here.
def index(request):
    recipes = Recipe.objects.all()  # Fetch all recipes from the database
    return render(request, 'recipes/index.html', {'recipes': recipes})

def add_recipe(request):
    if request.method == 'POST':
        form = RecipeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('recipe_index')  # Redirect to recipe index or change this to 'recipe_list' if you have that view
    else:
        form = RecipeForm()
    return render(request, 'recipes/add_recipe.html', {'form': form})

def recipe_detail(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)  # Fetch recipe using the 'recipe_id'
    return render(request, 'recipes/recipe_detail.html', {'recipe': recipe})

def edit_recipe(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    if request.method == 'POST':
        form = RecipeForm(request.POST, instance=recipe)
        if form.is_valid():
            form.save()
            return redirect('recipe_detail', recipe_id=recipe.id)
    else:
        form = RecipeForm(instance=recipe)
    return render(request, 'recipes/edit_recipe.html', {'form': form, 'recipe': recipe})

def delete_recipe(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    if request.method == 'POST':
        recipe.delete()
        messages.success(request, f'Recipe "{recipe.title}" was successfully deleted.')
        return redirect('recipe_index')  # Redirect to the recipe index page
    return render(request, 'recipes/delete_recipe.html', {'recipe': recipe})