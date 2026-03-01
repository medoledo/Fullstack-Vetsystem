from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm
from django import forms
from .models import AdminProfile, DoctorProfile, PetshopProfile

class CustomUserChangeForm(UserChangeForm):
    ROLE_CHOICES = [
        ('', 'No Role / Superuser'),
        ('ADMIN', 'Admin'),
        ('DOCTOR', 'Doctor'),
        ('PETSHOP', 'Petshop'),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=False, label="User Role")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            if hasattr(self.instance, 'adminprofile'):
                self.fields['role'].initial = 'ADMIN'
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
        if hasattr(obj, 'adminprofile'):
            name = obj.adminprofile.name
            phone = obj.adminprofile.phone_number
        elif hasattr(obj, 'doctorprofile'):
            name = obj.doctorprofile.name
            phone = obj.doctorprofile.phone_number
        elif hasattr(obj, 'petshopprofile'):
            name = obj.petshopprofile.name
            phone = obj.petshopprofile.phone_number
            
        AdminProfile.objects.filter(user=obj).delete()
        DoctorProfile.objects.filter(user=obj).delete()
        PetshopProfile.objects.filter(user=obj).delete()
        
        if role == 'ADMIN':
            AdminProfile.objects.create(user=obj, name=name, phone_number=phone)
        elif role == 'DOCTOR':
            DoctorProfile.objects.create(user=obj, name=name, phone_number=phone)
        elif role == 'PETSHOP':
            PetshopProfile.objects.create(user=obj, name=name, phone_number=phone)

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'phone_number')
    search_fields = ('user__username', 'name', 'phone_number')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            from django.contrib.auth.models import User
            # Either it has NO profile at all, or it is the current instance's user
            kwargs["queryset"] = User.objects.filter(
                adminprofile__isnull=True,
                doctorprofile__isnull=True,
                petshopprofile__isnull=True
            )
            # If editing an existing profile, include its own user in the dropdown
            if request.resolver_match and request.resolver_match.kwargs.get('object_id'):
                try:
                    obj_id = request.resolver_match.kwargs.get('object_id')
                    current_user = AdminProfile.objects.get(pk=obj_id).user
                    kwargs["queryset"] = kwargs["queryset"] | User.objects.filter(pk=current_user.pk)
                except AdminProfile.DoesNotExist:
                    pass
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'phone_number')
    search_fields = ('user__username', 'name', 'phone_number')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            from django.contrib.auth.models import User
            kwargs["queryset"] = User.objects.filter(
                adminprofile__isnull=True,
                doctorprofile__isnull=True,
                petshopprofile__isnull=True
            )
            if request.resolver_match and request.resolver_match.kwargs.get('object_id'):
                try:
                    obj_id = request.resolver_match.kwargs.get('object_id')
                    current_user = DoctorProfile.objects.get(pk=obj_id).user
                    kwargs["queryset"] = kwargs["queryset"] | User.objects.filter(pk=current_user.pk)
                except DoctorProfile.DoesNotExist:
                    pass
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(PetshopProfile)
class PetshopProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'phone_number')
    search_fields = ('user__username', 'name', 'phone_number')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            from django.contrib.auth.models import User
            kwargs["queryset"] = User.objects.filter(
                adminprofile__isnull=True,
                doctorprofile__isnull=True,
                petshopprofile__isnull=True
            )
            if request.resolver_match and request.resolver_match.kwargs.get('object_id'):
                try:
                    obj_id = request.resolver_match.kwargs.get('object_id')
                    current_user = PetshopProfile.objects.get(pk=obj_id).user
                    kwargs["queryset"] = kwargs["queryset"] | User.objects.filter(pk=current_user.pk)
                except PetshopProfile.DoesNotExist:
                    pass
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
