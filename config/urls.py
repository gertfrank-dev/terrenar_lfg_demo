"""La "carta": qué dirección lleva a qué vista."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from perfiles import views

urlpatterns = [
    path("", views.portada, name="portada"),
    path("entrar-demo/", views.entrar_demo, name="entrar_demo"),
    path("explorar/", views.explorar, name="explorar"),
    path("mi-perfil/", views.mi_perfil, name="mi_perfil"),
    path("ficha/<slug:paso>/", views.ficha, name="ficha"),
    path("p/<int:pk>/", views.perfil, name="perfil"),
    path("p/<int:pk>/interes/", views.interes, name="interes"),
    path("cuenta/", include("allauth.urls")),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
