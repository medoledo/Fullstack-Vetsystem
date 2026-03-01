from django.db import models
from django.utils import timezone
from django.conf import settings
from owners.models import Pet

class Visit(models.Model):
    WEIGHT_CHOICES = [
        ('kg', 'Kilogram'),
        ('g', 'Gram'),
    ]
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='visits')
    visit_date = models.DateField(default=timezone.now, db_index=True)
    weight = models.FloatField()
    weight_unit = models.CharField(max_length=2, choices=WEIGHT_CHOICES, default='kg')
    temperature = models.FloatField(null=True, blank=True)
    diagnosis = models.TextField()
    treatment_protocol = models.TextField()
    next_visit_date = models.DateField(null=True, blank=True, db_index=True)
    
    # Audit trail for the creating doctor
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='visits_recorded')
    doctor_name_snapshot = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Visit for {self.pet.name} on {self.visit_date}"
