from django.urls import path
from . import views

urlpatterns = [
    path('pet/<int:pet_id>/', views.pet_visits, name='pet_visits'),
    path('expected/', views.expected_visits, name='expected_visits'),
]
