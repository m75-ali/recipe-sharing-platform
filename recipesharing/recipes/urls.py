from django.urls import path
from django.contrib.auth import views as auth_views
from . import views  # Import views from the current app

# Define the URL patterns for the recipes app
urlpatterns = [
    # URL for the home page (recipe index), handled by the index view
    path('', views.index, name='recipe_index'),

    # URL for adding a new recipe, handled by the add_recipe view
    path('add/', views.add_recipe, name='add_recipe'),

    # URL for viewing the details of a specific recipe, using the recipe's ID, handled by recipe_detail view
    path('<int:recipe_id>/', views.recipe_detail, name='recipe_detail'),

    # URL for editing a specific recipe, using the recipe's ID, handled by edit_recipe view
    path('<int:recipe_id>/edit/', views.edit_recipe, name='edit_recipe'),

    # URL for deleting a specific recipe, using the recipe's ID, handled by delete_recipe view
    path('<int:recipe_id>/delete/', views.delete_recipe, name='delete_recipe'),

    # URL for marking/unmarking a specific recipe as a favorite, using the recipe's ID, handled by favorite_recipe view
    path('<int:recipe_id>/favorite/', views.favorite_recipe, name='favorite_recipe'),

    # URL for the login page, using Django's built-in LoginView, specifying the custom template 'user/login.html'
    path('login/', auth_views.LoginView.as_view(template_name='user/login.html'), name='login'),

    # URL for the logout functionality, using Django's built-in LogoutView
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # URL for searching ingredients, handled by the ingredient_search view
    path('search/', views.ingredient_search, name='ingredient_search'),
    
    # URL for generating random recipes, handled by the random_recipe view
    path('random-recipe/', views.random_recipe, name='random_recipe'),

    # Recipe Generator URLs
    path('ai-recipe-generator/', views.recipe_generator_page, name='recipe_generator_page'),
    path('api/generate-recipe/', views.generate_recipe_api, name='generate_recipe_api'),
]