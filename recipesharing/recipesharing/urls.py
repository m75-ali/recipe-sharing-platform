# recipesharing/urls.py
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from recipes.views import recipe_index  # Import the actual view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('recipes/', include('recipes.urls')),
    path('users/', include('users.urls')),
    path('', recipe_index, name='home'),  # Use the actual view function
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)