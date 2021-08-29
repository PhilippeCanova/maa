"""myproject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

from myproject.apps.site.views import update_profile, create_profile

urlpatterns = [
    path('accounts/login/', auth_views.LoginView.as_view(template_name='core/registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(template_name='core/registration/logged_out.html'), name='logout'),
    path('accounts/update/', update_profile, name='accountsupdate'),
    path('accounts/create/', create_profile, name='accountscreate'),

    path('income/', include('myproject.apps.income.urls'), name='income'),
    path('admin/', admin.site.urls),
    path('', include('myproject.apps.site.urls'), name='accueil'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
