from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path('maatxt/', views.SimpleView, name='incoming_maa_txt'),
]