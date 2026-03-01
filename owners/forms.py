from django import forms
from .models import Owner, Pet, PetType


class OwnerForm(forms.ModelForm):
    class Meta:
        model = Owner
        fields = ['name', 'phone_number', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Owner Name'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address (optional)'}),
        }


class PetForm(forms.ModelForm):
    class Meta:
        model = Pet
        fields = ['name', 'gender', 'picture', 'pet_type', 'birthdate', 'favorite_food', 'food_allergy', 'food_allergy_name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Pet Name'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'pet_type': forms.Select(attrs={'class': 'form-select'}),
            'birthdate': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'favorite_food': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Tuna, Chicken'}),
            'food_allergy': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'foodAllergyCheck'}),
            'food_allergy_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'What are they allergic to?'}),
        }


class PetTypeForm(forms.ModelForm):
    class Meta:
        model = PetType
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Dog, Cat, Parrot'}),
        }