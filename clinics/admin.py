from django.contrib import admin
from .models import Clinic, SubscriptionPlan, ClinicSubscription


@admin.register(Clinic)
class ClinicAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'phone', 'address')


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'days')
    ordering = ('days',)


@admin.register(ClinicSubscription)
class ClinicSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('clinic', 'plan', 'start_date', 'end_date', 'is_active_display', 'days_remaining_display')
    list_filter = ('plan',)
    search_fields = ('clinic__name',)
    date_hierarchy = 'end_date'

    @admin.display(description='Active', boolean=True)
    def is_active_display(self, obj):
        return obj.is_active

    @admin.display(description='Days Remaining')
    def days_remaining_display(self, obj):
        return obj.days_remaining
