from django.urls import path
from . import views

urlpatterns = [
    path('', views.boarding_dashboard, name='boarding_dashboard'),
    path('add-cage/', views.add_cage, name='add_cage'),
    path('add-type/', views.add_boarding_type, name='add_boarding_type'),
    path('edit-cage/<int:cage_id>/', views.edit_cage, name='edit_cage'),
    path('delete-cage/<int:cage_id>/', views.delete_cage, name='delete_cage'),
    path('edit-type/<int:type_id>/', views.edit_boarding_type, name='edit_boarding_type'),
    path('delete-type/<int:type_id>/', views.delete_boarding_type, name='delete_boarding_type'),
    path('board-pet/', views.board_pet, name='board_pet'),
    path('end-boarding/<int:boarding_id>/', views.end_boarding, name='end_boarding'),
]
