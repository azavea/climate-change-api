# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-12-20 00:56


from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('climate_data', '0035_delete_city_boundary_null_city'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cityboundary',
            name='city',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='boundary', to='climate_data.City'),
        ),
    ]
