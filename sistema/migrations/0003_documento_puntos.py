# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sistema', '0002_perfil_imagen'),
    ]

    operations = [
        migrations.AddField(
            model_name='documento',
            name='puntos',
            field=models.FloatField(verbose_name='Puntuación', default=0.0, help_text='Puntuación del documento'),
        ),
    ]
