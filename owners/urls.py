from django.urls import path
from . import views

urlpatterns = [
    path('', views.owners, name='owners'),
    path('add/', views.add_owner, name='add_owner'),
    path('<int:owner_id>/', views.owner_detail, name='owner_detail'),
    path('<int:owner_id>/edit/', views.edit_owner, name='edit_owner'),
    path('<int:owner_id>/delete/', views.delete_owner, name='delete_owner'),
    path('download/', views.download_owners, name='download_owners'),
    path('birthdays/', views.todays_birthdays, name='todays_birthdays'),

    # AJAX endpoints
    path('api/search/', views.api_search_owners, name='api_search_owners'),
    path('api/<int:owner_id>/pets/', views.api_get_owner_pets, name='api_get_owner_pets'),

    # Pet types
    path('pet-types/', views.pet_types, name='pet_types'),
    path('pet-types/<int:type_id>/delete/', views.delete_pet_type, name='delete_pet_type'),

    # Pets
    path('<int:owner_id>/pets/add/', views.add_pet, name='add_pet'),
    path('pets/<int:pet_id>/', views.pet_detail, name='pet_detail'),
    path('pets/<int:pet_id>/edit/', views.edit_pet, name='edit_pet'),
    path('pets/<int:pet_id>/delete/', views.delete_pet, name='delete_pet'),
]
