from django.contrib import admin
from .models import Category, InventoryItem, InventoryPreference

admin.site.register(InventoryPreference)
admin.site.register(Category)
admin.site.register(InventoryItem)
