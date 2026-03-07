from django.urls import path
from . import views

urlpatterns = [
    path('', views.vetlogin, name='vetlogin'),
    path('logout/', views.logout_view, name='logout'),
    path('home/', views.home, name='home'),
    path('users/', views.add_user, name='add_user'),
    path('users/<int:user_id>/edit/', views.edit_user, name='edit_user'),
    path('users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    # Siteowner clinic management
    path('clinics/', views.manage_clinics, name='manage_clinics'),
    path('clinics/add/', views.add_clinic, name='add_clinic'),
    path('clinics/<int:clinic_id>/edit/', views.edit_clinic, name='edit_clinic'),
    path('clinics/<int:clinic_id>/delete/', views.delete_clinic, name='delete_clinic'),
]