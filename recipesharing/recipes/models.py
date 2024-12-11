import json
from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    ingredients = models.TextField()  # Stored as a JSON string
    instructions = models.TextField()
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='recipes'
    )
    favorites = models.ManyToManyField(
        User, related_name='favorite_recipes', blank=True
    )
    image = models.ImageField(upload_to='recipe_images/', null=True, blank=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)

    def set_ingredients(self, ingredients_list):
        self.ingredients = json.dumps(ingredients_list)

    def get_ingredients(self):
        return json.loads(self.ingredients) if self.ingredients else []

    def __str__(self):
        return self.title

    def total_favorites(self):
        return self.favorites.count()

    def average_rating(self):
        return self.ratings.aggregate(models.Avg('rating'))['rating__avg'] or 0

    def save(self, *args, **kwargs):
        if isinstance(self.ingredients, list):
            self.ingredients = json.dumps(self.ingredients)
        super().save(*args, **kwargs)


class Rating(models.Model):
    recipe = models.ForeignKey(Recipe, related_name='ratings', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField()

    class Meta:
        unique_together = ('user', 'recipe')

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
