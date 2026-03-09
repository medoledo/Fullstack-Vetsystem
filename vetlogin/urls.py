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
    # Siteowner subscription management
    path('subscriptions/', views.subscription_history, name='subscription_history'),
    path('subscriptions/plans/add/', views.add_subscription_plan, name='add_subscription_plan'),
    path('subscriptions/plans/<int:plan_id>/edit/', views.edit_subscription_plan, name='edit_subscription_plan'),
    path('subscriptions/plans/<int:plan_id>/delete/', views.delete_subscription_plan, name='delete_subscription_plan'),
    path('subscriptions/assign/', views.assign_subscription, name='assign_subscription'),
    path('subscriptions/<int:clinic_id>/revoke/', views.revoke_subscription, name='revoke_subscription'),
]
