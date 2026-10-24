from django.contrib import admin

from . import models as m

for catalogo in (m.Comuna, m.Plataforma, m.Sistema, m.Tono, m.Arquetipo, m.Ambientacion, m.HerramientaSeguridad, m.Conducta):
    admin.site.register(catalogo, list_display=("nombre", "orden"), list_editable=("orden",), search_fields=("nombre",))


@admin.register(m.Tema)
class TemaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "categoria", "estado_por_defecto", "orden")
    list_filter = ("categoria",)
    list_editable = ("orden",)


class PerfilSistemaInline(admin.TabularInline):
    model = m.PerfilSistema
    extra = 0


class LimiteInline(admin.TabularInline):
    model = m.LimiteTema
    extra = 0


@admin.register(m.Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ("alias", "rol", "modalidad", "experiencia", "publicado", "es_demo")
    list_filter = ("rol", "modalidad", "experiencia", "publicado", "es_demo")
    search_fields = ("alias",)
    filter_horizontal = ("comunas", "plataformas", "tonos", "arquetipos", "ambientaciones", "herramientas", "conductas_no_tolera")
    inlines = [PerfilSistemaInline, LimiteInline]


admin.site.register(m.Interes, list_display=("de", "a", "creado"))
admin.site.register(m.Bloqueo, list_display=("de", "a", "creado"))
admin.site.register(m.Disponibilidad, list_display=("perfil", "fecha", "bloque"), list_filter=("perfil",))

admin.site.site_header = "Administración de Terrenar"
