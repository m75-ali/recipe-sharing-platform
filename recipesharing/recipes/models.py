from django.db import models
from django.contrib.auth.models import User

# Define a Category model to categorize recipes
class Category(models.Model):
    name = models.CharField(max_length=200)  # Name of the category (e.g., Breakfast, Lunch)

    # Return the category name when it is referenced
    def __str__(self):
        return self.name

# Define a Recipe model to store recipe details
class Recipe(models.Model):
    title = models.CharField(max_length=200)  # Title of the recipe
    description = models.TextField()  # Short description of the recipe
    ingredients = models.TextField()  # List of ingredients for the recipe
    instructions = models.TextField()  # Step-by-step instructions for preparing the recipe
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='recipes')  
    # ForeignKey link to Category, with cascading delete (if the category is deleted, its recipes are too)
    favorites = models.ManyToManyField(User, related_name='favorite_recipes', blank=True)  
    # Many-to-many field to track users who have marked this recipe as a favorite
    creator = models.ForeignKey(User, on_delete=models.CASCADE)  
    # Link the recipe to the user who created it (if the user is deleted, the recipe is deleted too)

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