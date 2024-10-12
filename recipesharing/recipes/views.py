from django.shortcuts import render, get_object_or_404
from django.shortcuts import redirect
from .forms import RecipeForm
from .models import Recipe

# Create your views here.
def index(request):
    return render(request, 'recipes/index.html')


def index(request):
    recipes = Recipe.objects.all()  # Fetch all recipes from the database
    return render(request, 'recipes/index.html', {'recipes': recipes})

def add_recipe(request):
    if request.method == 'POST':
        form = RecipeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('recipe_index')
    else:
        form = RecipeForm()
    return render(request, 'recipes/add_recipe.html', {'form': form})

def recipe_detail(request, id):
    recipe = get_object_or_404(Recipe, id=id)  # Get the recipe by its ID
    return render(request, 'recipes/recipe_detail.html', {'recipe': recipe})