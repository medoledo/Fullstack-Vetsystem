from django.contrib import admin
from .models import Visit

@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ('pet', 'visit_date', 'weight', 'next_visit_date', 'doctor')
    search_fields = ('pet__name', 'diagnosis', 'treatment_protocol')
    list_filter = ('visit_date', 'next_visit_date', 'pet__owner__clinic')
