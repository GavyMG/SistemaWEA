from django.conf.urls import patterns, url


urlpatterns= patterns('sistema.views',
	url(r'^$', 'inicio', name="index"),
	url(r'^info/$', 'info', name="info"),
	url(r'^tema/(?P<tema_id>[0-9]+)/$', 'tema', name="tema"),
	url(r'^registro/$', 'registro', name="registro"),
	url(r'^login/$', 'iniciarSesion', name="login"),
	url(r'^logout/$', 'Salir', name="logout"),
	url(r'^inicial_test/$', 'inicial_test', name="inicial_test"),
	url(r'^editar_perfil/$', 'editar_perfil', name="editar_perfil"),
	url(r'^documentos/$', 'material', name="material"),
	url(r'^doc/(?P<documento_id>[0-9]+)/$', 'documento', name="doc"),
	url(r'^puntuar/$', 'Puntuar', name="puntuar"),
	url(r'^estilos/$', 'Estilos', name="estilos"),
	url(r'^cambio_password/$', 'Password_change', name="password_change"),
	url(r'^comentar/(?P<documento_id>[0-9]+)/$', 'comentar', name="comentar"),
	url(r'^editar_foto_perfil/$', 'subir_imagen', name="subir_imagen"),
	url(r'^profesor/$', 'Pinicio', name="Pinicio"),
	url(r'^opinar/(?P<documento_id>[0-9]+)/$', 'opinar', name="opinar"),
	)
