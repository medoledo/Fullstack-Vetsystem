from django.contrib import admin
from .models import Category, InventoryItem, InventoryPreference, InventoryBatch


@admin.register(InventoryPreference)
class InventoryPreferenceAdmin(admin.ModelAdmin):
    list_display = ('clinic', 'low_stock_threshold', 'expiry_warning_days')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'clinic', 'is_infinite')
    list_filter = ('clinic', 'is_infinite')


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'clinic', 'category', 'unit', 'price')
    list_filter = ('clinic', 'category')
    search_fields = ('name',)


@admin.register(InventoryBatch)
class InventoryBatchAdmin(admin.ModelAdmin):
    list_display = ('item', 'quantity', 'expiration_date', 'date_received')
    list_filter = ('item__clinic',)
