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
    favorites = models.ManyToManyField(User, related_name='favorite_recipes', blank=True)  # New field to track likes
    creator = models.ForeignKey(User, on_delete=models.CASCADE)  # Link to User


    def __str__(self):
        return self.title
    
    def total_favorites(self):
        return self.favorites.count()
