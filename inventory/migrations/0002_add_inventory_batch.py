import datetime
import django.db.models.deletion
from django.db import migrations, models


def migrate_items_to_batches(apps, schema_editor):
    """Copy existing quantity + expiration_date from InventoryItem into InventoryBatch rows."""
    InventoryItem = apps.get_model('inventory', 'InventoryItem')
    InventoryBatch = apps.get_model('inventory', 'InventoryBatch')
    for item in InventoryItem.objects.all():
        qty = item.quantity
        exp = item.expiration_date
        if qty is not None and qty > 0:
            InventoryBatch.objects.create(
                item=item,
                quantity=qty,
                expiration_date=exp,
                date_received=datetime.date.today(),
            )


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0001_initial'),
    ]

    operations = [
        # Step 1: update field help texts / options
        migrations.AlterField(
            model_name='category',
            name='is_infinite',
            field=models.BooleanField(
                default=False,
                help_text='If enabled, items in this category have unlimited quantity and no expiry tracking.'
            ),
        ),
        migrations.AlterField(
            model_name='inventoryitem',
            name='unit',
            field=models.CharField(blank=True, help_text='e.g. bottles, vials, mg', max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='inventorypreference',
            name='expiry_warning_days',
            field=models.PositiveIntegerField(
                default=30,
                help_text='Show an expiry warning when the nearest batch expires within this many days.'
            ),
        ),
        migrations.AlterField(
            model_name='inventorypreference',
            name='low_stock_threshold',
            field=models.PositiveIntegerField(
                default=10,
                help_text='Show a low-stock warning when total quantity is at or below this number.'
            ),
        ),

        # Step 2: create the InventoryBatch table
        migrations.CreateModel(
            name='InventoryBatch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField()),
                ('expiration_date', models.DateField(blank=True, null=True)),
                ('date_received', models.DateField(default=datetime.date.today)),
                ('notes', models.CharField(blank=True, help_text='e.g. supplier, lot number', max_length=255, null=True)),
                ('item', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='batches',
                    to='inventory.inventoryitem'
                )),
            ],
            options={
                'ordering': ['expiration_date', 'date_received'],
            },
        ),

        # Step 3: copy existing qty/expiry data into batches
        migrations.RunPython(migrate_items_to_batches, migrations.RunPython.noop),

        # Step 4: remove old columns from InventoryItem
        migrations.RemoveField(model_name='inventoryitem', name='expiration_date'),
        migrations.RemoveField(model_name='inventoryitem', name='quantity'),
    ]
