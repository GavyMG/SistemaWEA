from sistema.models import Tema, Documento, Perfil, Rating, Estilo, Comentario, Parametro
from django.contrib.auth.models import User, Group
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, render_to_response, RequestContext, get_object_or_404, get_list_or_404
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.context_processors import csrf
from sistema.forms import RegistroForm, TestForm, ComentarioForm, PerfilForm, ReviewForm
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.db.models import Q, Avg, Count
from django.db import connection
from datetime import date
from math import sqrt
# for fuzzy logic
import numpy as np
import skfuzzy as fuzz

# Generate universe variables
#   * Visual, auditivo, lectura and kinestesico on subjective ranges [0, 16]
visual = np.arange(0, 17, 1)
auditivo = np.arange(0, 17, 1)
lectura = np.arange(0, 17, 1)
kinestesico = np.arange(0, 17, 1)

# Generate fuzzy membership functions
# visual
visual_hi = fuzz.trapmf(visual, [8, 12, 16, 16])
visual_md = fuzz.trimf(visual, [0, 8, 16])
visual_lo = fuzz.trimf(visual, [0, 0, 8])
# auditivo
auditivo_hi = fuzz.trapmf(auditivo, [8, 12, 16, 16])
auditivo_md = fuzz.trimf(auditivo, [0, 8, 16])
auditivo_lo = fuzz.trimf(auditivo, [0, 0, 8])
# lectura
lectura_hi = fuzz.trapmf(lectura, [8, 12, 16, 16])
lectura_md = fuzz.trimf(lectura, [0, 8, 16])
lectura_lo = fuzz.trimf(lectura, [0, 0, 8])
# kinestesico
kinestesico_hi = fuzz.trapmf(kinestesico, [8, 12, 16, 16])
kinestesico_md = fuzz.trimf(kinestesico, [0, 8, 16])
kinestesico_lo = fuzz.trimf(kinestesico, [0, 0, 8])


# Create your views here.

# Vista del Home 
def inicio(request):
	temas = Tema.objects.all().order_by('posicion')
	if request.user.is_authenticated():
		perfil = Perfil.objects.get(usuario=request.user)
		profesor = Group.objects.filter(user=request.user, name='Profesores')
		is_profesor = len(profesor)>0
		visual_level = np.array([fuzz.interp_membership(visual, visual_hi, perfil.visual), fuzz.interp_membership(visual, visual_md, perfil.visual), fuzz.interp_membership(visual, visual_lo, perfil.visual)])
		auditivo_level = np.array([fuzz.interp_membership(auditivo, auditivo_hi, perfil.auditivo), fuzz.interp_membership(auditivo, auditivo_md, perfil.auditivo), fuzz.interp_membership(auditivo, auditivo_lo, perfil.auditivo)])
		lectura_level = np.array([fuzz.interp_membership(lectura, lectura_hi, perfil.lectura), fuzz.interp_membership(lectura, lectura_md, perfil.lectura), fuzz.interp_membership(lectura, lectura_lo, perfil.lectura)])
		kinestesico_level = np.array([fuzz.interp_membership(kinestesico, kinestesico_hi, perfil.kinestesico), fuzz.interp_membership(kinestesico, kinestesico_md, perfil.kinestesico), fuzz.interp_membership(kinestesico, kinestesico_lo, perfil.kinestesico)])
		#para visual
		if visual_level.argmax()==0:
			perfil.visual='Fuerte'
		elif visual_level.argmax()==1:
			perfil.visual='Medio'
		elif visual_level.argmax()==2:
			perfil.visual='Bajo'
		if auditivo_level.argmax()==0:
			perfil.auditivo='Fuerte'
		elif auditivo_level.argmax()==1:
			perfil.auditivo='Medio'
		elif auditivo_level.argmax()==2:
			perfil.auditivo='Bajo'
		if lectura_level.argmax()==0:
			perfil.lectura='Fuerte'
		elif lectura_level.argmax()==1:
			perfil.lectura='Medio'
		elif lectura_level.argmax()==2:
			perfil.lectura='Bajo'
		if kinestesico_level.argmax()==0:
			perfil.kinestesico='Fuerte'
		elif kinestesico_level.argmax()==1:
			perfil.kinestesico='Medio'
		elif kinestesico_level.argmax()==2:
			perfil.kinestesico='Bajo'
	else:
		perfil = False
		is_profesor = False
	# Obtener planificación de los temas para guiar
	plan = []
	for p in temas:
		if p.activo:
			plan.append(p)
	if len(plan)>0:
		plan1 = plan[0]
	elif len(temas) >0:
		plan1 = temas[0]
	else:
		plan1 = False
	documentos = Documento.objects.filter(puntuacion__gt=3.99).order_by('puntuacion').reverse()[:20]
	return render_to_response('index.html', {'temas':temas, 'plan1':plan1, 'plan':plan, 'perfil':perfil, 'is_profesor':is_profesor, 'documentos':documentos}, context_instance=RequestContext(request))

# Vista generica para un tema 
def tema(request, tema_id):
	temas = Tema.objects.all().order_by('posicion')
	dato = get_object_or_404(Tema, pk=tema_id)  
	#dato = Tema.objects.get(id=tema_id)
	documentos = Documento.objects.filter(temas__id=tema_id)
	ndocumentos = documentos.count()
	# Obtener planificación de los temas para guiar, en caso de que haya más de un tema activo
	plansig = []
	planant = []
	plan=[]
	for p in temas:
		if p.activo:
			plan.append(p)
			if p.posicion>dato.posicion:
				plansig.append(p)
			# temas anteriores
			elif p.posicion<dato.posicion:
				planant.append(p)
	# Elegir el tema siguiente inmediato
	if len(plansig)>0:
		plan1 = plansig[0]
	else:
		plan1 = False
	# Elegir el tema anterior inmediato
	if len(planant) >0:
		plan2 = planant[(len(planant)-1)]
	else:
		plan2 = False
	# Array de los estilos a recomendar
	estilos = []
	peso = []
	yourdocumentos = []
	# Funciones de pertenencia y comienzo de la LD si el usuario está autentificado
	if request.user.is_authenticated():
		perfil = Perfil.objects.get(usuario=request.user)
		profesor = Group.objects.filter(user=request.user, name='Profesores')
		is_profesor = len(profesor)>0
		recomendar_doc = recommend(request.user)
		#return HttpResponse(recomendar_doc)
		docs=[]
		Recomendar=[]
		for x in range(0,len(recomendar_doc)):
			docs.append(recomendar_doc[x][0])
			aux=Documento.objects.filter(nombre=recomendar_doc[x][0]).filter(temas__id=tema_id)
			if len(aux)>0:
				Recomendar.append(aux[0])
		#
		# Obtener grado de pertenencia para los estilos (con indices de interacción)
		visual_level = np.array([fuzz.interp_membership(visual, visual_hi, perfil.visual), fuzz.interp_membership(visual, visual_md, perfil.visual), fuzz.interp_membership(visual, visual_lo, perfil.visual)])
		auditivo_level = np.array([fuzz.interp_membership(auditivo, auditivo_hi, perfil.auditivo), fuzz.interp_membership(auditivo, auditivo_md, perfil.auditivo), fuzz.interp_membership(auditivo, auditivo_lo, perfil.auditivo)])
		lectura_level = np.array([fuzz.interp_membership(lectura, lectura_hi, perfil.lectura), fuzz.interp_membership(lectura, lectura_md, perfil.lectura), fuzz.interp_membership(lectura, lectura_lo, perfil.lectura)])
		kinestesico_level = np.array([fuzz.interp_membership(kinestesico, kinestesico_hi, perfil.kinestesico), fuzz.interp_membership(kinestesico, kinestesico_md, perfil.kinestesico), fuzz.interp_membership(kinestesico, kinestesico_lo, perfil.kinestesico)])
		# Si los indices de las interacciones son bajas, usar los indices del test
		if visual_level.argmax()==2 and auditivo_level.argmax()==2 and lectura_level.argmax()==2 and kinestesico_level.argmax()==2:
			# Obtener grado de pertenencia de los indices del test
			visual_level = np.array([fuzz.interp_membership(visual, visual_hi, perfil.test_visual), fuzz.interp_membership(visual, visual_md, perfil.test_visual), fuzz.interp_membership(visual, visual_lo, perfil.test_visual)])
			auditivo_level = np.array([fuzz.interp_membership(auditivo, auditivo_hi, perfil.test_auditivo), fuzz.interp_membership(auditivo, auditivo_md, perfil.test_auditivo), fuzz.interp_membership(auditivo, auditivo_lo, perfil.test_auditivo)])
			lectura_level = np.array([fuzz.interp_membership(lectura, lectura_hi, perfil.test_lectura), fuzz.interp_membership(lectura, lectura_md, perfil.test_lectura), fuzz.interp_membership(lectura, lectura_lo, perfil.test_lectura)])
			kinestesico_level = np.array([fuzz.interp_membership(kinestesico, kinestesico_hi, perfil.test_kinestesico), fuzz.interp_membership(kinestesico, kinestesico_md, perfil.test_kinestesico), fuzz.interp_membership(kinestesico, kinestesico_lo, perfil.test_kinestesico)])
		# Applicar reglas para definir estilos
		# Si hay un estilo fuerte recomiendalo
		# visual
		if visual_level.argmax()==0:
			estilos.append('v')
			peso.append(perfil.visual)
		# auditivo
		if auditivo_level.argmax()==0:
			estilos.append('a')
			peso.append(perfil.auditivo)
		# lectura-escritura
		if lectura_level.argmax()==0:
			estilos.append('r')
			peso.append(perfil.lectura)
		# kinestésico
		if kinestesico_level.argmax()==0:
			estilos.append('k')
			peso.append(perfil.kinestesico)
		# Si hay estilos fuertes recomiendalos
		if len(estilos)>0 and len(documentos)>0:
			if len(estilos)==1:
				with connection.cursor() as c:
					c.execute("select c.nombre, c.puntuacion, SUM(c.peso) as peso from ((SELECT a.id, a.nombre, a.puntuacion, b.estilo, (b.peso * %s) as peso FROM sistema_documento as a join sistema_estilo as b on a.id = b.documento_id where estilo=%s)) as c group by c.nombre, c.puntuacion order by peso desc, puntuacion desc", [int(peso[0]), estilos[0]])
					query = dictfetchall(c)
					for x in query:
						docs.append(x['nombre'])
						aux=Documento.objects.filter(nombre=x['nombre']).filter(temas__id=tema_id)
						if len(aux)>0:
							yourdocumentos.append(aux[0])
			elif len(estilos)==2:
				with connection.cursor() as c:
					c.execute("select c.nombre, c.puntuacion, SUM(c.peso) as peso from((SELECT a.id, a.nombre, a.puntuacion, b.estilo, (b.peso * %s) as peso FROM sistema_documento as a join sistema_estilo as b on a.id = b.documento_id where estilo=%s) union (SELECT a.id, a.nombre, a.puntuacion, b.estilo, (b.peso * %s) as peso FROM sistema_documento as a join sistema_estilo as b on a.id = b.documento_id where estilo=%s)) as c group by c.nombre, c.puntuacion order by peso desc, puntuacion desc", [int(peso[0]), estilos[0], int(peso[1]), estilos[1]])
					query = dictfetchall(c)
					for x in query:
						docs.append(x['nombre'])
						aux=Documento.objects.filter(nombre=x['nombre']).filter(temas__id=tema_id)
						if len(aux)>0:
							yourdocumentos.append(aux[0])
			elif len(estilos)==3:
				with connection.cursor() as c:
					c.execute("select c.nombre, c.puntuacion, SUM(c.peso) as peso from((SELECT a.id, a.nombre, a.puntuacion, b.estilo, (b.peso * %s) as peso FROM sistema_documento as a join sistema_estilo as b on a.id = b.documento_id where estilo=%s) union (SELECT a.id, a.nombre, a.puntuacion, b.estilo, (b.peso * %s) as peso FROM sistema_documento as a join sistema_estilo as b on a.id = b.documento_id where estilo=%s) union (SELECT a.id, a.nombre, a.puntuacion, b.estilo, (b.peso * %s) as peso FROM sistema_documento as a join sistema_estilo as b on a.id = b.documento_id where estilo=%s)) as c group by c.nombre, c.puntuacion order by peso desc, puntuacion desc", [int(peso[0]), estilos[0], int(peso[1]), estilos[1], int(peso[2]), estilos[2]])
					query = dictfetchall(c)
					for x in query:
						docs.append(x['nombre'])
						aux=Documento.objects.filter(nombre=x['nombre']).filter(temas__id=tema_id)
						if len(aux)>0:
							yourdocumentos.append(aux[0])
			else:
				with connection.cursor() as c:
					c.execute("select c.nombre, c.puntuacion, SUM(c.peso) as peso from((SELECT a.id, a.nombre, a.puntuacion, b.estilo, (b.peso * %s) as peso FROM sistema_documento as a join sistema_estilo as b on a.id = b.documento_id where estilo=%s) union (SELECT a.id, a.nombre, a.puntuacion, b.estilo, (b.peso * %s) as peso FROM sistema_documento as a join sistema_estilo as b on a.id = b.documento_id where estilo=%s) union (SELECT a.id, a.nombre, a.puntuacion, b.estilo, (b.peso * %s) as peso FROM sistema_documento as a join sistema_estilo as b on a.id = b.documento_id where estilo=%s) union (SELECT a.id, a.nombre, a.puntuacion, b.estilo, (b.peso * %s) as peso FROM sistema_documento as a join sistema_estilo as b on a.id = b.documento_id where estilo=%s)) as c group by c.nombre, c.puntuacion order by peso desc, puntuacion desc", [int(peso[0]), estilos[0], int(peso[1]), estilos[1], int(peso[2]), estilos[2], int(peso[3]), estilos[3]])
					query = dictfetchall(c)
					for x in query:
						docs.append(x['nombre'])
						aux=Documento.objects.filter(nombre=x['nombre']).filter(temas__id=tema_id)
						if len(aux)>0:
							yourdocumentos.append(aux[0])
		# Si no hubo estilos fuertes o no hay documentos de los estilos fuertes, buscar los estilos medios y recomendarlos
		if len(yourdocumentos)==0:
			# visual
			if visual_level.argmax()==1:
				estilos.append('v')
				peso.append(perfil.visual)
			# auditivo
			if auditivo_level.argmax()==1:
				estilos.append('a')
				peso.append(perfil.auditivo)
			# lectura-escritura
			if lectura_level.argmax()==1:
				estilos.append('r')
				peso.append(perfil.lectura)
			# kinestésico
			if kinestesico_level.argmax()==1:
				estilos.append('k')
				peso.append(perfil.kinestesico)
			# Recomendar o buscar documentos
			if len(estilos)>0 and len(documentos)>0:
				if len(estilos)==1:
					with connection.cursor() as c:
						c.execute("select c.nombre, c.puntuacion, SUM(c.peso) as peso from ((SELECT a.id, a.nombre, a.puntuacion, b.estilo, (b.peso * %s) as peso FROM sistema_documento as a join sistema_estilo as b on a.id = b.documento_id where estilo=%s)) as c group by c.nombre, c.puntuacion order by peso desc, puntuacion desc", [int(peso[0]), estilos[0]])
						query = dictfetchall(c)
						for x in query:
							docs.append(x['nombre'])
							aux=Documento.objects.filter(nombre=x['nombre']).filter(temas__id=tema_id)
							if len(aux)>0:
								yourdocumentos.append(aux[0])
				elif len(estilos)==2:
					with connection.cursor() as c:
						c.execute("select c.nombre, c.puntuacion, SUM(c.peso) as peso from((SELECT a.id, a.nombre, a.puntuacion, b.estilo, (b.peso * %s) as peso FROM sistema_documento as a join sistema_estilo as b on a.id = b.documento_id where estilo=%s) union (SELECT a.id, a.nombre, a.puntuacion, b.estilo, (b.peso * %s) as peso FROM sistema_documento as a join sistema_estilo as b on a.id = b.documento_id where estilo=%s)) as c group by c.nombre, c.puntuacion order by peso desc, puntuacion desc", [int(peso[0]), estilos[0], int(peso[1]), estilos[1]])
						query = dictfetchall(c)
						for x in query:
							docs.append(x['nombre'])
							aux=Documento.objects.filter(nombre=x['nombre']).filter(temas__id=tema_id)
							if len(aux)>0:
								yourdocumentos.append(aux[0])
				elif len(estilos)==3:
					with connection.cursor() as c:
						c.execute("select c.nombre, c.puntuacion, SUM(c.peso) as peso from((SELECT a.id, a.nombre, a.puntuacion, b.estilo, (b.peso * %s) as peso FROM sistema_documento as a join sistema_estilo as b on a.id = b.documento_id where estilo=%s) union (SELECT a.id, a.nombre, a.puntuacion, b.estilo, (b.peso * %s) as peso FROM sistema_documento as a join sistema_estilo as b on a.id = b.documento_id where estilo=%s) union (SELECT a.id, a.nombre, a.puntuacion, b.estilo, (b.peso * %s) as peso FROM sistema_documento as a join sistema_estilo as b on a.id = b.documento_id where estilo=%s)) as c group by c.nombre, c.puntuacion order by peso desc, puntuacion desc", [int(peso[0]), estilos[0], int(peso[1]), estilos[1], int(peso[2]), estilos[2]])
						query = dictfetchall(c)
						for x in query:
							docs.append(x['nombre'])
							aux=Documento.objects.filter(nombre=x['nombre']).filter(temas__id=tema_id)
							if len(aux)>0:
								yourdocumentos.append(aux[0])
				else:
					with connection.cursor() as c:
						c.execute("select c.nombre, c.puntuacion, SUM(c.peso) as peso from((SELECT a.id, a.nombre, a.puntuacion, b.estilo, (b.peso * %s) as peso FROM sistema_documento as a join sistema_estilo as b on a.id = b.documento_id where estilo=%s) union (SELECT a.id, a.nombre, a.puntuacion, b.estilo, (b.peso * %s) as peso FROM sistema_documento as a join sistema_estilo as b on a.id = b.documento_id where estilo=%s) union (SELECT a.id, a.nombre, a.puntuacion, b.estilo, (b.peso * %s) as peso FROM sistema_documento as a join sistema_estilo as b on a.id = b.documento_id where estilo=%s) union (SELECT a.id, a.nombre, a.puntuacion, b.estilo, (b.peso * %s) as peso FROM sistema_documento as a join sistema_estilo as b on a.id = b.documento_id where estilo=%s)) as c group by c.nombre, c.puntuacion order by peso desc, puntuacion desc", [int(peso[0]), estilos[0], int(peso[1]), estilos[1], int(peso[2]), estilos[2], int(peso[3]), estilos[3]])
						query = dictfetchall(c)
						for x in query:
							docs.append(x['nombre'])
							aux=Documento.objects.filter(nombre=x['nombre']).filter(temas__id=tema_id)
							if len(aux)>0:
								yourdocumentos.append(aux[0])		
		documentos = documentos.exclude(nombre__in = docs)
		#Recomendar = Recomendar.order_by('puntuacion').reverse()
		otros= documentos.order_by('puntuacion').reverse()
		#yourdocumentos = yourdocumentos.order_by('puntuacion').reverse()
		#para visual
		if visual_level.argmax()==0:
			perfil.visual='Fuerte'
		elif visual_level.argmax()==1:
			perfil.visual='Medio'
		elif visual_level.argmax()==2:
			perfil.visual='Bajo'
		if auditivo_level.argmax()==0:
			perfil.auditivo='Fuerte'
		elif auditivo_level.argmax()==1:
			perfil.auditivo='Medio'
		elif auditivo_level.argmax()==2:
			perfil.auditivo='Bajo'
		if lectura_level.argmax()==0:
			perfil.lectura='Fuerte'
		elif lectura_level.argmax()==1:
			perfil.lectura='Medio'
		elif lectura_level.argmax()==2:
			perfil.lectura='Bajo'
		if kinestesico_level.argmax()==0:
			perfil.kinestesico='Fuerte'
		elif kinestesico_level.argmax()==1:
			perfil.kinestesico='Medio'
		elif kinestesico_level.argmax()==2:
			perfil.kinestesico='Bajo'
	else:
		Recomendar = []
		otros=[]
		perfil=False
		is_profesor = False
	todos = Documento.objects.filter(temas__id=tema_id).order_by('puntuacion').reverse()
	documentos = Documento.objects.filter(temas__id=tema_id, puntuacion__gt=3.99).order_by('puntuacion').reverse()
	return render_to_response('tema.html', {'temas':temas, 'tema':dato, 'documentos':documentos, 'todos':todos,'yourdocumentos':yourdocumentos,'plan':plan, 'siguiente':plan1, 'anterior':plan2, 'Recomendar':Recomendar,'otros':otros, 'perfil':perfil, 'ndocumentos':ndocumentos, 'is_profesor':is_profesor}, context_instance=RequestContext(request))

# Pagina de información y contacto
def info(request):
	temas = Tema.objects.all().order_by('posicion')
	documentos = Documento.objects.filter(puntuacion__gt=3.99).order_by('puntuacion').reverse()
	plan = []
	for p in temas:
		# temas siguientes
		if p.activo:
			plan.append(p)
	ac_temas= len(plan)
	if request.user.is_authenticated():
		perfil = Perfil.objects.get(usuario=request.user)
		profesor = Group.objects.filter(user=request.user, name='Profesores')
		is_profesor = len(profesor)>0
		visual_level = np.array([fuzz.interp_membership(visual, visual_hi, perfil.visual), fuzz.interp_membership(visual, visual_md, perfil.visual), fuzz.interp_membership(visual, visual_lo, perfil.visual)])
		auditivo_level = np.array([fuzz.interp_membership(auditivo, auditivo_hi, perfil.auditivo), fuzz.interp_membership(auditivo, auditivo_md, perfil.auditivo), fuzz.interp_membership(auditivo, auditivo_lo, perfil.auditivo)])
		lectura_level = np.array([fuzz.interp_membership(lectura, lectura_hi, perfil.lectura), fuzz.interp_membership(lectura, lectura_md, perfil.lectura), fuzz.interp_membership(lectura, lectura_lo, perfil.lectura)])
		kinestesico_level = np.array([fuzz.interp_membership(kinestesico, kinestesico_hi, perfil.kinestesico), fuzz.interp_membership(kinestesico, kinestesico_md, perfil.kinestesico), fuzz.interp_membership(kinestesico, kinestesico_lo, perfil.kinestesico)])
		#para visual
		if visual_level.argmax()==0:
			perfil.visual='Fuerte'
		elif visual_level.argmax()==1:
			perfil.visual='Medio'
		elif visual_level.argmax()==2:
			perfil.visual='Bajo'
		if auditivo_level.argmax()==0:
			perfil.auditivo='Fuerte'
		elif auditivo_level.argmax()==1:
			perfil.auditivo='Medio'
		elif auditivo_level.argmax()==2:
			perfil.auditivo='Bajo'
		if lectura_level.argmax()==0:
			perfil.lectura='Fuerte'
		elif lectura_level.argmax()==1:
			perfil.lectura='Medio'
		elif lectura_level.argmax()==2:
			perfil.lectura='Bajo'
		if kinestesico_level.argmax()==0:
			perfil.kinestesico='Fuerte'
		elif kinestesico_level.argmax()==1:
			perfil.kinestesico='Medio'
		elif kinestesico_level.argmax()==2:
			perfil.kinestesico='Bajo'
	else:
		perfil = False
		is_profesor = False
	return render_to_response('info.html', {'temas':temas, 'perfil':perfil, 'is_profesor':is_profesor, 'plan':plan,'documentos':documentos}, context_instance=RequestContext(request))

# Registro de usuario estudiante o no administrador
def registro(request):
	temas = Tema.objects.all().order_by('posicion')
	if request.POST:
		formulario = UserCreationForm(request.POST)
		formulariob = PerfilForm(request.POST, request.FILES)
		if formulario.is_valid and formulariob.is_valid():
			username = request.POST['username']
			password = request.POST['password1']
			image = request.FILES['image']
			formulario.save()
			user = authenticate(username=username, password=password)
			if user is not None:
				if user.is_active:
					login(request, user)
			perfil = Perfil(usuario=user, imagen=image)
			perfil.save()
			return HttpResponseRedirect('/inicial_test/')
	else:
		formulario = UserCreationForm()
		formulariob = PerfilForm()
	return render_to_response('registro.html', {'temas':temas, 'formulario':formulario, 'formulariob':formulariob}, context_instance=RequestContext(request))

# Iniciar sesión
def iniciarSesion(request):
	next = request.GET.get('next', '/')
	error=False
	if request.method == 'POST':
		formulario = AuthenticationForm(request.POST)
		if formulario.is_valid:
			username = request.POST['username']
			password = request.POST['password']
			user = authenticate(username=username, password=password)
			if user is not None:
				if user.is_active:
					login(request, user)
					return HttpResponseRedirect(next)
				else:
					HttpResponse("Inactive user.")
			else:
				error=True
				#return HttpResponse("Ingresa un usuario y contraseña valido")
	else:
		formulario = AuthenticationForm()
	return render_to_response('login.html', { 'error':error,'formulario':formulario}, context_instance=RequestContext(request))

# Cambiar contraseña
@login_required
def Password_change(request):
	temas = Tema.objects.all().order_by('posicion')
	perfil = Perfil.objects.get(usuario=request.user)
	profesor = Group.objects.filter(user=request.user, name='Profesores')
	is_profesor = len(profesor)>0 
	next = request.GET.get('next', '/')
	if request.method == 'POST':
		form = PasswordChangeForm(user=request.user, data=request.POST)
		if form.is_valid():
			form.save()
			update_session_auth_hash(request, form.user)
			return HttpResponseRedirect(next)
	else:
		form = PasswordChangeForm(user=request.user)
	plan = []
	for p in temas:
		# temas siguientes
		if p.activo:
			plan.append(p)
	ac_temas= len(plan)
	documentos = Documento.objects.filter(puntuacion__gt=3.9).order_by('puntuacion').reverse()[:100]
	visual_level = np.array([fuzz.interp_membership(visual, visual_hi, perfil.visual), fuzz.interp_membership(visual, visual_md, perfil.visual), fuzz.interp_membership(visual, visual_lo, perfil.visual)])
	auditivo_level = np.array([fuzz.interp_membership(auditivo, auditivo_hi, perfil.auditivo), fuzz.interp_membership(auditivo, auditivo_md, perfil.auditivo), fuzz.interp_membership(auditivo, auditivo_lo, perfil.auditivo)])
	lectura_level = np.array([fuzz.interp_membership(lectura, lectura_hi, perfil.lectura), fuzz.interp_membership(lectura, lectura_md, perfil.lectura), fuzz.interp_membership(lectura, lectura_lo, perfil.lectura)])
	kinestesico_level = np.array([fuzz.interp_membership(kinestesico, kinestesico_hi, perfil.kinestesico), fuzz.interp_membership(kinestesico, kinestesico_md, perfil.kinestesico), fuzz.interp_membership(kinestesico, kinestesico_lo, perfil.kinestesico)])
	#para visual
	if visual_level.argmax()==0:
		perfil.visual='Fuerte'
	elif visual_level.argmax()==1:
		perfil.visual='Medio'
	elif visual_level.argmax()==2:
		perfil.visual='Bajo'
	if auditivo_level.argmax()==0:
		perfil.auditivo='Fuerte'
	elif auditivo_level.argmax()==1:
		perfil.auditivo='Medio'
	elif auditivo_level.argmax()==2:
		perfil.auditivo='Bajo'
	if lectura_level.argmax()==0:
		perfil.lectura='Fuerte'
	elif lectura_level.argmax()==1:
		perfil.lectura='Medio'
	elif lectura_level.argmax()==2:
		perfil.lectura='Bajo'
	if kinestesico_level.argmax()==0:
		perfil.kinestesico='Fuerte'
	elif kinestesico_level.argmax()==1:
		perfil.kinestesico='Medio'
	elif kinestesico_level.argmax()==2:
		perfil.kinestesico='Bajo'
	return render_to_response('cambio_password.html', { 'documentos':documentos,'plan':plan,'temas':temas, 'formulario':form, 'perfil':perfil, 'is_profesor':is_profesor}, context_instance=RequestContext(request))


# Cerrar Sesión
@login_required
def Salir(request):
	logout(request)
	return HttpResponseRedirect(settings.LOGIN_URL)

# Cambiar información del usuario
@login_required	
def editar_perfil(request):
	temas = Tema.objects.all().order_by('posicion')
	perfil = Perfil.objects.get(usuario=request.user)
	profesor = Group.objects.filter(user=request.user, name='Profesores')
	is_profesor = len(profesor)>0 
	if request.method == "POST":
		formulario = RegistroForm(request.POST, instance=request.user)
		if formulario.is_valid():
			formulario.save()
			perfil.save()
			return HttpResponseRedirect('/')	
	else:
		formulario = RegistroForm(instance=request.user)
	plan = []
	for p in temas:
		# temas siguientes
		if p.activo:
			plan.append(p)
	ac_temas= len(plan)
	documentos = Documento.objects.filter(puntuacion__gt=3.9).order_by('puntuacion').reverse()[:100]
	visual_level = np.array([fuzz.interp_membership(visual, visual_hi, perfil.visual), fuzz.interp_membership(visual, visual_md, perfil.visual), fuzz.interp_membership(visual, visual_lo, perfil.visual)])
	auditivo_level = np.array([fuzz.interp_membership(auditivo, auditivo_hi, perfil.auditivo), fuzz.interp_membership(auditivo, auditivo_md, perfil.auditivo), fuzz.interp_membership(auditivo, auditivo_lo, perfil.auditivo)])
	lectura_level = np.array([fuzz.interp_membership(lectura, lectura_hi, perfil.lectura), fuzz.interp_membership(lectura, lectura_md, perfil.lectura), fuzz.interp_membership(lectura, lectura_lo, perfil.lectura)])
	kinestesico_level = np.array([fuzz.interp_membership(kinestesico, kinestesico_hi, perfil.kinestesico), fuzz.interp_membership(kinestesico, kinestesico_md, perfil.kinestesico), fuzz.interp_membership(kinestesico, kinestesico_lo, perfil.kinestesico)])
	#para visual
	if visual_level.argmax()==0:
		perfil.visual='Fuerte'
	elif visual_level.argmax()==1:
		perfil.visual='Medio'
	elif visual_level.argmax()==2:
		perfil.visual='Bajo'
	if auditivo_level.argmax()==0:
		perfil.auditivo='Fuerte'
	elif auditivo_level.argmax()==1:
		perfil.auditivo='Medio'
	elif auditivo_level.argmax()==2:
		perfil.auditivo='Bajo'
	if lectura_level.argmax()==0:
		perfil.lectura='Fuerte'
	elif lectura_level.argmax()==1:
		perfil.lectura='Medio'
	elif lectura_level.argmax()==2:
		perfil.lectura='Bajo'
	if kinestesico_level.argmax()==0:
		perfil.kinestesico='Fuerte'
	elif kinestesico_level.argmax()==1:
		perfil.kinestesico='Medio'
	elif kinestesico_level.argmax()==2:
		perfil.kinestesico='Bajo'
	return render_to_response('editar_perfil.html', { 'documentos':documentos, 'plan':plan,'temas':temas, 'formulario':formulario, 'perfil':perfil, 'is_profesor':is_profesor}, context_instance=RequestContext(request))

@login_required
def subir_imagen(request):
	temas = Tema.objects.all().order_by('posicion')
	perfil = Perfil.objects.get(usuario=request.user)
	profesor = Group.objects.filter(user=request.user, name='Profesores')
	is_profesor = len(profesor)>0
	if request.method == "POST":
		formulariob = PerfilForm(request.POST, request.FILES)
		if formulariob.is_valid():
			image = request.FILES['image']
			perfil.imagen=image
			perfil.save()
			return HttpResponseRedirect('/')	
	else:
		formulariob = PerfilForm()
	plan = []
	for p in temas:
		# temas siguientes
		if p.activo:
			plan.append(p)
	ac_temas= len(plan)
	documentos = Documento.objects.filter(puntuacion__gt=3.9).order_by('puntuacion').reverse()[:100]
	visual_level = np.array([fuzz.interp_membership(visual, visual_hi, perfil.visual), fuzz.interp_membership(visual, visual_md, perfil.visual), fuzz.interp_membership(visual, visual_lo, perfil.visual)])
	auditivo_level = np.array([fuzz.interp_membership(auditivo, auditivo_hi, perfil.auditivo), fuzz.interp_membership(auditivo, auditivo_md, perfil.auditivo), fuzz.interp_membership(auditivo, auditivo_lo, perfil.auditivo)])
	lectura_level = np.array([fuzz.interp_membership(lectura, lectura_hi, perfil.lectura), fuzz.interp_membership(lectura, lectura_md, perfil.lectura), fuzz.interp_membership(lectura, lectura_lo, perfil.lectura)])
	kinestesico_level = np.array([fuzz.interp_membership(kinestesico, kinestesico_hi, perfil.kinestesico), fuzz.interp_membership(kinestesico, kinestesico_md, perfil.kinestesico), fuzz.interp_membership(kinestesico, kinestesico_lo, perfil.kinestesico)])
	#para visual
	if visual_level.argmax()==0:
		perfil.visual='Fuerte'
	elif visual_level.argmax()==1:
		perfil.visual='Medio'
	elif visual_level.argmax()==2:
		perfil.visual='Bajo'
	if auditivo_level.argmax()==0:
		perfil.auditivo='Fuerte'
	elif auditivo_level.argmax()==1:
		perfil.auditivo='Medio'
	elif auditivo_level.argmax()==2:
		perfil.auditivo='Bajo'
	if lectura_level.argmax()==0:
		perfil.lectura='Fuerte'
	elif lectura_level.argmax()==1:
		perfil.lectura='Medio'
	elif lectura_level.argmax()==2:
		perfil.lectura='Bajo'
	if kinestesico_level.argmax()==0:
		perfil.kinestesico='Fuerte'
	elif kinestesico_level.argmax()==1:
		perfil.kinestesico='Medio'
	elif kinestesico_level.argmax()==2:
		perfil.kinestesico='Bajo'
	return render_to_response('editar_foto_perfil.html', {'documentos':documentos, 'plan':plan,'temas':temas, 'perfil':perfil, 'formulariob':formulariob, 'is_profesor':is_profesor}, context_instance=RequestContext(request))


# Test inicial
@login_required
def inicial_test(request):
	temas = Tema.objects.all().order_by('posicion')
	perfil = Perfil.objects.get(usuario=request.user)
	profesor = Group.objects.filter(user=request.user, name='Profesores')
	is_profesor = len(profesor)>0 
	if request.method == "POST":
		formulario = TestForm(request.POST)
		if formulario.is_valid:
			p=['','','','','','','','','','','','','','','','']
			for x in range(1,17):
				campo='p'+ str(x)
				p[x-1] = request.POST.getlist(campo, False)
			if p[0] or p[1] or p[2] or p[3] or p[4] or p[5] or p[6] or p[7] or p[8] or p[9] or p[10] or p[11] or p[12] or p[13] or p[14] or p[15]:
				estilos=[0,0,0,0]
				for i in range(0,16):
					if p[i]:
						for j in range(0,len(p[i])):
							if p[i][j]=='V':
								estilos[0]=estilos[0]+1
							elif p[i][j]=='A':
								estilos[1]=estilos[1]+1
							elif p[i][j]=='R':
								estilos[2]=estilos[2]+1
							elif p[i][j]=='K':
								estilos[3]=estilos[3]+1
				perfil = Perfil.objects.get(usuario=request.user)
				perfil.test_visual=estilos[0]
				perfil.test_auditivo=estilos[1]
				perfil.test_lectura=estilos[2]
				perfil.test_kinestesico=estilos[3]
				#Normalizar valores numericos
				if perfil.visual ==0 and perfil.auditivo==0 and perfil.lectura==0 and perfil.kinestesico==0:
					estil=np.array([perfil.test_visual, perfil.test_auditivo, perfil.test_lectura, perfil.test_kinestesico], dtype='float')
					maximo= estil.max()
					for i in range(0,len(estil)):
						estil[i] = estil[i]/maximo *16
					perfil.visual=round(estil[0], 2)
					perfil.auditivo=round(estil[1], 2)
					perfil.lectura=round(estil[2], 2)
					perfil.kinestesico=round(estil[3],2)
				perfil.save()
				return HttpResponseRedirect('/estilos/')
			else:
				return HttpResponse("responde una pregunta")
		else:
			return HttpResponse("Invalido")
	else:
		formulario = TestForm()
	#paginator = Paginator(formulario, 1)
	#page = request.GET.get('page')
	#try:
	#	form = paginator.page(page)
	#except PageNotAnInteger:
	#	form = paginator.page(1)
	#except EmptyPage:
	#	form = paginator.page(paginator.num_pages)
	return render_to_response('inicial_test.html', {'temas':temas, 'formulario':formulario, 'perfil':perfil, 'is_profesor':is_profesor}, context_instance=RequestContext(request))


# Todo el material
def material(request):
	temas = Tema.objects.all().order_by('posicion')
	todos = Documento.objects.all().order_by('puntuacion', 'fecha').reverse()
	otros = Documento.objects.all().order_by('fecha').reverse()
	documentos = todos.filter(puntuacion__gt=3.99)
	# Obtener planificación de los temas para guiar
	plan = []
	for p in temas:
		if p.activo:
			plan.append(p)
	if request.user.is_authenticated():
		perfil = Perfil.objects.get(usuario=request.user)
		profesor = Group.objects.filter(user=request.user, name='Profesores')
		is_profesor = len(profesor)>0
		recomendar_doc = recommend(request.user)
		docs=[]
		Recomendar=[]
		for x in range(0,len(recomendar_doc)):
			docs.append(recomendar_doc[x][0])
			aux=Documento.objects.filter(nombre=recomendar_doc[x][0])
			if len(aux)>0:
				Recomendar.append(aux[0])
		# Array de los estilos a recomendar
		estilos = []
		peso=[]
		yourdocumentos=[]
		# Funciones de pertenencia y comienzo de la LD 
		# Obtener grado de pertenencia para los estilos (con indices de interacción)
		visual_level = np.array([fuzz.interp_membership(visual, visual_hi, perfil.visual), fuzz.interp_membership(visual, visual_md, perfil.visual), fuzz.interp_membership(visual, visual_lo, perfil.visual)])
		auditivo_level = np.array([fuzz.interp_membership(auditivo, auditivo_hi, perfil.auditivo), fuzz.interp_membership(auditivo, auditivo_md, perfil.auditivo), fuzz.interp_membership(auditivo, auditivo_lo, perfil.auditivo)])
		lectura_level = np.array([fuzz.interp_membership(lectura, lectura_hi, perfil.lectura), fuzz.interp_membership(lectura, lectura_md, perfil.lectura), fuzz.interp_membership(lectura, lectura_lo, perfil.lectura)])
		kinestesico_level = np.array([fuzz.interp_membership(kinestesico, kinestesico_hi, perfil.kinestesico), fuzz.interp_membership(kinestesico, kinestesico_md, perfil.kinestesico), fuzz.interp_membership(kinestesico, kinestesico_lo, perfil.kinestesico)])
		#Si los indices de las interacciones son bajas, usar los indices del test
		if visual_level.argmax()==2 and auditivo_level.argmax()==2 and lectura_level.argmax()==2 and kinestesico_level.argmax()==2:
			#Obtener grado de pertenencia de los indices del test
			visual_level = np.array([fuzz.interp_membership(visual, visual_hi, perfil.test_visual), fuzz.interp_membership(visual, visual_md, perfil.test_visual), fuzz.interp_membership(visual, visual_lo, perfil.test_visual)])
			auditivo_level = np.array([fuzz.interp_membership(auditivo, auditivo_hi, perfil.test_auditivo), fuzz.interp_membership(auditivo, auditivo_md, perfil.test_auditivo), fuzz.interp_membership(auditivo, auditivo_lo, perfil.test_auditivo)])
			lectura_level = np.array([fuzz.interp_membership(lectura, lectura_hi, perfil.test_lectura), fuzz.interp_membership(lectura, lectura_md, perfil.test_lectura), fuzz.interp_membership(lectura, lectura_lo, perfil.test_lectura)])
			kinestesico_level = np.array([fuzz.interp_membership(kinestesico, kinestesico_hi, perfil.test_kinestesico), fuzz.interp_membership(kinestesico, kinestesico_md, perfil.test_kinestesico), fuzz.interp_membership(kinestesico, kinestesico_lo, perfil.test_kinestesico)])
		# Applicar reglas para definir estilos
		# Si hay un estilo fuerte recomiendalo
		# visual
		if visual_level.argmax()==0:
			estilos.append('v')
			peso.append(perfil.visual)
		# auditivo
		if auditivo_level.argmax()==0:
			estilos.append('a')
			peso.append(perfil.auditivo)
		# lectura-escritura
		if lectura_level.argmax()==0:
			estilos.append('r')
			peso.append(perfil.lectura)
		# kinestésico
		if kinestesico_level.argmax()==0:
			estilos.append('k')
			peso.append(perfil.kinestesico)
		# Si hay estilos fuertes recomiendalos
		if len(estilos)>0 and len(documentos)>0:
			if len(estilos)==1:
				with connection.cursor() as c:
					c.execute("select c.nombre, c.puntuacion, SUM(c.peso) as peso from ((SELECT a.id, a.nombre, a.puntuacion, b.estilo, (b.peso * %s) as peso FROM sistema_documento as a join sistema_estilo as b on a.id = b.documento_id where estilo=%s)) as c group by c.nombre, c.puntuacion order by peso desc, puntuacion desc", [int(peso[0]), estilos[0]])
					query = dictfetchall(c)
					for x in query:
						docs.append(x['nombre'])
						aux=Documento.objects.filter(nombre=x['nombre'])
						if len(aux)>0:
							yourdocumentos.append(aux[0])
			elif len(estilos)==2:
				with connection.cursor() as c:
					c.execute("select c.nombre, c.puntuacion, SUM(c.peso) as peso from((SELECT a.id, a.nombre, a.puntuacion, b.estilo, (b.peso * %s) as peso FROM sistema_documento as a join sistema_estilo as b on a.id = b.documento_id where estilo=%s) union (SELECT a.id, a.nombre, a.puntuacion, b.estilo, (b.peso * %s) as peso FROM sistema_documento as a join sistema_estilo as b on a.id = b.documento_id where estilo=%s)) as c group by c.nombre, c.puntuacion order by peso desc, puntuacion desc", [int(peso[0]), estilos[0], int(peso[1]), estilos[1]])
					query = dictfetchall(c)
					for x in query:
						docs.append(x['nombre'])
						aux=Documento.objects.filter(nombre=x['nombre'])
						if len(aux)>0:
							yourdocumentos.append(aux[0])
			elif len(estilos)==3:
				with connection.cursor() as c:
					c.execute("select c.nombre, c.puntuacion, SUM(c.peso) as peso from((SELECT a.id, a.nombre, a.puntuacion, b.estilo, (b.peso * %s) as peso FROM sistema_documento as a join sistema_estilo as b on a.id = b.documento_id where estilo=%s) union (SELECT a.id, a.nombre, a.puntuacion, b.estilo, (b.peso * %s) as peso FROM sistema_documento as a join sistema_estilo as b on a.id = b.documento_id where estilo=%s) union (SELECT a.id, a.nombre, a.puntuacion, b.estilo, (b.peso * %s) as peso FROM sistema_documento as a join sistema_estilo as b on a.id = b.documento_id where estilo=%s)) as c group by c.nombre, c.puntuacion order by peso desc, puntuacion desc", [int(peso[0]), estilos[0], int(peso[1]), estilos[1], int(peso[2]), estilos[2]])
					query = dictfetchall(c)
					for x in query:
						docs.append(x['nombre'])
						aux=Documento.objects.filter(nombre=x['nombre'])
						if len(aux)>0:
							yourdocumentos.append(aux[0])
			else:
				with connection.cursor() as c:
					c.execute("select c.nombre, c.puntuacion, SUM(c.peso) as peso from((SELECT a.id, a.nombre, a.puntuacion, b.estilo, (b.peso * %s) as peso FROM sistema_documento as a join sistema_estilo as b on a.id = b.documento_id where estilo=%s) union (SELECT a.id, a.nombre, a.puntuacion, b.estilo, (b.peso * %s) as peso FROM sistema_documento as a join sistema_estilo as b on a.id = b.documento_id where estilo=%s) union (SELECT a.id, a.nombre, a.puntuacion, b.estilo, (b.peso * %s) as peso FROM sistema_documento as a join sistema_estilo as b on a.id = b.documento_id where estilo=%s) union (SELECT a.id, a.nombre, a.puntuacion, b.estilo, (b.peso * %s) as peso FROM sistema_documento as a join sistema_estilo as b on a.id = b.documento_id where estilo=%s)) as c group by c.nombre, c.puntuacion order by peso desc, puntuacion desc", [int(peso[0]), estilos[0], int(peso[1]), estilos[1], int(peso[2]), estilos[2], int(peso[3]), estilos[3]])
					query = dictfetchall(c)
					for x in query:
						docs.append(x['nombre'])
						aux=Documento.objects.filter(nombre=x['nombre'])
						if len(aux)>0:
							yourdocumentos.append(aux[0])
		# Si no hubo estilos fuertes o no hay documentos de los estilos fuertes, buscar los estilos medios y recomendarlos
		if len(yourdocumentos)==0:
			# visual
			if visual_level.argmax()==1:
				estilos.append('v')
				peso.append(perfil.visual)
			# auditivo
			if auditivo_level.argmax()==1:
				estilos.append('a')
				peso.append(perfil.auditivo)
			# lectura-escritura
			if lectura_level.argmax()==1:
				estilos.append('r')
				peso.append(perfil.lectura)
			# kinestésico
			if kinestesico_level.argmax()==1:
				estilos.append('k')
				peso.append(perfil.kinestesico)
			# Recomendar o buscar documentos
			if len(estilos)>0 and len(documentos)>0:
				if len(estilos)==1:
					with connection.cursor() as c:
						c.execute("select c.nombre, c.puntuacion, SUM(c.peso) as peso from ((SELECT a.id, a.nombre, a.puntuacion, b.estilo, (b.peso * %s) as peso FROM sistema_documento as a join sistema_estilo as b on a.id = b.documento_id where estilo=%s)) as c group by c.nombre, c.puntuacion order by peso desc, puntuacion desc", [int(peso[0]), estilos[0]])
						query = dictfetchall(c)
						for x in query:
							docs.append(x['nombre'])
							aux=Documento.objects.filter(nombre=x['nombre'])
							if len(aux)>0:
								yourdocumentos.append(aux[0])
				elif len(estilos)==2:
					with connection.cursor() as c:
						c.execute("select c.nombre, c.puntuacion, SUM(c.peso) as peso from((SELECT a.id, a.nombre, a.puntuacion, b.estilo, (b.peso * %s) as peso FROM sistema_documento as a join sistema_estilo as b on a.id = b.documento_id where estilo=%s) union (SELECT a.id, a.nombre, a.puntuacion, b.estilo, (b.peso * %s) as peso FROM sistema_documento as a join sistema_estilo as b on a.id = b.documento_id where estilo=%s)) as c group by c.nombre, c.puntuacion order by peso desc, puntuacion desc", [int(peso[0]), estilos[0], int(peso[1]), estilos[1]])
						query = dictfetchall(c)
						for x in query:
							docs.append(x['nombre'])
							aux=Documento.objects.filter(nombre=x['nombre'])
							if len(aux)>0:
								yourdocumentos.append(aux[0])
				elif len(estilos)==3:
					with connection.cursor() as c:
						c.execute("select c.nombre, c.puntuacion, SUM(c.peso) as peso from((SELECT a.id, a.nombre, a.puntuacion, b.estilo, (b.peso * %s) as peso FROM sistema_documento as a join sistema_estilo as b on a.id = b.documento_id where estilo=%s) union (SELECT a.id, a.nombre, a.puntuacion, b.estilo, (b.peso * %s) as peso FROM sistema_documento as a join sistema_estilo as b on a.id = b.documento_id where estilo=%s) union (SELECT a.id, a.nombre, a.puntuacion, b.estilo, (b.peso * %s) as peso FROM sistema_documento as a join sistema_estilo as b on a.id = b.documento_id where estilo=%s)) as c group by c.nombre, c.puntuacion order by peso desc, puntuacion desc", [int(peso[0]), estilos[0], int(peso[1]), estilos[1], int(peso[2]), estilos[2]])
						query = dictfetchall(c)
						for x in query:
							docs.append(x['nombre'])
							aux=Documento.objects.filter(nombre=x['nombre'])
							if len(aux)>0:
								yourdocumentos.append(aux[0])
				else:
					with connection.cursor() as c:
						c.execute("select c.nombre, c.puntuacion, SUM(c.peso) as peso from((SELECT a.id, a.nombre, a.puntuacion, b.estilo, (b.peso * %s) as peso FROM sistema_documento as a join sistema_estilo as b on a.id = b.documento_id where estilo=%s) union (SELECT a.id, a.nombre, a.puntuacion, b.estilo, (b.peso * %s) as peso FROM sistema_documento as a join sistema_estilo as b on a.id = b.documento_id where estilo=%s) union (SELECT a.id, a.nombre, a.puntuacion, b.estilo, (b.peso * %s) as peso FROM sistema_documento as a join sistema_estilo as b on a.id = b.documento_id where estilo=%s) union (SELECT a.id, a.nombre, a.puntuacion, b.estilo, (b.peso * %s) as peso FROM sistema_documento as a join sistema_estilo as b on a.id = b.documento_id where estilo=%s)) as c group by c.nombre, c.puntuacion order by peso desc, puntuacion desc", [int(peso[0]), estilos[0], int(peso[1]), estilos[1], int(peso[2]), estilos[2], int(peso[3]), estilos[3]])
						query = dictfetchall(c)
						for x in query:
							docs.append(x['nombre'])
							aux=Documento.objects.filter(nombre=x['nombre'])
							if len(aux)>0:
								yourdocumentos.append(aux[0])
		#para visual
		if visual_level.argmax()==0:
			perfil.visual='Fuerte'
		elif visual_level.argmax()==1:
			perfil.visual='Medio'
		elif visual_level.argmax()==2:
			perfil.visual='Bajo'
		if auditivo_level.argmax()==0:
			perfil.auditivo='Fuerte'
		elif auditivo_level.argmax()==1:
			perfil.auditivo='Medio'
		elif auditivo_level.argmax()==2:
			perfil.auditivo='Bajo'
		if lectura_level.argmax()==0:
			perfil.lectura='Fuerte'
		elif lectura_level.argmax()==1:
			perfil.lectura='Medio'
		elif lectura_level.argmax()==2:
			perfil.lectura='Bajo'
		if kinestesico_level.argmax()==0:
			perfil.kinestesico='Fuerte'
		elif kinestesico_level.argmax()==1:
			perfil.kinestesico='Medio'
		elif kinestesico_level.argmax()==2:
			perfil.kinestesico='Bajo'
	else:
		perfil = False
		is_profesor = False
		Recomendar=[]
		yourdocumentos=[]
	return render_to_response('material.html', {'temas':temas, 'otros':otros, 'yourdocumentos':yourdocumentos,'Recomendar':Recomendar,'documentos':documentos, 'todos':todos ,'plan':plan,'perfil':perfil, 'is_profesor':is_profesor}, context_instance=RequestContext(request))

# Vista de un documento
def documento(request, documento_id):
	temas = Tema.objects.all().order_by('posicion')
	documentos = Documento.objects.annotate(ntemas=Count('temas'))
	#documento
	doc = get_object_or_404(documentos, pk=documento_id)
	doc.visto+=1
	puntos = Rating.objects.filter(documento=doc).order_by('fecha').reverse()
	punto= puntos.aggregate(Avg('puntuacion'))
	puntos = puntos.values('usuario__imagen','puntuacion', 'usuario__usuario__username', 'texto', 'fecha')
	comentarios = Comentario.objects.filter(documento=doc)
	comentarios = comentarios.values('usuario__imagen','usuario__usuario__username','texto', 'fecha')
	interacciones = puntos.count()+comentarios.count()+doc.visto
	#doc = doc.annotate(Count('nombre'))
	#return HttpResponse(comentarios)
	#doc.puntuacion =  round(punto['puntuacion__avg'], 2)
	doc.save()
	if request.user.is_authenticated():
		perfil = Perfil.objects.get(usuario=request.user)
		profesor = Group.objects.filter(user=request.user, name='Profesores')
		is_profesor = len(profesor)>0
	else:
		perfil = False 
		is_profesor = False
		puntuacion = False
	#Documento.objects.get(id=documento_id)
	# Manejar puntuacion 
	if request.user.is_authenticated():
		raiting = Rating.objects.filter(usuario=perfil, documento=doc).values('usuario__imagen','puntuacion', 'usuario__usuario__username', 'texto', 'fecha')
		if len(raiting)>0:
			puntuacion = raiting[0]
		else:
			puntuacion=False
		visual_level = np.array([fuzz.interp_membership(visual, visual_hi, perfil.visual), fuzz.interp_membership(visual, visual_md, perfil.visual), fuzz.interp_membership(visual, visual_lo, perfil.visual)])
		auditivo_level = np.array([fuzz.interp_membership(auditivo, auditivo_hi, perfil.auditivo), fuzz.interp_membership(auditivo, auditivo_md, perfil.auditivo), fuzz.interp_membership(auditivo, auditivo_lo, perfil.auditivo)])
		lectura_level = np.array([fuzz.interp_membership(lectura, lectura_hi, perfil.lectura), fuzz.interp_membership(lectura, lectura_md, perfil.lectura), fuzz.interp_membership(lectura, lectura_lo, perfil.lectura)])
		kinestesico_level = np.array([fuzz.interp_membership(kinestesico, kinestesico_hi, perfil.kinestesico), fuzz.interp_membership(kinestesico, kinestesico_md, perfil.kinestesico), fuzz.interp_membership(kinestesico, kinestesico_lo, perfil.kinestesico)])
		#para visual
		if visual_level.argmax()==0:
			perfil.visual='Fuerte'
		elif visual_level.argmax()==1:
			perfil.visual='Medio'
		elif visual_level.argmax()==2:
			perfil.visual='Bajo'
		if auditivo_level.argmax()==0:
			perfil.auditivo='Fuerte'
		elif auditivo_level.argmax()==1:
			perfil.auditivo='Medio'
		elif auditivo_level.argmax()==2:
			perfil.auditivo='Bajo'
		if lectura_level.argmax()==0:
			perfil.lectura='Fuerte'
		elif lectura_level.argmax()==1:
			perfil.lectura='Medio'
		elif lectura_level.argmax()==2:
			perfil.lectura='Bajo'
		if kinestesico_level.argmax()==0:
			perfil.kinestesico='Fuerte'
		elif kinestesico_level.argmax()==1:
			perfil.kinestesico='Medio'
		elif kinestesico_level.argmax()==2:
			perfil.kinestesico='Bajo'
	plan = []
	for p in temas:
		# temas siguientes
		if p.activo:
			plan.append(p)
	documentos = Documento.objects.filter(puntuacion__gt=3.9).order_by('puntuacion').reverse()[:100]
	return render_to_response('doc.html', { 'plan':plan, 'documentos':documentos,'temas':temas, 'doc':doc, 'puntuacion':puntuacion,
	 'perfil':perfil, 'reviews':puntos, 'comentarios':comentarios, 'interacciones':interacciones, 'is_profesor':is_profesor}, context_instance=RequestContext(request))

@login_required
def comentar(request, documento_id):
	temas = Tema.objects.all().order_by('posicion')
	perfil = Perfil.objects.get(usuario=request.user)
	profesor = Group.objects.filter(user=request.user, name='Profesores')
	is_profesor = len(profesor)>0
	doc = get_object_or_404(Documento, pk=documento_id)
	if request.method == "POST":
		formulario = ComentarioForm(request.POST)
		if formulario.is_valid:
			newcomentario = request.POST['comentario']
			request.POST['comentario']=''
			if newcomentario!='':
				co = Comentario(usuario=perfil, documento=doc, texto=newcomentario)
				co.save()
				return HttpResponseRedirect("/doc/"+str(documento_id))
	else:
		formulario = ComentarioForm()
	plan = []
	for p in temas:
		if p.activo:
			plan.append(p)
	documentos = Documento.objects.filter(puntuacion__gt=3.9).order_by('puntuacion').reverse()[:100]
	return render_to_response('interacciones.html', { 'plan':plan,'documentos':documentos,'temas':temas, 'perfil':perfil, 'formulario':formulario, 'doc':doc, 'is_profesor':is_profesor}, context_instance=RequestContext(request))

@login_required
def opinar(request, documento_id):
	temas = Tema.objects.all().order_by('posicion')
	perfil = Perfil.objects.get(usuario=request.user)
	profesor = Group.objects.filter(user=request.user, name='Profesores')
	is_profesor = len(profesor)>0
	doc = get_object_or_404(Documento, pk=documento_id)
	raiting = Rating.objects.filter(usuario=perfil, documento=doc)
	if len(raiting)==0:
		raiting = Rating(usuario=perfil, documento=doc)
	else:
		raiting = raiting[0]
	if request.method == "POST":
		formulario = ReviewForm(request.POST, instance=raiting)
		if formulario.is_valid:
			formulario.save()
			return HttpResponseRedirect("/doc/"+str(documento_id))
	else:
		formulario = ReviewForm(instance=raiting)
	plan = []
	for p in temas:
		if p.activo:
			plan.append(p)
	documentos = Documento.objects.filter(puntuacion__gt=3.9).order_by('puntuacion').reverse()[:100]
	return render_to_response('review.html', { 'plan':plan,'documentos':documentos,'temas':temas, 'perfil':perfil, 'formulario':formulario, 'doc':doc, 'is_profesor':is_profesor}, context_instance=RequestContext(request))

# función para raw SQL 
def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

# Actualizar estilos de aprendizaje logica difusa
def actualizarEA2(user):
	estil = np.array([0, 0, 0, 0], dtype='float')
	perfil = Perfil.objects.get(usuario=user)
	with connection.cursor() as c:
		t = Parametro.objects.filter(nombre='historico')
		c.execute("select estilo, SUM(peso/100) as valor from sistema_estilo as a join (SELECT puntuacion, documento_id, usuario_id, fecha FROM sistema_rating where usuario_id = %s and fecha > now() - interval '%s month') as b on a.documento_id=b.documento_id where puntuacion=5 group by estilo;", [user.id, int(t[0].valor)])
		#c.execute("select estilo, AVG(peso)as peso, count(*) as cant, AVG(puntuacion) as raiting from sistema_estilo as a join (SELECT puntuacion, documento_id, usuario_id, fecha FROM sistema_rating where usuario_id = %s and fecha > now() - interval '%s month') as b on a.documento_id=b.documento_id group by estilo order by raiting desc, peso desc, cant desc;", [user.id, int(t[0].valor)])
		query = dictfetchall(c)
		c.execute("select estilo, SUM(peso/100*1/2) as valor from sistema_estilo as a join (SELECT puntuacion, documento_id, usuario_id, fecha FROM sistema_rating where usuario_id = %s and fecha > now() - interval '%s month') as b on a.documento_id=b.documento_id where puntuacion=4 group by estilo;", [user.id, int(t[0].valor)])
		query4 = dictfetchall(c)
		c.execute("select estilo, SUM(-1*peso/100*1/puntuacion) as valor from sistema_estilo as a join (SELECT puntuacion, documento_id, usuario_id, fecha FROM sistema_rating where usuario_id = %s and fecha > now() - interval '%s month') as b on a.documento_id=b.documento_id where puntuacion<3 group by estilo;", [user.id, int(t[0].valor)])
		queryn = dictfetchall(c)
		for j in query:
			#x =  j['cant'] * j['peso'] / 100 * float(j['raiting']) / 5
			if j['estilo']=='v':
				estil[0] += round(j['valor'], 4)
				# perfil.visual = fuzz.defuzz(visual, visual_hi, 'centroid')
			elif j['estilo']=='a':
				estil[1] += round(j['valor'], 4)
				# perfil.auditivo = fuzz.defuzz(auditivo, auditivo_hi, 'centroid')
			elif j['estilo']=='r':
				estil[2] += round(j['valor'], 4)
				# perfil.lectura = fuzz.defuzz(lectura, lectura_hi, 'centroid')
			elif j['estilo']=='k':
				estil[3] += round(j['valor'], 4)
				# perfil.kinestesico = fuzz.defuzz(kinestesico, kinestesico_hi, 'centroid')
		for j in query4:
			#x =  j['cant'] * j['peso'] / 100 * float(j['raiting']) / 5
			if j['estilo']=='v':
				estil[0] += round(j['valor'], 4)
				# perfil.visual = fuzz.defuzz(visual, visual_hi, 'centroid')
			elif j['estilo']=='a':
				estil[1] += round(j['valor'], 4)
				# perfil.auditivo = fuzz.defuzz(auditivo, auditivo_hi, 'centroid')
			elif j['estilo']=='r':
				estil[2] += round(j['valor'], 4)
				# perfil.lectura = fuzz.defuzz(lectura, lectura_hi, 'centroid')
			elif j['estilo']=='k':
				estil[3] += round(j['valor'], 4)
		for j in queryn:
			#x =  j['cant'] * j['peso'] / 100 * float(j['raiting']) / 5
			if j['estilo']=='v':
				estil[0] += round(j['valor'], 4)
				# perfil.visual = fuzz.defuzz(visual, visual_hi, 'centroid')
			elif j['estilo']=='a':
				estil[1] += round(j['valor'], 4)
				# perfil.auditivo = fuzz.defuzz(auditivo, auditivo_hi, 'centroid')
			elif j['estilo']=='r':
				estil[2] += round(j['valor'], 4)
				# perfil.lectura = fuzz.defuzz(lectura, lectura_hi, 'centroid')
			elif j['estilo']=='k':
				estil[3] += round(j['valor'], 4)
		# Normalizar indices de estilos	
		maximo= estil.max()
		if maximo>0:
			estil[estil<0]=0
			for i in range(0,len(estil)):
				estil[i] = round(estil[i]/maximo *16, 4)
			# Verificar si hubo interacción antes
			visual_level = np.array([fuzz.interp_membership(visual, visual_hi, perfil.visual), fuzz.interp_membership(visual, visual_md, perfil.visual), fuzz.interp_membership(visual, visual_lo, perfil.visual)])
			auditivo_level = np.array([fuzz.interp_membership(auditivo, auditivo_hi, perfil.auditivo), fuzz.interp_membership(auditivo, auditivo_md, perfil.auditivo), fuzz.interp_membership(auditivo, auditivo_lo, perfil.auditivo)])
			lectura_level = np.array([fuzz.interp_membership(lectura, lectura_hi, perfil.lectura), fuzz.interp_membership(lectura, lectura_md, perfil.lectura), fuzz.interp_membership(lectura, lectura_lo, perfil.lectura)])
			kinestesico_level = np.array([fuzz.interp_membership(kinestesico, kinestesico_hi, perfil.kinestesico), fuzz.interp_membership(kinestesico, kinestesico_md, perfil.kinestesico), fuzz.interp_membership(kinestesico, kinestesico_lo, perfil.kinestesico)])
			# reglas para 
			visual_o = np.array([fuzz.interp_membership(visual, visual_hi, estil[0]), fuzz.interp_membership(visual, visual_md, estil[0]), fuzz.interp_membership(visual, visual_lo, estil[0])])
			auditivo_o = np.array([fuzz.interp_membership(auditivo, auditivo_hi, estil[1]), fuzz.interp_membership(auditivo, auditivo_md, estil[1]), fuzz.interp_membership(auditivo, auditivo_lo, estil[1])])
			lectura_o = np.array([fuzz.interp_membership(lectura, lectura_hi, estil[2]), fuzz.interp_membership(lectura, lectura_md, estil[2]), fuzz.interp_membership(lectura, lectura_lo, estil[2])])
			kinestesico_o = np.array([fuzz.interp_membership(kinestesico, kinestesico_hi, estil[3]), fuzz.interp_membership(kinestesico, kinestesico_md, estil[3]), fuzz.interp_membership(kinestesico, kinestesico_lo, estil[3])])
			# Inferencia
			#visual
			## SI visual de la consulta  es fuerte y diferente del visual actual ENTONCES visual es fuerte 
			if visual_o.argmax() == 0 and visual_level.argmax() != 0:
				perfil.visual = fuzz.defuzz(visual, visual_hi, 'som')
			## SI visual de consulta es medio y diferente al visual actual ENTONCES visual es medio
			elif visual_o.argmax() == 1 and visual_level.argmax() != 1:
				perfil.visual = fuzz.defuzz(visual, visual_md, 'som')
			## SI visual de la consulta es bajo y visual actual es fuerte  ENTONCES visual es medio 
			elif visual_o.argmax() == 2 and visual_level.argmax() ==0:
				perfil.visual = fuzz.defuzz(visual, visual_md, 'som')
			## SI visual de consulta es bajo y visual actual es medio ENTONCES visual es bajo
			elif visual_o.argmax() == 2 and visual_level.argmax() == 1 :
				perfil.visual = fuzz.defuzz(visual, visual_lo, 'som')
			#auditivo
			## SI auditivo de la consulta  es fuerte y diferente del auditivo actual ENTONCES auditivo es fuerte 
			if auditivo_o.argmax() == 0 and auditivo_level.argmax() != 0:
				perfil.auditivo = fuzz.defuzz(auditivo, auditivo_hi, 'som')
			## SI auditivo de consulta es medio y diferente al auditivo actual ENTONCES auditivo es medio
			elif auditivo_o.argmax() == 1 and auditivo_level.argmax() != 1:
				perfil.auditivo = fuzz.defuzz(auditivo, auditivo_md, 'som')
			## SI auditivo de la consulta es bajo y auditivo actual es fuerte  ENTONCES auditivo es medio 
			elif auditivo_o.argmax() == 2 and auditivo_level.argmax() ==0:
				perfil.auditivo = fuzz.defuzz(auditivo, auditivo_md, 'som')
			## SI auditivo de consulta es bajo y auditivo actual es medio ENTONCES auditivo es bajo
			elif auditivo_o.argmax() == 2 and auditivo_level.argmax() == 1 :
				perfil.auditivo = fuzz.defuzz(auditivo, auditivo_lo, 'som')
			#lectura
			## SI lectura de la consulta  es fuerte y diferente del lectura actual ENTONCES lectura es fuerte 
			if lectura_o.argmax() == 0 and lectura_level.argmax() != 0:
				perfil.lectura = fuzz.defuzz(lectura, lectura_hi, 'som')
			## SI lectura de consulta es medio y diferente al lectura actual ENTONCES lectura es medio
			elif lectura_o.argmax() == 1 and lectura_level.argmax() != 1:
				perfil.lectura = fuzz.defuzz(lectura, lectura_md, 'som')
			## SI lectura de la consulta es bajo y lectura actual es fuerte  ENTONCES lectura es medio 
			elif lectura_o.argmax() == 2 and lectura_level.argmax() ==0:
				perfil.lectura = fuzz.defuzz(lectura, lectura_md, 'som')
			## SI lectura de consulta es bajo y lectura actual es medio ENTONCES lectura es bajo
			elif lectura_o.argmax() == 2 and lectura_level.argmax() == 1 :
				perfil.lectura = fuzz.defuzz(lectura, lectura_lo, 'som')
			#kinestesico
			## SI kinestesico de la consulta  es fuerte y diferente del kinestesico actual ENTONCES kinestesico es fuerte 
			if kinestesico_o.argmax() == 0 and kinestesico_level.argmax() != 0:
				perfil.kinestesico = fuzz.defuzz(kinestesico, kinestesico_hi, 'som')
			## SI kinestesico de consulta es medio y diferente al kinestesico actual ENTONCES kinestesico es medio
			elif kinestesico_o.argmax() == 1 and kinestesico_level.argmax() != 1:
				perfil.kinestesico = fuzz.defuzz(kinestesico, kinestesico_md, 'som')
			## SI kinestesico de la consulta es bajo y kinestesico actual es fuerte  ENTONCES kinestesico es medio 
			elif kinestesico_o.argmax() == 2 and kinestesico_level.argmax() ==0:
				perfil.kinestesico = fuzz.defuzz(kinestesico, kinestesico_md, 'som')
			## SI kinestesico de consulta es bajo y kinestesico actual es medio ENTONCES kinestesico es bajo
			elif kinestesico_o.argmax() == 2 and kinestesico_level.argmax() == 1 :
				perfil.kinestesico = fuzz.defuzz(kinestesico, kinestesico_lo, 'som')			
		elif np.any(estil<(-3)):
			visual_level = np.array([fuzz.interp_membership(visual, visual_hi, perfil.visual), fuzz.interp_membership(visual, visual_md, perfil.visual), fuzz.interp_membership(visual, visual_lo, perfil.visual)])
			auditivo_level = np.array([fuzz.interp_membership(auditivo, auditivo_hi, perfil.auditivo), fuzz.interp_membership(auditivo, auditivo_md, perfil.auditivo), fuzz.interp_membership(auditivo, auditivo_lo, perfil.auditivo)])
			lectura_level = np.array([fuzz.interp_membership(lectura, lectura_hi, perfil.lectura), fuzz.interp_membership(lectura, lectura_md, perfil.lectura), fuzz.interp_membership(lectura, lectura_lo, perfil.lectura)])
			kinestesico_level = np.array([fuzz.interp_membership(kinestesico, kinestesico_hi, perfil.kinestesico), fuzz.interp_membership(kinestesico, kinestesico_md, perfil.kinestesico), fuzz.interp_membership(kinestesico, kinestesico_lo, perfil.kinestesico)])
			#visual
			if estil[0]<(-2) and visual_level.argmax()==0:
				perfil.visual = fuzz.defuzz(visual, visual_md, 'som')
			elif estil[0]<(-4):
				perfil.visual = fuzz.defuzz(visual, visual_lo, 'som')
			#auditivo
			if estil[1]<(-2) and auditivo_level.argmax()==0:
				perfil.auditivo = fuzz.defuzz(auditivo, auditivo_md, 'som')
			elif estil[1]<(-4):
				perfil.auditivo = fuzz.defuzz(auditivo, auditivo_lo, 'som')
			#lectura
			if estil[0]<(-2) and lectura_level.argmax()==0:
				perfil.lectura = fuzz.defuzz(lectura, lectura_md, 'som')
			elif estil[0]<(-4):
				perfil.lectura = fuzz.defuzz(lectura, lectura_lo, 'som')
			#kinestesico
			if estil[0]<(-2) and kinestesico_level.argmax()==0:
				perfil.kinestesico = fuzz.defuzz(kinestesico, kinestesico_md, 'som')
			elif estil[0]<(-4):
				perfil.kinestesico = fuzz.defuzz(kinestesico, kinestesico_lo, 'som')
		perfil.save()


# Puntuar
@login_required
def Puntuar(request):
	valor = request.GET.get('valor')
	next = request.GET.get('next')
	doc = Documento.objects.get(id=next)
	es= Estilo.objects.filter(documento=doc)
	perfil = Perfil.objects.get(usuario=request.user)
	raiting = Rating.objects.filter(usuario=perfil, documento=doc)
	#anterior=0
	if len(raiting)==0:
		ra = Rating(usuario=perfil, documento=doc, puntuacion=valor)
		ra.save()
	else:
		#Si hay un raiting
		#anterior=raiting[0].puntuacion
		raiting[0].puntuacion=int(valor)
		raiting[0].save()
	punto = Rating.objects.filter(documento=doc).order_by('puntuacion').aggregate(Avg('puntuacion'))
	doc.puntuacion =  round(punto['puntuacion__avg'],2)
	doc.save()
	# Ajuste de los indices de los estilos de aprendizaje con logica difusa
	actualizarEA2(request.user)	
	return HttpResponseRedirect("/doc/"+str(next))

# Mostrar Estilos de aprendizaje
@login_required
def Estilos(request):
	temas = Tema.objects.all().order_by('posicion')
	#documentos = Documento.objects.order_by('fecha').reverse()[:5]
	perfil = Perfil.objects.get(usuario=request.user)
	perfil1 = Perfil.objects.get(usuario=request.user)
	profesor = Group.objects.filter(user=request.user, name='Profesores')
	is_profesor = len(profesor)>0
	# Obtener planificación de los temas para guiar
	plan = []
	for p in temas:
		if p.activo:
			plan.append(p)
	documentos = Documento.objects.filter(puntuacion__gt=3.9).order_by('puntuacion').reverse()[:100]
	#Colocar lo de fuerte, medio, debil
	visual_level = np.array([fuzz.interp_membership(visual, visual_hi, perfil.test_visual), fuzz.interp_membership(visual, visual_md, perfil.test_visual), fuzz.interp_membership(visual, visual_lo, perfil.test_visual)])
	auditivo_level = np.array([fuzz.interp_membership(auditivo, auditivo_hi, perfil.test_auditivo), fuzz.interp_membership(auditivo, auditivo_md, perfil.test_auditivo), fuzz.interp_membership(auditivo, auditivo_lo, perfil.test_auditivo)])
	lectura_level = np.array([fuzz.interp_membership(lectura, lectura_hi, perfil.test_lectura), fuzz.interp_membership(lectura, lectura_md, perfil.test_lectura), fuzz.interp_membership(lectura, lectura_lo, perfil.test_lectura)])
	kinestesico_level = np.array([fuzz.interp_membership(kinestesico, kinestesico_hi, perfil.test_kinestesico), fuzz.interp_membership(kinestesico, kinestesico_md, perfil.test_kinestesico), fuzz.interp_membership(kinestesico, kinestesico_lo, perfil.test_kinestesico)])
	#para visual
	if visual_level.argmax()==0:
		perfil.test_visual='Fuerte'
	elif visual_level.argmax()==1:
		perfil.test_visual='Medio'
	elif visual_level.argmax()==2:
		perfil.test_visual='Bajo'
	if auditivo_level.argmax()==0:
		perfil.test_auditivo='Fuerte'
	elif auditivo_level.argmax()==1:
		perfil.test_auditivo='Medio'
	elif auditivo_level.argmax()==2:
		perfil.test_auditivo='Bajo'
	if lectura_level.argmax()==0:
		perfil.test_lectura='Fuerte'
	elif lectura_level.argmax()==1:
		perfil.test_lectura='Medio'
	elif lectura_level.argmax()==2:
		perfil.test_lectura='Bajo'
	if kinestesico_level.argmax()==0:
		perfil.test_kinestesico='Fuerte'
	elif kinestesico_level.argmax()==1:
		perfil.test_kinestesico='Medio'
	elif kinestesico_level.argmax()==2:
		perfil.test_kinestesico='Bajo'
	#return HttpResponse(str(per)+str(auditivo_level)+str(lectura_level)+ str(kinestesico_level))
	visual_level = np.array([fuzz.interp_membership(visual, visual_hi, perfil.visual), fuzz.interp_membership(visual, visual_md, perfil.visual), fuzz.interp_membership(visual, visual_lo, perfil.visual)])
	auditivo_level = np.array([fuzz.interp_membership(auditivo, auditivo_hi, perfil.auditivo), fuzz.interp_membership(auditivo, auditivo_md, perfil.auditivo), fuzz.interp_membership(auditivo, auditivo_lo, perfil.auditivo)])
	lectura_level = np.array([fuzz.interp_membership(lectura, lectura_hi, perfil.lectura), fuzz.interp_membership(lectura, lectura_md, perfil.lectura), fuzz.interp_membership(lectura, lectura_lo, perfil.lectura)])
	kinestesico_level = np.array([fuzz.interp_membership(kinestesico, kinestesico_hi, perfil.kinestesico), fuzz.interp_membership(kinestesico, kinestesico_md, perfil.kinestesico), fuzz.interp_membership(kinestesico, kinestesico_lo, perfil.kinestesico)])
	#para visual
	if visual_level.argmax()==0:
		perfil.visual='Fuerte'
	elif visual_level.argmax()==1:
		perfil.visual='Medio'
	elif visual_level.argmax()==2:
		perfil.visual='Bajo'
	if auditivo_level.argmax()==0:
		perfil.auditivo='Fuerte'
	elif auditivo_level.argmax()==1:
		perfil.auditivo='Medio'
	elif auditivo_level.argmax()==2:
		perfil.auditivo='Bajo'
	if lectura_level.argmax()==0:
		perfil.lectura='Fuerte'
	elif lectura_level.argmax()==1:
		perfil.lectura='Medio'
	elif lectura_level.argmax()==2:
		perfil.lectura='Bajo'
	if kinestesico_level.argmax()==0:
		perfil.kinestesico='Fuerte'
	elif kinestesico_level.argmax()==1:
		perfil.kinestesico='Medio'
	elif kinestesico_level.argmax()==2:
		perfil.kinestesico='Bajo'
	return render_to_response('estilos.html', {'temas':temas, 'documentos':documentos, 'plan':plan,'perfil':perfil, 'perfil1':perfil1, 'is_profesor':is_profesor}, context_instance=RequestContext(request))

# Correlación de Pearson entre dos usuarios
def pearson(user, u1):
    sum_xy = 0
    sum_x = 0
    sum_y = 0
    sum_x2 = 0
    sum_y2 = 0
    n = 4
    sum_xy = (user.visual*u1.visual)+(user.auditivo*u1.auditivo)+(user.lectura*u1.lectura)+(user.kinestesico*u1.kinestesico)
    sum_x = user.visual + user.auditivo + user.lectura + user.kinestesico
    sum_y = u1.visual + u1.auditivo + u1.lectura + u1.kinestesico
    sum_x2 = pow(user.visual, 2) + pow(user.auditivo, 2) + pow(user.lectura, 2) + pow(user.kinestesico, 2)
    sum_y2 = pow(u1.visual, 2) + pow(u1.auditivo, 2) + pow(u1.lectura, 2) + pow(u1.kinestesico, 2)
    # now compute denominator
    denominator = sqrt(sum_x2 - pow(sum_x, 2) / n) * sqrt(sum_y2 - pow(sum_y, 2) / n)
    if denominator == 0:
        return 0
    else:
        return (sum_xy - (sum_x * sum_y) / n) / denominator

# Calcular la lista de vecinos según Pearson
def computeNearestNeighbor(user):
    """creates a sorted list of users based on their distance to username"""
    users = Perfil.objects.all()
    p = Parametro.objects.filter(nombre='pearson')
    distances = []
    for u in users:
        if u != user:
            distance = pearson(user, u)
            #ver que sea mayor a 0.5 la correlación
            if distance>=p[0].valor :
            	distances.append((str(u), distance))
    # sort based on distance -- closest first
    distances.sort(key=lambda userTuple: userTuple[1], reverse=True)
    return distances

# Dar la recomendación de n documentos segun k vecinos
def recommend(user):
	"""Give list of recommendations"""
	recommendations = {}
	# first get list of users  ordered by nearness
	perfil = Perfil.objects.get(usuario=user)
	nearest = computeNearestNeighbor(perfil)
	#return nearest
	# now get the ratings for the user
	userRatings = Rating.objects.filter(usuario=perfil)
	# determine the total distance
	totalDistance = 0.0
	kvecinos = Parametro.objects.filter(nombre='kvecinos')
	if len(nearest) >= int(kvecinos[0].valor):
		k = 10
	else :
		k = len(nearest)
	for i in range(k):
		totalDistance += nearest[i][1]
	# now iterate through the k nearest neighbors
	# accumulating their ratings
	for i in range(k):
		# compute slice of pie 
		weight = nearest[i][1] / totalDistance
		# get the name of the person
		name = nearest[i][0]
		# get the ratings for this person
		usu = User.objects.get(username=name)
		per = Perfil.objects.get(usuario=usu)
		neighborRatings = Rating.objects.filter(usuario=per)
		for doc in neighborRatings:
			if not userRatings.filter(documento=doc.documento):
				if doc not in recommendations:
					recommendations[str(doc.documento)] = (doc.puntuacion * weight)
				else:
					recommendations[str(doc.documento)] = (recommendations[str(doc.documento)] + doc.puntuacion * weight)
   	# now make list from dictionary
	recommendations = list(recommendations.items())
	recommendations.sort(key=lambda docTuple: docTuple[1], reverse=True)
   	# Return the first n items
	return recommendations
	#return neighborRatings

@login_required
def Pinicio(request):
	profesor = Group.objects.filter(user=request.user, name='Profesores')
	is_profesor = len(profesor)>0
	temas = Tema.objects.all().order_by('posicion')
	perfil = Perfil.objects.get(usuario=request.user)
	usuarios = Perfil.objects.all().count()
	ra = Rating.objects.all().count()
	co = Comentario.objects.all().count()
	total = ra+co
	if is_profesor:
		parametros = Parametro.objects.all()
		ndocumentos= Documento.objects.all().count()
		plan = []
		for p in temas:
			# temas siguientes
			if p.activo:
				plan.append(p)
		ac_temas= len(plan)
		documentos = Documento.objects.filter(puntuacion__gt=3.9).order_by('puntuacion').reverse()[:100]
		visual_level = np.array([fuzz.interp_membership(visual, visual_hi, perfil.visual), fuzz.interp_membership(visual, visual_md, perfil.visual), fuzz.interp_membership(visual, visual_lo, perfil.visual)])
		auditivo_level = np.array([fuzz.interp_membership(auditivo, auditivo_hi, perfil.auditivo), fuzz.interp_membership(auditivo, auditivo_md, perfil.auditivo), fuzz.interp_membership(auditivo, auditivo_lo, perfil.auditivo)])
		lectura_level = np.array([fuzz.interp_membership(lectura, lectura_hi, perfil.lectura), fuzz.interp_membership(lectura, lectura_md, perfil.lectura), fuzz.interp_membership(lectura, lectura_lo, perfil.lectura)])
		kinestesico_level = np.array([fuzz.interp_membership(kinestesico, kinestesico_hi, perfil.kinestesico), fuzz.interp_membership(kinestesico, kinestesico_md, perfil.kinestesico), fuzz.interp_membership(kinestesico, kinestesico_lo, perfil.kinestesico)])
		#para visual
		if visual_level.argmax()==0:
			perfil.visual='Fuerte'
		elif visual_level.argmax()==1:
			perfil.visual='Medio'
		elif visual_level.argmax()==2:
			perfil.visual='Bajo'
		if auditivo_level.argmax()==0:
			perfil.auditivo='Fuerte'
		elif auditivo_level.argmax()==1:
			perfil.auditivo='Medio'
		elif auditivo_level.argmax()==2:
			perfil.auditivo='Bajo'
		if lectura_level.argmax()==0:
			perfil.lectura='Fuerte'
		elif lectura_level.argmax()==1:
			perfil.lectura='Medio'
		elif lectura_level.argmax()==2:
			perfil.lectura='Bajo'
		if kinestesico_level.argmax()==0:
			perfil.kinestesico='Fuerte'
		elif kinestesico_level.argmax()==1:
			perfil.kinestesico='Medio'
		elif kinestesico_level.argmax()==2:
			perfil.kinestesico='Bajo'
		return render_to_response('profesor_inicio.html', {'documentos':documentos,'plan':plan ,'temas':temas, 'perfil':perfil, 'is_profesor':is_profesor, 'parametros':parametros, 'ndocumentos':ndocumentos, 'ac_temas':ac_temas, 'usuarios':usuarios, 'ra':ra, 'co':co, 'total':total}, context_instance=RequestContext(request))
	else:
		return HttpResponseRedirect("/")