from django.urls import path
from . import views

urlpatterns = [
    path('', views.inventory_dashboard, name='inventory_dashboard'),

    # Category
    path('category/add/', views.add_category, name='add_category'),
    path('category/<int:category_id>/edit/', views.edit_category, name='edit_category'),
    path('category/<int:category_id>/delete/', views.delete_category, name='delete_category'),

    # Item
    path('item/add/', views.add_item, name='add_item'),
    path('item/<int:item_id>/edit/', views.edit_item, name='edit_item'),
    path('item/<int:item_id>/delete/', views.delete_item, name='delete_item'),

    # Batch
    path('item/<int:item_id>/batch/add/', views.add_batch, name='add_batch'),
    path('batch/<int:batch_id>/edit/', views.edit_batch, name='edit_batch'),
    path('batch/<int:batch_id>/delete/', views.delete_batch, name='delete_batch'),

    # Preferences
    path('preferences/', views.edit_preferences, name='inventory_preferences'),
]
