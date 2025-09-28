"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.users.api.urls')),
    path('api/', include('apps.categories.api.urls')),
    path('api/', include('apps.expenses.api.urls')),
    path('api/', include('apps.reports.api.urls')),
    path('api/', include('apps.contributions.urls')),
    path('api/updates/', include('apps.updates.api.urls')),
    path('api-auth/', include('rest_framework.urls')),
]

# Serve static and media files (including when DEBUG=False for development)
from django.views.static import serve
from django.urls import re_path
import os

if not settings.DEBUG:
    # Manually serve static files when DEBUG=False (for development only)
    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
else:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
