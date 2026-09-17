# config/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('bagusprasojo/', admin.site.urls),
    path('', include('hpp.urls')),
]
