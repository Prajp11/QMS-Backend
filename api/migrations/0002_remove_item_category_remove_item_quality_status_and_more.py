# Generated by Django 5.1.1 on 2024-10-14 09:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='item',
            name='category',
        ),
        migrations.RemoveField(
            model_name='item',
            name='quality_status',
        ),
        migrations.RemoveField(
            model_name='item',
            name='received_date',
        ),
        migrations.RemoveField(
            model_name='item',
            name='rejected_reason',
        ),
        migrations.AddField(
            model_name='item',
            name='accepted_or_rejected',
            field=models.CharField(default='Unknown', max_length=50),
        ),
        migrations.AddField(
            model_name='item',
            name='active_ingredient_purity',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='item',
            name='batch_number',
            field=models.CharField(default='Unknown', max_length=100),
        ),
        migrations.AddField(
            model_name='item',
            name='contaminant_level',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='item',
            name='expiry_date',
            field=models.DateField(default='2100-01-01'),
        ),
        migrations.AddField(
            model_name='item',
            name='humidity',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='item',
            name='inspected_by',
            field=models.CharField(default='Unknown', max_length=255),
        ),
        migrations.AddField(
            model_name='item',
            name='manufacture_date',
            field=models.DateField(default='2000-01-01'),
        ),
        migrations.AddField(
            model_name='item',
            name='ph_level',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='item',
            name='supplier',
            field=models.CharField(default='Unknown', max_length=255),
        ),
        migrations.AddField(
            model_name='item',
            name='temperature',
            field=models.FloatField(default=0.0),
        ),
    ]
