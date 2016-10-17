# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sistema', '0003_documento_puntos'),
    ]

    operations = [
        migrations.CreateModel(
            name='Comentario',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('texto', models.TextField(help_text='Tu comentario', max_length=200, verbose_name='Comentario')),
            ],
        ),
        migrations.AlterField(
            model_name='documento',
            name='puntos',
            field=models.IntegerField(help_text='Puntuación del documento', default=0.0, verbose_name='Puntuación'),
        ),
        migrations.AddField(
            model_name='comentario',
            name='documento',
            field=models.ForeignKey(to='sistema.Documento'),
        ),
        migrations.AddField(
            model_name='comentario',
            name='usuario',
            field=models.ForeignKey(to='sistema.Perfil'),
        ),
    ]
