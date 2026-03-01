from django.contrib import admin
from .models import Cage, BoardingType, BoardingPet

@admin.register(Cage)
class CageAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_pet_types')
    filter_horizontal = ('pet_types',)

    def get_pet_types(self, obj):
        return ", ".join([pt.name for pt in obj.pet_types.all()])
    get_pet_types.short_description = 'Eligible Pet Types'

@admin.register(BoardingType)
class BoardingTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_per_day')
    filter_horizontal = ('cages',)

@admin.register(BoardingPet)
class BoardingPetAdmin(admin.ModelAdmin):
    list_display = ('pet', 'get_cage_display', 'get_type_display', 'start_date', 'end_date', 'days_stayed', 'discount', 'amount_owed', 'checked_in_by', 'checked_out_by')
    list_filter = ('start_date', 'end_date', 'boarding_type', 'cage', 'checked_in_by', 'checked_out_by')
    search_fields = ('pet__name', 'cage_name', 'boarding_type_name')
    readonly_fields = ('cage_name', 'boarding_type_name', 'price_per_day', 'discount', 'checked_in_by', 'checked_out_by')
    
    def get_cage_display(self, obj):
        return obj.cage.name if obj.cage else f"{obj.cage_name} (Deleted)"
    get_cage_display.short_description = 'Cage'

    def get_type_display(self, obj):
        return obj.boarding_type.name if obj.boarding_type else f"{obj.boarding_type_name} (Deleted)"
    get_type_display.short_description = 'Boarding Type'
