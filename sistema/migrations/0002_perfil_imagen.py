# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sistema', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='perfil',
            name='imagen',
            field=models.ImageField(upload_to='usuarios', null=True, blank=True, verbose_name='Foto de Perfil', help_text='Foto de Perfil'),
        ),
    ]
