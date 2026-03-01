from django.contrib import admin
from .models import Owner, Pet, PetType


@admin.register(Owner)
class OwnerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone_number', 'joined_date']
    search_fields = ['name', 'phone_number']


@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'owner', 'pet_type', 'gender', 'birthdate']
    search_fields = ['code', 'name', 'owner__name']
    list_filter = ['pet_type', 'gender']


@admin.register(PetType)
class PetTypeAdmin(admin.ModelAdmin):
    list_display = ['name']
