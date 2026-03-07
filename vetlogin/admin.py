from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm
from django import forms
from .models import SiteOwnerProfile, ClinicOwnerProfile, DoctorProfile, PetshopProfile

class CustomUserChangeForm(UserChangeForm):
    ROLE_CHOICES = [
        ('', 'No Role / Superuser'),
        ('SITEOWNER', 'Site Owner'),
        ('CLINIC_OWNER', 'Clinic Owner'),
        ('DOCTOR', 'Doctor'),
        ('PETSHOP', 'Petshop'),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=False, label="User Role")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            if hasattr(self.instance, 'siteownerprofile'):
                self.fields['role'].initial = 'SITEOWNER'
            elif hasattr(self.instance, 'clinicownerprofile'):
                self.fields['role'].initial = 'CLINIC_OWNER'
            elif hasattr(self.instance, 'doctorprofile'):
                self.fields['role'].initial = 'DOCTOR'
            elif hasattr(self.instance, 'petshopprofile'):
                self.fields['role'].initial = 'PETSHOP'

class CustomUserAdmin(BaseUserAdmin):
    form = CustomUserChangeForm
    
    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        fieldsets = super().get_fieldsets(request, obj)
        return fieldsets + (
            ('Profile Information', {'fields': ('role',)}),
        )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        
        role = form.cleaned_data.get('role')
        
        name = ''
        phone = ''
        clinic = None
        if hasattr(obj, 'siteownerprofile'):
            name = obj.siteownerprofile.name
            phone = obj.siteownerprofile.phone_number or ''
        elif hasattr(obj, 'clinicownerprofile'):
            name = obj.clinicownerprofile.name
            phone = obj.clinicownerprofile.phone_number or ''
            clinic = obj.clinicownerprofile.clinic
        elif hasattr(obj, 'doctorprofile'):
            name = obj.doctorprofile.name
            phone = obj.doctorprofile.phone_number or ''
            clinic = obj.doctorprofile.clinic
        elif hasattr(obj, 'petshopprofile'):
            name = obj.petshopprofile.name
            phone = obj.petshopprofile.phone_number or ''
            clinic = obj.petshopprofile.clinic
            
        SiteOwnerProfile.objects.filter(user=obj).delete()
        ClinicOwnerProfile.objects.filter(user=obj).delete()
        DoctorProfile.objects.filter(user=obj).delete()
        PetshopProfile.objects.filter(user=obj).delete()
        
        if role == 'SITEOWNER':
            SiteOwnerProfile.objects.create(user=obj, name=name, phone_number=phone)
        elif role == 'CLINIC_OWNER' and clinic:
            ClinicOwnerProfile.objects.create(user=obj, name=name, phone_number=phone, clinic=clinic)
        elif role == 'DOCTOR' and clinic:
            DoctorProfile.objects.create(user=obj, name=name, phone_number=phone, clinic=clinic)
        elif role == 'PETSHOP' and clinic:
            PetshopProfile.objects.create(user=obj, name=name, phone_number=phone, clinic=clinic)

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(SiteOwnerProfile)
class SiteOwnerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'phone_number')
    search_fields = ('user__username', 'name', 'phone_number')

@admin.register(ClinicOwnerProfile)
class ClinicOwnerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'clinic', 'phone_number')
    search_fields = ('user__username', 'name', 'phone_number')
    list_filter = ('clinic',)

@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'clinic', 'phone_number')
    search_fields = ('user__username', 'name', 'phone_number')
    list_filter = ('clinic',)

@admin.register(PetshopProfile)
class PetshopProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'clinic', 'phone_number')
    search_fields = ('user__username', 'name', 'phone_number')
    list_filter = ('clinic',)
