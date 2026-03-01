from django.db import models
from owners.models import Owner
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class AdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='adminprofile')
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=11)

    def __str__(self):
        return f"Admin: {self.name}"

class DoctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctorprofile')
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=11)

    def __str__(self):
        return f"Doctor: {self.name}"

class PetshopProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='petshopprofile')
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=11)

    def __str__(self):
        return f"Petshop: {self.name}"
