from django.contrib import admin
from .models import Invoice, InvoiceItem


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0
    readonly_fields = ('line_total',)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('reference', 'clinic', 'source', 'customer_name', 'total_amount', 'created_by', 'created_at')
    list_filter = ('clinic', 'source', 'created_at')
    search_fields = ('reference', 'customer_name')
    inlines = [InvoiceItemInline]
    readonly_fields = ('reference', 'total_amount')
