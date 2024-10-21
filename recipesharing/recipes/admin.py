from django.contrib import admin
from .models import Recipe, Category

# Register the Category model with the Django admin site
admin.site.register(Category)

# Register the Recipe model with the Django admin site
admin.site.register(Recipe)