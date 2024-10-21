from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class Recipe(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    ingredients = models.TextField()
    instructions = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='recipes')
    favorites = models.ManyToManyField(User, related_name='favorite_recipes', blank=True)  # Field to track favorites
    creator = models.ForeignKey(User, on_delete=models.CASCADE)  # Link to User

    def __str__(self):
        return self.title
    
    def total_favorites(self):
        return self.favorites.count()

    # Optional: Calculate average rating of this recipe
    def average_rating(self):
        return self.ratings.aggregate(models.Avg('rating'))['rating__avg'] or 0

class Rating(models.Model):
    recipe = models.ForeignKey(Recipe, related_name='ratings', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField()

    class Meta:
        unique_together = ('user', 'recipe')  # Ensure a user can rate a recipe only once

    def __str__(self):
        return f'{self.recipe.title} rated {self.rating} by {self.user.username}'