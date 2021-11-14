from django.urls import path
from django.contrib.auth import views as auth_views

from . import views


urlpatterns = [
    path("maa/manuel/", views.SimpleView, name='incoming_maa'),
    path("test/", views.SimpleView, name='incoming_maa'),
    path("simple/", views.MyView.as_view(), {'test_phi':'moi', 'addon':'adonphi'}, name='test_simple'),
    path("simple/<int:test>/", views.MyView.as_view(), {'test_phi':'moi', 'addon':'adonphi'}, name='test_simple'),
    path("gone/", views.MyRedirectView.as_view(url='http://localhost:8080/income/simple/'), {'test_phi':'moi', 'addon':'adonphi'}, name='test_redirect'),
    path("gone/<int:test>/", views.MyRedirectView.as_view(), name='test_redirect'),
    path("station/<int:pk>/", views.StationDetailView.as_view(), name='station_detail'),
]