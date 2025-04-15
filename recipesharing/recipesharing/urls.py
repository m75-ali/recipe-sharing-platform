# recipesharing/urls.py
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('recipes/', include('recipes.urls')),  # Recipe-related URLs
    path('users/', include('users.urls')),  # User-related URLs
    # Modify this to redirect to the recipes/ URL pattern instead of a named URL
    path("", lambda request: redirect("recipes/")), 
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)