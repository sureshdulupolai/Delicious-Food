from django.urls import path
from . import views

urlpatterns = [
    # ================= Admin / Dev =================
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('invite-member/', views.developer_invite_add, name='dev_invite_add'),
    path('dev/errors/', views.error_dashboard, name='error_dashboard'),
    path('dev/errors/<int:error_id>/resolve/', views.resolve_error, name='resolve_error'),

    # ================= Home / Recipes =================
    path('', views.home, name='home'),
    path('recipes/', views.recipe_list, name='recipe_list'),
    path('recipes/add/', views.recipe_create, name='recipe_create'),
    path('recipes/<slug:slug>/preview/', views.recipe_preview, name='recipe_preview'),
    path('recipes/<slug:slug>/edit/', views.recipe_edit, name='recipe_edit'),
    path('recipes/<slug:slug>/delete/', views.recipe_delete, name='recipe_delete'),
    path('recipes/<slug:slug>/approve/', views.recipe_approve, name='recipe_approve'),
    path('recipes/<slug:slug>/', views.recipe_detail, name='recipe_detail'),
    path('search/', views.search, name='search'),

    # ================= Auth =================
    path('register/', views.register_view, name='register'),
    path('register/developer/', views.register_dev_view, name='register_dev'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
]
