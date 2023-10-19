from django.urls import path, re_path
from .views import LeaguePrediction
from . import views

urlpatterns = [
    path('leagueprediction/<str:league>/', LeaguePrediction.as_view(), name="leagueprediction"),
    re_path('login', views.login),
    re_path('signup', views.signup),
    re_path('auth-token', views.auth_token),
]