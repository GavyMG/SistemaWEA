from django.db import models
from django.contrib.auth.models import User
from datetime import date, datetime


# Create your models here.
class Rating(models.Model):
	usuario = models.ForeignKey('Perfil')
	documento = models.ForeignKey('Documento')
	puntuacion= models.SmallIntegerField(verbose_name='Puntuación', null=True, choices=((1,"1 estrella"), (2,"2 estrellas"), (3, "3 estrellas"), (4, "4 estrellas"), (5, "5 estrellas")))
	texto = models.CharField(max_length=200, verbose_name='Review', help_text='Tu reseña del documento (200 carácteres)')
	fecha = models.DateTimeField(auto_now=True)

	def __str__(self):
		return str(self.usuario)+'-'+str(self.documento)+": "+str(self.puntuacion)

class Documento(models.Model):
	nombre = models.CharField(max_length=200, verbose_name='Nombre del documento', unique=True,help_text='El nombre del documento debe ser unico')
	fecha = models.DateTimeField(default=datetime.today(), editable=False)
	atualizado = models.DateTimeField(auto_now=True)
	documento= models.FileField(upload_to='material', null=True, blank=True, help_text='puede ser un archivo de video, audio o pdf')
	visto = models.IntegerField(default=0,verbose_name='Cantidad de visualizaciones')
	puntuacion = models.FloatField(default=0.0, verbose_name='Puntuación')	
	temas = models.ManyToManyField('Tema')
	
	@property
	def tipo_doc(self):
	    if self.documento.name.endswith('.pdf') or self.documento.name.endswith('.PDF'):
	    	return 'pdf'
	    elif self.documento.name.endswith('.mp3'):
	    	return 'audio'
	    elif self.documento.name.endswith('.mp4'):
	    	return 'video'

	def __str__(self):
		return self.nombre

class Estilo(models.Model):
	estilo = models.CharField(max_length=1, unique=False, choices=(('v',"Visual"), ('a',"Auditivo"), ('r', "Lectura/escritura"), ('k', "Kinestésico")))
	peso = models.FloatField(default=0.0, verbose_name='Peso para el estilo de aprendizaje', help_text='porcentaje del estilo dentro del documento Ej: 100, 50.5, 40, etc.')
	documento = models.ForeignKey('Documento')

	def __str__(self):
		return str(self.documento)+': '+str(self.estilo)+'-'+str(self.peso)

class Tema(models.Model):
	posicion = models.PositiveSmallIntegerField(verbose_name = 'Tema', unique=True, help_text='Posición del tema dentro de la asignatura (entero positivo y unico)')
	nombre = models.CharField(max_length=200, verbose_name='Nombre', unique=True, help_text='Nombre del tema, debe ser unico')
	resumen = models.TextField(max_length=200, verbose_name='Resumen', help_text='200 carácteres')
	imagen = models.ImageField(upload_to='temas', null=True, blank=True,help_text='Imagen ilustrativa del tema')
	fecha = models.DateTimeField(auto_now=True, verbose_name= 'Fecha de actualización')
	inicio = models.DateField(verbose_name= 'Planificación: inicio', help_text='Fecha estimada de inicio para ver el tema')
	fin = models.DateField(verbose_name= 'Planificación: fin', help_text='Fecha estimada de finalización del tema')

	@property
	def activo(self):
	    if (date.today() <= self.fin) and (date.today() >= self.inicio ):
	        return True
	    return False

	@property
	def duracion(self):
	 	duracion= self.fin - self.inicio
	 	if int(duracion.days/7)<1:
	 		return str(duracion.days)+' días'
	 	else:
	 		return str(round(duracion.days/7)) + ' semanas'

	def __str__(self):
		return str(self.posicion)+'. ' +self.nombre


class Perfil(models.Model):
	usuario = models.OneToOneField(User, primary_key=True)
	imagen = models.ImageField(upload_to='usuarios', null=True,verbose_name='Foto de Perfil', blank=True,help_text='Foto de Perfil')
	visual = models.FloatField(default=0.0, help_text='Indice del estilo visual para la interacción (0-16)')
	auditivo = models.FloatField(default=0.0, help_text='Indice del estilo auditivo para la interacción (0-16)')
	lectura = models.FloatField(default=0.0, verbose_name='lectura/escritura', help_text='Indice del estilo lectura-escritura para la interacción (0-16)')
	kinestesico = models.FloatField(default=0.0,verbose_name='kinestésico', help_text='Indice del estilo kinestésico para la interacción (0-16)')
	test_fecha = models.DateTimeField(auto_now=True, verbose_name= 'Fecha de actualizacion', help_text='Fecha de la ultima realización del test')
	test_visual = models.FloatField(default=0.0, help_text='Indice del estilo visual obtenido del test (0-16)')
	test_auditivo = models.FloatField(default=0.0, help_text='Indice del estilo auditivo obtenido del test (0-16)')
	test_lectura = models.FloatField(default=0.0, verbose_name='Test lectura/escritura', help_text='Indice del estilo lectura-escritura obtenido del test (0-16)')
	test_kinestesico = models.FloatField(default=0.0,verbose_name='Test kinestésico', help_text='Indice del estilo kinestésico obtenido del test (0-16)')
	
	@property
	def conimagen(self):
	    if self.imagen:
	    	return True
	    else:
	    	return False

	def __str__(self):
		return str(self.usuario)

class Comentario(models.Model):
	usuario = models.ForeignKey('Perfil')
	documento = models.ForeignKey('Documento')
	texto = models.CharField(max_length=200, verbose_name='Comentario', help_text='200 carácteres')
	fecha = models.DateTimeField(auto_now=True, verbose_name= 'Fecha de actualizacion')

	def __str__(self):
		return str(self.usuario)+': '+str(self.texto)

class Parametro(models.Model):
	nombre = models.CharField(max_length=200, verbose_name='Parametro', unique=True, choices=(('pearson',"Correlación entre usuarios"), ('kvecinos',"Maximo de usuarios para la recomendación"), ('historico', "Cantidad de meses en el historico de interacciones")))
	valor = models.FloatField(default=0.0)

	def __str__(self):
		return str(self.nombre)+': '+str(self.valor)