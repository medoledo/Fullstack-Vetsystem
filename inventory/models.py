from django.db import models
from django.utils import timezone
from datetime import timedelta, date
from django.db.models import Sum, Min


class InventoryPreference(models.Model):
    """Singleton — one row only. Holds clinic-wide inventory settings."""
    low_stock_threshold = models.PositiveIntegerField(
        default=10,
        help_text="Show a low-stock warning when total quantity is at or below this number."
    )
    expiry_warning_days = models.PositiveIntegerField(
        default=30,
        help_text="Show an expiry warning when the nearest batch expires within this many days."
    )

    class Meta:
        verbose_name = "Inventory Preference"
        verbose_name_plural = "Inventory Preferences"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # Prevent deletion

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return f"Prefs (low≤{self.low_stock_threshold}, expiry warning {self.expiry_warning_days}d)"


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_infinite = models.BooleanField(
        default=False,
        help_text="If enabled, items in this category have unlimited quantity and no expiry tracking."
    )

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


UNIT_CHOICES = [
    ('bottles', 'Bottles'),
    ('vials', 'Vials'),
    ('mg', 'Milligrams (mg)'),
    ('ml', 'Milliliters (ml)'),
    ('boxes', 'Boxes'),
    ('tablets', 'Tablets'),
    ('capsules', 'Capsules'),
    ('kg', 'Kilograms (kg)'),
    ('g', 'Grams (g)'),
    ('pieces', 'Pieces'),
    ('ampoules', 'Ampoules'),
    ('cans', 'Cans'),
    ('pouches', 'Pouches'),
    ('doses', 'Doses'),
    ('strips', 'Strips'),
    ('syringes', 'Syringes'),
    ('packs', 'Packs'),
]

class InventoryItem(models.Model):
    """Represents a product type. Stock is tracked via InventoryBatch records."""
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='items')
    unit = models.CharField(max_length=50, choices=UNIT_CHOICES, null=True, blank=True, help_text="Select a unit")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(null=True, blank=True)
    date_added = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.category.name})"

    # ── Computed stock properties ────────────────────────────────

    @property
    def total_quantity(self):
        if self.category.is_infinite:
            return None
        agg = self.batches.aggregate(total=Sum('quantity'))
        return agg['total'] or 0

    @property
    def nearest_expiry(self):
        """Returns the soonest expiration_date across all batches, or None."""
        agg = self.batches.filter(expiration_date__isnull=False).aggregate(
            nearest=Min('expiration_date')
        )
        return agg['nearest']

    @property
    def is_low_stock(self):
        if self.category.is_infinite:
            return False
        total = self.total_quantity
        if total is None:
            return False
        prefs = InventoryPreference.get()
        return total <= prefs.low_stock_threshold

    @property
    def expiry_status(self):
        """Returns: 'ok', 'warning', 'expired', or None."""
        if self.category.is_infinite:
            return None
        nearest = self.nearest_expiry
        if not nearest:
            return None
        today = timezone.now().date()
        if nearest < today:
            return 'expired'
        prefs = InventoryPreference.get()
        if nearest <= today + timedelta(days=prefs.expiry_warning_days):
            return 'warning'
        return 'ok'

    def consume(self, quantity):
        """
        FIFO deduction: removes `quantity` units starting from the batch
        with the soonest expiration date. Raises ValueError if insufficient stock.
        """
        if self.category.is_infinite:
            return  # Nothing to track

        available = self.total_quantity
        if available < quantity:
            raise ValueError(
                f"Insufficient stock for '{self.name}': "
                f"requested {quantity}, available {available}."
            )

        remaining = quantity
        for batch in self.batches.filter(quantity__gt=0).order_by('expiration_date', 'date_received'):
            if remaining <= 0:
                break
            if batch.quantity <= remaining:
                remaining -= batch.quantity
                batch.delete()
            else:
                batch.quantity -= remaining
                batch.save()
                remaining = 0


class InventoryBatch(models.Model):
    """One stock lot for an InventoryItem. An item can have many batches."""
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='batches')
    quantity = models.PositiveIntegerField()
    expiration_date = models.DateField(null=True, blank=True)
    date_received = models.DateField(default=date.today)
    notes = models.CharField(max_length=255, null=True, blank=True, help_text="e.g. supplier, lot number")

    class Meta:
        ordering = ['expiration_date', 'date_received']

    def __str__(self):
        exp = self.expiration_date.strftime('%d %b %Y') if self.expiration_date else 'No expiry'
        return f"{self.item.name} — {self.quantity} units (expires {exp})"

    @property
    def expiry_status(self):
        if not self.expiration_date:
            return None
        today = timezone.now().date()
        if self.expiration_date < today:
            return 'expired'
        prefs = InventoryPreference.get()
        if self.expiration_date <= today + timedelta(days=prefs.expiry_warning_days):
            return 'warning'
        return 'ok'
