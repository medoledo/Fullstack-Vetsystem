from django.db import models
from django.contrib.auth.models import User
from clinics.models import Clinic


class SiteOwnerProfile(models.Model):
    """Platform-wide administrator. Not tied to any clinic."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='siteownerprofile')
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"Site Owner: {self.name}"


class ClinicOwnerProfile(models.Model):
    """Owner / administrator of a specific clinic."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='clinicownerprofile')
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name='clinic_owners')
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"Clinic Owner: {self.name} ({self.clinic.name})"


class DoctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctorprofile')
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name='doctors')
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"Doctor: {self.name} ({self.clinic.name})"


class PetshopProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='petshopprofile')
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name='petshop_staff')
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"Petshop: {self.name} ({self.clinic.name})"
