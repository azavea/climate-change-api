# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-05-20 15:23


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('climate_data', '0006_auto_20160517_1527'),
    ]

    operations = [
        migrations.AlterField(
            model_name='climatemodel',
            name='name',
            field=models.CharField(max_length=40, unique=True),
        ),
    ]
