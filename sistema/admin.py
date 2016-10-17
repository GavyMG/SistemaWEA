from django.contrib import admin

# Register your models here.
from .models import Tema, Documento, Perfil, Rating, Estilo, Comentario, Parametro

class EstiloInline(admin.StackedInline):
	model = Estilo
	extra = 1

class ComentarioInline(admin.StackedInline):
	model = Comentario
	extra = 0

class DocumentoAdmin(admin.ModelAdmin):
	fieldsets = [
	('Documento', {'fields': ['nombre', 'documento', 'temas']}),
	]
	inlines = [EstiloInline, ComentarioInline]

		

admin.site.register(Tema)
admin.site.register(Documento, DocumentoAdmin)
admin.site.register(Perfil)
admin.site.register(Parametro)
admin.site.register(Rating)
#admin.site.register(Comentario)