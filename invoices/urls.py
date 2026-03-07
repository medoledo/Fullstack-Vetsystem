from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_invoice, name='create_invoice'),
    path('<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    path('', views.invoice_list, name='invoice_list'),
    path('history/', views.history, name='history'),
    path('api/items/', views.get_inventory_items_json, name='api_inventory_items'),
]
