from django.contrib import admin
from .models import Owner, Pet, PetType


@admin.register(Owner)
class OwnerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone_number', 'clinic', 'joined_date']
    search_fields = ['name', 'phone_number']
    list_filter = ['clinic']


@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'owner', 'pet_type', 'gender', 'birthdate']
    search_fields = ['code', 'name', 'owner__name']
    list_filter = ['pet_type', 'gender', 'owner__clinic']


@admin.register(PetType)
class PetTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'clinic']
    list_filter = ['clinic']
