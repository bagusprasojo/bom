# config/urls.py
from django.contrib import admin
from django.urls import path, include
from hpp.views import favicon_view

urlpatterns = [
    path('favicon.ico', favicon_view, name='favicon'),
    path('bagusprasojo/', admin.site.urls),
    path('', include('hpp.urls')),
]
