from django.contrib import admin
from .models import Recipe, Category

admin.site.register(Category)
admin.site.register(Recipe)
