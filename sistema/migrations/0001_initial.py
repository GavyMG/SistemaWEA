# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='Documento',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(help_text='Nombre del documento (debe ser unico)', max_length=200, unique=True, verbose_name='Nombre del documento')),
                ('fecha', models.DateTimeField(auto_now=True)),
                ('documento', models.FileField(help_text='Documento a cargar', upload_to='material', null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Estilo',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('estilo', models.CharField(max_length=1, choices=[('v', 'Visual'), ('a', 'Auditivo'), ('r', 'Lectura/escritura'), ('k', 'Kinestésico')])),
                ('peso', models.FloatField(help_text='Peso del estilo en el documento en porcentaje Ej: 100, 50, 40, etc.', default=0.0, verbose_name='Peso para el estilo de aprendizaje')),
                ('documento', models.ForeignKey(to='sistema.Documento')),
            ],
        ),
        migrations.CreateModel(
            name='Perfil',
            fields=[
                ('usuario', models.OneToOneField(to=settings.AUTH_USER_MODEL, primary_key=True, serialize=False)),
                ('visual', models.FloatField(help_text='Indice del estilo visual para la interacción (0-16)', default=0.0)),
                ('auditivo', models.FloatField(help_text='Indice del estilo auditivo para la interacción (0-16)', default=0.0)),
                ('lectura', models.FloatField(help_text='Indice del estilo lectura-escritura para la interacción (0-16)', default=0.0, verbose_name='lectura/escritura')),
                ('kinestesico', models.FloatField(help_text='Indice del estilo kinestésico para la interacción (0-16)', default=0.0, verbose_name='kinestésico')),
                ('test_fecha', models.DateTimeField(help_text='Fecha de la ultima realización del test', auto_now=True, verbose_name='Fecha de actualizacion')),
                ('test_visual', models.FloatField(help_text='Indice del estilo visual obtenido del test (0-16)', default=0.0)),
                ('test_auditivo', models.FloatField(help_text='Indice del estilo auditivo obtenido del test (0-16)', default=0.0)),
                ('test_lectura', models.FloatField(help_text='Indice del estilo lectura-escritura obtenido del test (0-16)', default=0.0, verbose_name='Test lectura/escritura')),
                ('test_kinestesico', models.FloatField(help_text='Indice del estilo kinestésico obtenido del test (0-16)', default=0.0, verbose_name='Test kinestésico')),
            ],
        ),
        migrations.CreateModel(
            name='Rating',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('puntuacion', models.SmallIntegerField(verbose_name='Puntuación')),
                ('fecha', models.DateTimeField(auto_now=True)),
                ('documento', models.ForeignKey(to='sistema.Documento')),
                ('usuario', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Tema',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('posicion', models.PositiveSmallIntegerField(help_text='Número del tema dentro de la asignatura (entero positivo y unico)', unique=True, verbose_name='Tema')),
                ('nombre', models.CharField(help_text='Nombre del tema, debe ser unico', max_length=200, unique=True, verbose_name='Nombre')),
                ('resumen', models.TextField(help_text='No más de 200 caracteres', max_length=200, verbose_name='Resumen')),
                ('imagen', models.ImageField(help_text='Imagen ilustrativa del tema', upload_to='temas', null=True, blank=True)),
                ('fecha', models.DateTimeField(auto_now=True, verbose_name='Fecha de actualizacion')),
                ('inicio', models.DateField(help_text='Fecha estimada de inicio para ver el tema', verbose_name='Planificación: inicio')),
                ('fin', models.DateField(help_text='Fecha estimada de finalización del tema', verbose_name='Planificación: fin')),
            ],
        ),
        migrations.AddField(
            model_name='documento',
            name='temas',
            field=models.ManyToManyField(to='sistema.Tema'),
        ),
    ]
