# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-08-03 15:20


import climate_data.models
import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion


def forwards(apps, schema_editor):
    if not schema_editor.connection.alias == 'default':
        return

    # Remove any existing data to avoid foreign key errors
    ClimateData = apps.get_model('climate_data', 'ClimateData')
    ClimateDataSource = apps.get_model('climate_data', 'ClimateDataSource')
    ClimateData.objects.all().delete()
    ClimateDataSource.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('climate_data', '0017_city__geog'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClimateDataCell',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lat', models.DecimalField(decimal_places=3, max_digits=6)),
                ('lon', models.DecimalField(decimal_places=3, max_digits=6))
            ],
        ),
        migrations.RunPython(forwards),
        migrations.AddField(
            model_name='climatedata',
            name='map_cell',
            field=climate_data.models.TinyForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='climate_data.ClimateDataCell'),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='climatedata',
            unique_together=set([('map_cell', 'data_source', 'day_of_year')]),
        ),
        migrations.RemoveField(
            model_name='climatedata',
            name='city',
        ),
        migrations.AddField(
            model_name='city',
            name='map_cell',
            field=climate_data.models.TinyForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='climate_data.ClimateDataCell'),
        ),
        migrations.AlterUniqueTogether(
            name='climatedatacell',
            unique_together=set([('lat', 'lon')]),
        ),
    ]
