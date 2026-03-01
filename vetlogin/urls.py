from django.urls import path
from . import views

urlpatterns = [
    path('', views.vetlogin, name='vetlogin'),
    path('logout/', views.logout_view, name='logout'),
    path('home/', views.home, name='home'),
    path('users/', views.add_user, name='add_user'),
    path('users/<int:user_id>/edit/', views.edit_user, name='edit_user'),
    path('users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
]