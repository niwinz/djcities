# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='City',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('geoname_id', models.IntegerField(blank=True, unique=True, null=True)),
                ('slug', models.SlugField(max_length=200, blank=True)),
                ('name', models.CharField(max_length=200, db_index=True)),
                ('name_std', models.CharField(max_length=200, db_index=True)),
                ('alternate_names', models.TextField(blank=True, null=True, default='')),
                ('latitude', models.DecimalField(blank=True, null=True, decimal_places=5, max_digits=8)),
                ('longitude', models.DecimalField(blank=True, null=True, decimal_places=5, max_digits=8)),
            ],
            options={
                'verbose_name_plural': 'cities',
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('geoname_id', models.IntegerField(blank=True, unique=True, null=True)),
                ('slug', models.SlugField(max_length=200, blank=True)),
                ('name', models.CharField(max_length=200, db_index=True)),
                ('code2', models.CharField(max_length=2, blank=True, unique=True, null=True)),
                ('code3', models.CharField(max_length=3, blank=True, unique=True, null=True)),
                ('continent', models.CharField(max_length=2, choices=[('OC', 'Oceania'), ('EU', 'Europe'), ('AF', 'Africa'), ('NA', 'North America'), ('AN', 'Antarctica'), ('SA', 'South America'), ('AS', 'Asia')], db_index=True)),
                ('tld', models.CharField(max_length=5, blank=True, db_index=True)),
            ],
            options={
                'verbose_name_plural': 'countries',
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('geoname_id', models.IntegerField(blank=True, unique=True, null=True)),
                ('slug', models.SlugField(max_length=200, blank=True)),
                ('name', models.CharField(max_length=200, db_index=True)),
                ('name_std', models.CharField(max_length=200)),
                ('geoname_code', models.CharField(max_length=50, blank=True, null=True, db_index=True)),
                ('is_subregion', models.BooleanField(default=False)),
                ('country', models.ForeignKey(related_name='regions', to='djcities.Country')),
                ('parent', models.ForeignKey(to='djcities.Region', related_name='subregions', null=True, default=None)),
            ],
            options={
                'verbose_name_plural': 'regions/states',
                'verbose_name': 'region/state',
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Timezone',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('country_code', models.CharField(max_length=100)),
                ('name', models.CharField(max_length=200, unique=True)),
                ('gmt_offset', models.CharField(max_length=50)),
                ('country', models.ForeignKey(to='djcities.Country', related_name='timezones', null=True, default=None)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='city',
            name='country',
            field=models.ForeignKey(related_name='cities', to='djcities.Country'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='city',
            name='region',
            field=models.ForeignKey(related_name='cities', blank=True, null=True, to='djcities.Region'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='city',
            name='subregion',
            field=models.ForeignKey(related_name='cities_as_subregion', blank=True, null=True, to='djcities.Region'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='city',
            name='timezone',
            field=models.ForeignKey(to='djcities.Timezone', related_name='cities', null=True, default=None),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='city',
            unique_together=set([('country', 'name')]),
        ),
    ]
