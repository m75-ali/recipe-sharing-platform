from django.urls import path
from . import views  # Import views from the current directory

urlpatterns = [
    path('', views.index, name='index'),  # Add a basic route
    path('<int:recipe_id>/', views.recipe_detail, name='recipe_detail'),  # Recipe detail page
    path('add/', views.add_recipe, name='add_recipe'),  # Add recipe page


]
