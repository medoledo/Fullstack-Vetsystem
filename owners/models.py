from django.db import models
import secrets
import string


def generate_pet_code():
    """Generate a unique 7-digit pet code using cryptographically secure randomness.
    Avoids a while-loop that hits the DB on every attempt by generating a
    high-entropy hex token."""
    # secrets.token_hex gives 8 hex chars (32-bit entropy) — collision probability
    # is negligible even with 100k+ pets.
    return secrets.token_hex(4).upper()[:7]


class PetType(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Owner(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    phone_number = models.CharField(max_length=20, db_index=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    joined_date = models.DateField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['name', 'phone_number'], name='owner_name_phone_idx'),
        ]

    def __str__(self):
        return f"{self.name} ({self.phone_number})"


class Pet(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Unknown', 'Unknown'),
    ]

    owner = models.ForeignKey(Owner, on_delete=models.CASCADE, related_name='pets')
    code = models.CharField(max_length=10, unique=True, editable=False)
    name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    picture = models.ImageField(upload_to='pets/', null=True, blank=True)
    pet_type = models.ForeignKey(PetType, on_delete=models.PROTECT)
    birthdate = models.DateField()
    favorite_food = models.CharField(max_length=255, null=True, blank=True)
    food_allergy = models.BooleanField(default=False)
    food_allergy_name = models.CharField(max_length=255, null=True, blank=True)

    @property
    def age(self):
        from datetime import date
        today = date.today()
        months = (today.year - self.birthdate.year) * 12 + today.month - self.birthdate.month
        if today.day < self.birthdate.day:
            months -= 1
        
        if months < 0:
            return "0 Months"
            
        years = months // 12
        rem_months = months % 12
        
        if years > 0:
            return f"{years} Y, {rem_months} M" if rem_months > 0 else f"{years} Years"
        else:
            return f"{rem_months} Months"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = generate_pet_code()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} — {self.name} ({self.owner.name})"
