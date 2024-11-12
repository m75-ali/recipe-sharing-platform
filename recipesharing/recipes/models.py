import json
from django.db import models
from django.db.models import JSONField
from django.contrib.auth.models import User
from django.db.models import Q

# Define a Category model to categorize recipes
class Category(models.Model):
    name = models.CharField(max_length=200)  # Name of the category (e.g., Breakfast, Lunch)

    # Return the category name when it is referenced
    def __str__(self):
        return self.name

# Define a Recipe model to store recipe details
class Recipe(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    ingredients = JSONField()  # JSON-encoded list of ingredients
    instructions = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='recipes')
    favorites = models.ManyToManyField(User, related_name='favorite_recipes', blank=True)
    image = models.ImageField(upload_to='recipe_images/', null=True, blank=True)  # New image field
    creator = models.ForeignKey(User, on_delete=models.CASCADE)

    def set_ingredients(self, ingredients_list):
        """Store ingredients list directly without JSON encoding."""
        self.ingredients = ingredients_list

    def get_ingredients(self):
        """Retrieve the list of ingredients from JSON."""
        return json.loads(self.ingredients)
    # Return the title of the recipe when referenced
    def __str__(self):
        return self.title

    # Calculate the total number of users who have favorited the recipe
    def total_favorites(self):
        return self.favorites.count()

    # Optional method to calculate the average rating of the recipe
    def average_rating(self):
        return self.ratings.aggregate(models.Avg('rating'))['rating__avg'] or 0
        # Aggregates the average of all the ratings for this recipe; returns 0 if no ratings exist

# Define a Rating model to store user ratings for recipes
class Rating(models.Model):
    recipe = models.ForeignKey(Recipe, related_name='ratings', on_delete=models.CASCADE)
    # ForeignKey link to Recipe, with cascading delete (if a recipe is deleted, its ratings are too)
    user = models.ForeignKey(User, on_delete=models.CASCADE)  
    # ForeignKey link to User (if a user is deleted, their ratings are deleted too)
    rating = models.PositiveIntegerField()  # Stores the user's rating as a positive integer

    # Ensure that each user can only rate each recipe once
    class Meta:
        unique_together = ('user', 'recipe') 

    # Return a string representing the rating
    def __str__(self):
        return f'{self.recipe.title} rated {self.rating} by {self.user.username}'
    


def find_recipes_by_ingredients(user_ingredients):
    results = []
    all_recipes = Recipe.objects.all()

    for recipe in all_recipes:
        # Split ingredients in recipe, assuming they are comma-separated
        recipe_ingredients = recipe.ingredients.lower().split(", ")
        
        # Calculate the match score based on the intersection
        match_score = len(set(user_ingredients) & set(recipe_ingredients)) / len(user_ingredients)
        
        if match_score > 0:  # Only add recipes with a match
            results.append((recipe, match_score))

    # Sort by match score in descending order to show best matches first
    results.sort(key=lambda x: x[1], reverse=True)
    return results
