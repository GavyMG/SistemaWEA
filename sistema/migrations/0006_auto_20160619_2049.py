# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sistema', '0005_auto_20160619_1627'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rating',
            name='usuario',
            field=models.ForeignKey(to='sistema.Perfil'),
        ),
    ]
