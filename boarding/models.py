from django.db import models
from django.utils import timezone
from owners.models import Pet, PetType

class Cage(models.Model):
    name = models.CharField(max_length=50, unique=True)
    pet_types = models.ManyToManyField(PetType, related_name='cages', blank=True)

    def __str__(self):
        return self.name

class BoardingType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    cages = models.ManyToManyField(Cage, related_name='boarding_types')
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} - ${self.price_per_day}/day"

class BoardingPet(models.Model):
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='boardings')
    cage = models.ForeignKey(Cage, on_delete=models.SET_NULL, null=True, related_name='boardings')
    boarding_type = models.ForeignKey(BoardingType, on_delete=models.SET_NULL, null=True)
    start_date = models.DateField(default=timezone.now, db_index=True)
    end_date = models.DateField(null=True, blank=True, db_index=True)
    
    # Tracking
    checked_in_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='boardings_checked_in')
    checked_out_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='boardings_checked_out')
    
    # Snapshots for historical integrity if cages/packages are edited or deleted
    cage_name = models.CharField(max_length=50, blank=True, null=True)
    boarding_type_name = models.CharField(max_length=100, blank=True, null=True)
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        if self.cage and not self.cage_name:
            self.cage_name = self.cage.name
        if self.boarding_type and not self.boarding_type_name:
            self.boarding_type_name = self.boarding_type.name
        if self.boarding_type and not self.price_per_day:
            self.price_per_day = self.boarding_type.price_per_day
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.pet.name} boarding from {self.start_date}"
    
    @property
    def days_stayed(self):
        if self.end_date:
            delta = (self.end_date - self.start_date).days + 1
            return max(delta, 1)  # Minimum 1 day charge
        return None
        
    @property
    def get_cage_name(self):
        if self.cage_name:
            return self.cage_name
        return self.cage.name if self.cage else "Unknown Cage"

    @property
    def get_boarding_type_name(self):
        if self.boarding_type_name:
            return self.boarding_type_name
        return self.boarding_type.name if self.boarding_type else "Unknown Package"
        
    @property
    def get_price_per_day(self):
        if self.price_per_day is not None:
            return self.price_per_day
        return self.boarding_type.price_per_day if self.boarding_type else 0

    @property
    def get_checked_in_by_name(self):
        if not self.checked_in_by:
            return None
        u = self.checked_in_by
        if hasattr(u, 'adminprofile'):
            return u.adminprofile.name
        if hasattr(u, 'doctorprofile'):
            return u.doctorprofile.name
        if hasattr(u, 'petshopprofile'):
            return u.petshopprofile.name
        return u.username

    @property
    def get_checked_out_by_name(self):
        if not self.checked_out_by:
            return None
        u = self.checked_out_by
        if hasattr(u, 'adminprofile'):
            return u.adminprofile.name
        if hasattr(u, 'doctorprofile'):
            return u.doctorprofile.name
        if hasattr(u, 'petshopprofile'):
            return u.petshopprofile.name
        return u.username
    
    @property
    def total_before_discount(self):
        days = self.days_stayed
        price = self.get_price_per_day
        if days and price:
            return days * price
        return 0

    @property
    def amount_owed(self):
        days = self.days_stayed
        price = self.get_price_per_day
        if days and price:
            return (days * price) - self.discount
        return None
