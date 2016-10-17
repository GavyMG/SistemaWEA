# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.utils.timezone import utc
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('sistema', '0008_auto_20160629_0030'),
    ]

    operations = [
        migrations.AddField(
            model_name='documento',
            name='atualizado',
            field=models.DateTimeField(default=datetime.datetime(2016, 7, 5, 17, 47, 30, 266650, tzinfo=utc), auto_now=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='rating',
            name='texto',
            field=models.CharField(help_text='Tu reseña del documento', default='', max_length=200, verbose_name='Review'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='documento',
            name='fecha',
            field=models.DateTimeField(editable=False, default=datetime.datetime(2016, 7, 5, 13, 47, 3, 752895)),
        ),
        migrations.AlterField(
            model_name='parametro',
            name='nombre',
            field=models.CharField(unique=True, choices=[('pearson', 'Correlación entre usuarios'), ('kvecinos', 'Maximo de usuarios para la recomendación'), ('historico', 'Cantidad de meses en el historico de interacciones')], max_length=200, verbose_name='Parametro'),
        ),
        migrations.AlterField(
            model_name='rating',
            name='puntuacion',
            field=models.SmallIntegerField(null=True, verbose_name='Puntuación'),
        ),
    ]
