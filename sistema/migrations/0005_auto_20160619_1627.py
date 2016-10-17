# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sistema', '0004_auto_20160619_1044'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comentario',
            name='texto',
            field=models.CharField(verbose_name='Comentario', max_length=200, help_text='Tu comentario'),
        ),
    ]
