from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('recipes/', views.recipe_list, name='recipe_list'),
    path('recipes/add/', views.recipe_create, name='recipe_create'),
    path('recipes/<slug:slug>/', views.recipe_detail, name='recipe_detail'),
    path('recipes/<slug:slug>/preview/', views.recipe_preview, name='recipe_preview'),
    path('recipes/<slug:slug>/edit/', views.recipe_edit, name='recipe_edit'),
    path('recipes/<slug:slug>/delete/', views.recipe_delete, name='recipe_delete'),
    path('recipes/<slug:slug>/approve/', views.recipe_approve, name='recipe_approve'),
    path('search/', views.search, name='search'),
    path('register/', views.register_view, name='register'),
    path('register-dev/', views.register_dev_view, name='register_dev'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
]
