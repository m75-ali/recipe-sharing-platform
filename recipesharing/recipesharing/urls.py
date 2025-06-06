# recipesharing/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect


urlpatterns = [
    path('admin/', admin.site.urls),
    path('recipes/', include('recipes.urls')),  # Recipe-related URLs
    path('users/', include('users.urls')),  # User-related URLs
    path("", lambda request: redirect("recipe_index")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)