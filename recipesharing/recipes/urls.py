from django.urls import path
from . import views  # Import views from the current directory

urlpatterns = [
    path('', views.index, name='recipe_index'),  # Use index for the main recipe page
    path('<int:recipe_id>/', views.recipe_detail, name='recipe_detail'),
    path('add/', views.add_recipe, name='add_recipe'),  # Add recipe page
    path('<int:recipe_id>/edit/', views.edit_recipe, name='edit_recipe'),
    path('<int:recipe_id>/delete/', views.delete_recipe, name='delete_recipe'),


]
