import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from clinics.models import Clinic
from inventory.models import InventoryItem


class Invoice(models.Model):
    """A sales invoice for a clinic or petshop."""

    SOURCE_CHOICES = [
        ('clinic', 'Clinic Inventory'),
        ('petshop', 'Petshop'),
        ('boarding', 'Boarding'),
        ('visit', 'Visit / Consultation'),
        ('other', 'Other'),
    ]

    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name='invoices')
    reference = models.CharField(max_length=20, unique=True, editable=False)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='clinic')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='invoices_created')
    customer_name = models.CharField(max_length=200, blank=True, default='Walk-in Customer')
    notes = models.TextField(blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"INV-{self.reference} ({self.get_source_display()})"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self._generate_reference()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_reference():
        """Generate a unique short reference like INV-A3F8K2."""
        return uuid.uuid4().hex[:8].upper()

    def recalculate_total(self):
        """Recalculate total from line items."""
        self.total_amount = sum(item.line_total for item in self.items.all())
        self.save(update_fields=['total_amount'])

    @property
    def creator_name(self):
        if not self.created_by:
            return 'System'
        from vetlogin.templatetags.role_tags import profile_name
        return profile_name(self.created_by)


class InvoiceItem(models.Model):
    """A single line item on an invoice."""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    inventory_item = models.ForeignKey(
        InventoryItem, on_delete=models.SET_NULL,
        null=True, blank=True,
        help_text="Link to inventory item for automatic stock deduction"
    )
    name = models.CharField(max_length=200, help_text="Product/service name")
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2, editable=False, default=0)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.name} x{self.quantity}"

    def save(self, *args, **kwargs):
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)
