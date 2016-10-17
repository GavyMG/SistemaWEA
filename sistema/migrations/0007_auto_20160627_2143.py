# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('sistema', '0006_auto_20160619_2049'),
    ]

    operations = [
        migrations.CreateModel(
            name='Parametros',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('nombre', models.CharField(unique=True, max_length=200, verbose_name='Parametro')),
                ('valor', models.FloatField(default=0.0)),
            ],
        ),
        migrations.RemoveField(
            model_name='documento',
            name='puntos',
        ),
        migrations.AddField(
            model_name='comentario',
            name='fecha',
            field=models.DateTimeField(auto_now=True, default=datetime.datetime(2016, 6, 28, 1, 43, 16, 723470, tzinfo=utc), verbose_name='Fecha de actualizacion'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='documento',
            name='puntuacion',
            field=models.FloatField(default=0.0, verbose_name='Puntuación'),
        ),
        migrations.AddField(
            model_name='documento',
            name='visto',
            field=models.IntegerField(default=0.0, verbose_name='Cantidad de visualizaciones'),
        ),
    ]
