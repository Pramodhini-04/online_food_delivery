# Generated by Django 5.2 on 2025-05-13 06:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0017_orderitem_placed_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='placedorder',
            name='total_price',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
    ]
