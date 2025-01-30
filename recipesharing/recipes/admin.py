from django.contrib import admin
from .models import Recipe, Category , Allergen

# Register the Category model with the Django admin site
admin.site.register(Category)

# Register the Recipe model with the Django admin site
admin.site.register(Recipe)

# Register the Allergen model with the Django admin site
admin.site.register(Allergen)