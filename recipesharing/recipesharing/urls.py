# recipesharing/urls.py
from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('recipes/', include('recipes.urls')),  # Recipe-related URLs
    path('users/', include('users.urls')),  # User-related URLs
]
