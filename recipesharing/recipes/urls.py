from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.index, name='recipe_index'),
    path('add/', views.add_recipe, name='add_recipe'),
    path('<int:recipe_id>/', views.recipe_detail, name='recipe_detail'),
    path('<int:recipe_id>/edit/', views.edit_recipe, name='edit_recipe'),
    path('<int:recipe_id>/delete/', views.delete_recipe, name='delete_recipe'),
    path('login/', auth_views.LoginView.as_view(template_name='user/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]