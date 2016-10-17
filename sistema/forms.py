from django import forms
from django.contrib.auth.models import User
from sistema.models import Comentario, Perfil, Rating

class RegistroForm(forms.ModelForm):
	class Meta:
		model = User
		fields = ('first_name', 'last_name', 'email')

class PerfilForm(forms.Form):
	image = forms.ImageField( label="Foto de Perfil", required=True)

class ComentarioForm(forms.Form):
	comentario = forms.CharField(widget=forms.Textarea, max_length=200, min_length=1, help_text='Escribe tu comentario')

class ReviewForm(forms.ModelForm):
	class Meta:
		model = Rating
		fields = ('puntuacion', 'texto')

class TestForm(forms.Form):
	p1 = forms.MultipleChoiceField(required=False,label="Está ayudando a una persona que desea ir al aeropuerto, al centro de la ciudad o a la estación del ferrocarril. Ud.:" ,widget = forms.CheckboxSelectMultiple,
		choices=(
			('K',"Iría con ella."),
			('A',"Le diría como llegar."),
			('R', "Le diría las indicaciones por escrito (sin un mapa)."),
			('V', "Le daría un mapa."),)
		)
	p2 = forms.MultipleChoiceField(required=False,label="No está seguro si una palabra se escribe como trascendente o tracendente, Ud.:" ,widget = forms.CheckboxSelectMultiple,
		choices=(
			('V',"Vería las palabras en su mente y elegiría la que mejor luce."),
			('A',"Pensaría en cómo suena cada palabra y elegiría una."),
			('R', "Las buscaría en un diccionario."),
			('K', "Escribiría ambas palabras y elegiría una."),)
		)
	p3 = forms.MultipleChoiceField(required=False,label="Está planeando unas vacaciones para un grupo de personas y desearía la retroalimentación de ellos sobre el plan. Ud.:" ,widget = forms.CheckboxSelectMultiple,
		choices=(
			('K',"Describiría algunos de los atractivos del viaje."),
			('V',"Utilizaría un mapa o un sitio web para mostrar los lugares."),
			('R', "Les daría una copia del itinerario impreso."),
			('A', "Les llamaría por teléfono, les escribiría o les enviaría un e-mail."),)
		)
	p4 = forms.MultipleChoiceField(required=False,label="Va a cocinar algún platillo especial para su familia. Ud.:" ,widget = forms.CheckboxSelectMultiple,
		choices=(
			('K',"Cocinaría algo que conoce sin la necesidad de instrucciones."),
			('A',"Pediría sugerencias a sus amigos."),
			('V', "Hojearía un libro de cocina para tomar ideas de las fotografías."),
			('R', "Utilizaría un libro de cocina donde sabe que hay una buena receta."),)
		)
	p5 = forms.MultipleChoiceField(required=False,label="Un grupo de turistas desea aprender sobre los parques o las reservas de vida salvaje en su área. Ud.:" ,widget = forms.CheckboxSelectMultiple,
		choices=(
			('A',"Les daría una plática acerca de parques o reservas de vida salvaje."),
			('V',"Les mostraría figuras de Internet, fotografías o libros con imágenes."),
			('K', "Los llevaría a un parque o reserva y daría una caminata con ellos."),
			('R', "Les daría libros o folletos sobre parques o reservas de vida salvaje."),)
		)
	p6 = forms.MultipleChoiceField(required=False,label="Está a punto de comprar una cámara digital o un teléfono móvil. ¿Además del precio, qué más influye en su decisión?" ,widget = forms.CheckboxSelectMultiple,
		choices=(
			('K',"Lo utiliza o lo prueba."),
			('R',"La lectura de los detalles acerca de las características del aparato."),
			('V', "El diseño del aparato es moderno y parece bueno."),
			('A', "Los comentarios del vendedor acerca de las características del aparato."),)
		)
	p7 = forms.MultipleChoiceField(required=False,label="Recuerde la vez cuando aprendió cómo hacer algo nuevo. Evite elegir una destreza física, como montar bicicleta. ¿Cómo aprendió mejor?" ,widget = forms.CheckboxSelectMultiple,
		choices=(
			('K',"Viendo una demostración."),
			('A',"Escuchando la explicación de alguien y haciendo preguntas."),
			('V', "Siguiendo pistas visuales en diagramas y gráficas."),
			('R', "Siguiendo instrucciones escritas en un manual o libro de texto."),)
		)
	p8 = forms.MultipleChoiceField(required=False,label="Tiene un problema con su rodilla. Preferiría que el doctor:" ,widget = forms.CheckboxSelectMultiple,
		choices=(
			('R',"Le diera una dirección web o algo para leer sobre el asunto."),
			('K',"Utilizara un modelo plástico de una rodilla para mostrarle qué está mal."),
			('A', "Le describiera qué está mal."),
			('V', "Le mostrara con un diagrama qué es lo que está mal."),)
		)
	p9 = forms.MultipleChoiceField(required=False,label="Desea aprender un nuevo programa, habilidad o juego de computadora. Ud. debe:" ,widget = forms.CheckboxSelectMultiple,
		choices=(
			('R',"Leer las instrucciones escritas que vienen con el programa."),
			('A',"Platicar con personas que conocen el programa."),
			('K', "Utilizar los controles o el teclado."),
			('V', "Seguir los diagramas del libro que vienen con el programa."),)
		)
	p10 = forms.MultipleChoiceField(required=False,label="Le gustan los sitios web que tienen:" ,widget = forms.CheckboxSelectMultiple,
		choices=(
			('K',"Cosas que se pueden picar, mover o probar."),
			('V',"Un diseño interesante y características visuales."),
			('R', "Descripciones escritas interesantes, características y explicaciones."),
			('A', "Canales de audio para oír música, programas o entrevistas."),)
		)
	p11 = forms.MultipleChoiceField(required=False,label="Además del precio, ¿Qué influiría más en su decisión de comprar un nuevo libro de no ficción?" ,widget = forms.CheckboxSelectMultiple,
		choices=(
			('V',"La apariencia le resulta atractiva."),
			('R',"Una lectura rápida de algunas partes del libro."),
			('A', "Un amigo le habla del libro y se lo recomienda."),
			('K', "Tiene historias, experiencias y ejemplos de la vida real."),)
		)
	p12 = forms.MultipleChoiceField(required=False,label="Está utilizando un libro, CD o sitio web para aprender cómo tomar fotografías con su nueva cámara digital. Le gustaría tener:" ,widget = forms.CheckboxSelectMultiple,
		choices=(
			('A',"La oportunidad de hacer preguntas y que le hablen sobre la cámara y sus características."),
			('R',"Instrucciones escritas con claridad, con características y puntos sobre qué hacer."),
			('V', "Diagramas que muestren la cámara y que hace cada una de sus partes."),
			('K', "Muchos ejemplos de fotografías buenas y malas y cómo mejorar éstas."),)
		)
	p13 = forms.MultipleChoiceField(required=False,label="Prefiere a un profesor o un expositor que utiliza:" ,widget = forms.CheckboxSelectMultiple,
		choices=(
			('K',"Demostraciones, modelos o sesiones prácticas."),
			('A',"Preguntas y respuestas, charlas, grupos de discusión u oradores invitados."),
			('R', "Folletos, libros o lecturas."),
			('V', "Diagramas, esquemas o gráficas."),)
		)
	p14 = forms.MultipleChoiceField(required=False,label="Ha acabado una competencia o una prueba y quisiera una retroalimentación. Quisiera tener la retroalimentación:" ,widget = forms.CheckboxSelectMultiple,
		choices=(
			('K',"Utilizando ejemplos de lo que ha hecho."),
			('R',"Utilizando una descripción escrita de sus resultados."),
			('A', "Escuchando a alguien haciendo una revisión detallada de su desempeño."),
			('V', "Utilizando gráficas que muestren lo que ha conseguido"),)
		)
	p15 = forms.MultipleChoiceField(required=False,label="Va a elegir sus alimentos en un restaurante o café. Ud.:" ,widget = forms.CheckboxSelectMultiple,
		choices=(
			('K',"Elegiría algo que ya ha probado en ese lugar."),
			('A',"Escucharía al mesero o pediría recomendaciones a sus amigos."),
			('R', "Elegiría a partir de las descripciones del menú."),
			('V', "Observaría lo que otros están comiendo o las fotografías de cada platillo."),)
		)
	p16 = forms.MultipleChoiceField(required=False, label="Tiene que hacer un discurso importante para una conferencia o una ocasión especial. Ud.:" ,widget = forms.CheckboxSelectMultiple,
		choices=(
			('V',"Elaboraría diagramas o conseguiría gráficos que le ayuden a explicar las ideas."),
			('A',"Escribiría algunas palabras clave y práctica su discurso repetidamente."),
			('R', "Escribiría su discurso y se lo aprendería leyéndolo varias veces."),
			('K', "Conseguiría muchos ejemplos e historias para hacer la charla real y práctica."),)
		)	
