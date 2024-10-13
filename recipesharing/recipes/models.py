from django.db import models

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

    def __str__(self):
        return self.title
