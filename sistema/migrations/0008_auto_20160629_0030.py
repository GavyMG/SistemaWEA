# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sistema', '0007_auto_20160627_2143'),
    ]

    operations = [
        migrations.CreateModel(
            name='Parametro',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('nombre', models.CharField(max_length=200, unique=True, choices=[('pearson', 'Correlación entre usuarios'), ('kvecinos', 'Maximo de usuarios para la recomendación')], verbose_name='Parametro')),
                ('valor', models.FloatField(default=0.0)),
            ],
        ),
        migrations.DeleteModel(
            name='Parametros',
        ),
    ]
