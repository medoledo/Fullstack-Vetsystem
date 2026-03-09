from django.db import models
from django.utils import timezone
from datetime import timedelta


class Clinic(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=500, blank=True, null=True)
    logo = models.ImageField(upload_to='clinic_logos/', blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    days = models.PositiveIntegerField(help_text='Duration in days (e.g. 30 for monthly, 365 for yearly)')

    class Meta:
        ordering = ['days']
        verbose_name = 'Subscription Plan'
        verbose_name_plural = 'Subscription Plans'

    def __str__(self):
        return f'{self.name} ({self.days} days – {self.price} EGP)'


class ClinicSubscription(models.Model):
    clinic = models.OneToOneField(Clinic, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name='subscriptions')
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True, help_text='Auto-calculated from start date + plan days. Can be overridden.')

    class Meta:
        ordering = ['end_date']
        verbose_name = 'Clinic Subscription'
        verbose_name_plural = 'Clinic Subscriptions'

    def save(self, *args, **kwargs):
        if not self.end_date and self.start_date and self.plan:
            self.end_date = self.start_date + timedelta(days=self.plan.days)
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        if not self.end_date:
            return False
        return timezone.localdate() <= self.end_date

    @property
    def days_remaining(self):
        if not self.end_date:
            return 0
        delta = (self.end_date - timezone.localdate()).days
        return max(delta, 0)

    def __str__(self):
        return f'{self.clinic.name} – {self.plan.name} (until {self.end_date})'
