# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-08 17:57


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('climate_data', '0011_auto_20160603_1305'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='climatedata',
            unique_together=set([('city', 'scenario', 'climate_model', 'year', 'day_of_year')]),
        ),
    ]
