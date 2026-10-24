"""
Tablas del sitio. Cada clase es una tabla en la base de datos.
El detalle y el porqué de cada campo está en MODELO-DATOS.md.
"""
from datetime import date

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

# Valores de los dados "cargados" (standard array). Cada uno se usa una sola vez.
STANDARD_ARRAY = (15, 14, 13, 12, 10, 8)
ATRIBUTOS = (
    ("atr_combate", "Combate"),
    ("atr_exploracion", "Exploración"),
    ("atr_interpretacion", "Interpretación"),
    ("atr_misterio", "Misterio e intriga"),
    ("atr_estrategia", "Estrategia"),
    ("atr_humor", "Humor"),
)
EJES = (
    # campo, nombre, extremo 1, extremo 5
    ("eje_enfoque", "Enfoque", "Narrativo", "Táctico"),
    ("eje_mundo", "Mundo", "Sandbox", "Lineal"),
    ("eje_reglas", "Reglas", "RAW estricto", "Regla de lo genial"),
    ("eje_ritmo", "Ritmo", "Ágil", "Pausado"),
    ("eje_profundidad", "Profundidad", "Ligera", "Inmersiva"),
    ("eje_intensidad", "Intensidad", "Aventura liviana", "Drama intenso"),
    ("letalidad", "Letalidad", "Mi personaje no muere", "Puede morir sin drama"),
)


def uno_a_cinco(**kw):
    return models.PositiveSmallIntegerField(
        default=3, validators=[MinValueValidator(1), MaxValueValidator(5)], **kw
    )


def dado(**kw):
    return models.PositiveSmallIntegerField(null=True, blank=True, choices=[(v, v) for v in STANDARD_ARRAY], **kw)


# ---------------------------------------------------------------- catálogos
class Catalogo(models.Model):
    """Base para listas simples que se editan desde el panel de administración."""

    nombre = models.CharField(max_length=80, unique=True)
    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        abstract = True
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre


class Comuna(Catalogo):
    pass


class Plataforma(Catalogo):
    pass


class Sistema(Catalogo):
    pass


class Tono(Catalogo):
    pass


class Arquetipo(Catalogo):
    pass


class Ambientacion(Catalogo):
    class Meta(Catalogo.Meta):
        verbose_name_plural = "ambientaciones"


class HerramientaSeguridad(Catalogo):
    class Meta(Catalogo.Meta):
        verbose_name_plural = "herramientas de seguridad"


class Conducta(Catalogo):
    pass


class Tema(Catalogo):
    """Tema de contenido para Líneas y Velos."""

    categoria = models.CharField(max_length=40)
    estado_por_defecto = models.CharField(max_length=10, default="ok")


# ---------------------------------------------------------------- perfil
class Perfil(models.Model):
    class Rol(models.TextChoices):
        JUGADOR = "jugador", "Jugador"
        MASTER = "master", "Máster"
        AMBOS = "ambos", "Jugador y máster"

    class Modalidad(models.TextChoices):
        PRESENCIAL = "presencial", "Presencial"
        ONLINE = "online", "Online"
        AMBAS = "ambas", "Presencial u online"

    class MesaPagada(models.TextChoices):
        GRATIS = "gratis", "Solo mesas gratis"
        PAGA = "paga", "Acepto pagar"
        COBRA = "cobra", "Cobro por mesa"

    class Experiencia(models.TextChoices):
        NUEVO = "nuevo", "Nuevo"
        INTERMEDIO = "intermedio", "Intermedio"
        VETERANO = "veterano", "Veterano"

    class Novatos(models.TextChoices):
        ENSENA = "ensena", "Me gusta enseñar"
        IGUAL = "igual", "Me da igual"
        EXPERTOS = "expertos", "Prefiero mesas con experiencia"

    class Gusto(models.TextChoices):
        SI = "si", "Sí"
        IGUAL = "igual", "Me da igual"
        NO = "no", "Prefiero que no"

    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="perfil")

    # Identidad
    alias = models.CharField(max_length=40)
    fecha_nacimiento = models.DateField(help_text="Solo para comprobar que es mayor de 18. Nunca se muestra.")
    historia = models.TextField("La mejor sesión que he jugado", blank=True, max_length=800)
    retrato = models.ImageField(
        "Retrato de tu personaje o criatura", upload_to="retratos/", blank=True,
        help_text="Opcional. Si no subes uno, se muestra tu inicial como capitular.",
    )
    # Solo para los perfiles de demo: retratos incluidos en el repositorio (static/demo/).
    # Así la demo funciona en Render sin depender de archivos subidos.
    retrato_demo = models.CharField(max_length=60, blank=True)
    contacto_discord = models.CharField(max_length=40, blank=True)
    contacto_correo = models.EmailField(blank=True)
    publicado = models.BooleanField(default=False)
    es_demo = models.BooleanField(default=False)
    creado = models.DateTimeField(auto_now_add=True)

    # Capa 1 · Logística
    rol = models.CharField(max_length=10, choices=Rol.choices, default=Rol.JUGADOR)
    modalidad = models.CharField(max_length=12, choices=Modalidad.choices, default=Modalidad.AMBAS)
    comunas = models.ManyToManyField(Comuna, blank=True)
    plataformas = models.ManyToManyField(Plataforma, blank=True)
    one_shot = models.BooleanField(default=True)
    campana_corta = models.BooleanField(default=True)
    campana_larga = models.BooleanField(default=False)
    idiomas = models.CharField(max_length=60, default="es", help_text="Códigos separados por coma, ej: es,en")
    anfitrion = models.BooleanField("Puede ser anfitrión", default=False)
    mesa_pagada = models.CharField(max_length=8, choices=MesaPagada.choices, default=MesaPagada.GRATIS)
    precio = models.PositiveIntegerField("Precio por sesión (CLP)", null=True, blank=True)

    # Capa 2 · Experiencia
    sistemas = models.ManyToManyField(Sistema, through="PerfilSistema", blank=True)
    experiencia = models.CharField(max_length=12, choices=Experiencia.choices, default=Experiencia.INTERMEDIO)
    novatos = models.CharField(max_length=10, choices=Novatos.choices, default=Novatos.IGUAL)

    # Capa 3 · Estilo: seis atributos con dados
    atr_combate = dado()
    atr_exploracion = dado()
    atr_interpretacion = dado()
    atr_misterio = dado()
    atr_estrategia = dado()
    atr_humor = dado()
    # Seis ejes y letalidad
    eje_enfoque = uno_a_cinco()
    eje_mundo = uno_a_cinco()
    eje_reglas = uno_a_cinco()
    eje_ritmo = uno_a_cinco()
    eje_profundidad = uno_a_cinco()
    eje_intensidad = uno_a_cinco()
    letalidad = uno_a_cinco()
    tonos = models.ManyToManyField(Tono, blank=True)
    arquetipos = models.ManyToManyField(Arquetipo, blank=True)
    ambientaciones = models.ManyToManyField(Ambientacion, blank=True)

    # Capa 4 · Seguridad (los temas van en LimiteTema)
    herramientas = models.ManyToManyField(HerramientaSeguridad, blank=True)
    conductas_no_tolera = models.ManyToManyField(Conducta, blank=True)

    # Capa 5 · Social y vibra
    ambiente = uno_a_cinco(help_text="1 = sesión enfocada · 5 = casual con chela")
    alcohol = models.CharField(max_length=6, choices=Gusto.choices, default=Gusto.IGUAL)
    comida = models.CharField(max_length=6, choices=Gusto.choices, default=Gusto.SI)
    tabaco = models.CharField(max_length=6, choices=Gusto.choices, default=Gusto.NO)
    busca_amistad = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "perfiles"
        constraints = [
            # Los seis dados deben ser distintos entre sí (o estar todos vacíos mientras completa).
            # Como solo pueden tomar valores del standard array, distintos = cada valor usado una vez.
            models.CheckConstraint(
                name="dados_sin_repetir",
                condition=Q(atr_combate__isnull=True)
                | (
                    ~Q(atr_combate=models.F("atr_exploracion"))
                    & ~Q(atr_combate=models.F("atr_interpretacion"))
                    & ~Q(atr_combate=models.F("atr_misterio"))
                    & ~Q(atr_combate=models.F("atr_estrategia"))
                    & ~Q(atr_combate=models.F("atr_humor"))
                    & ~Q(atr_exploracion=models.F("atr_interpretacion"))
                    & ~Q(atr_exploracion=models.F("atr_misterio"))
                    & ~Q(atr_exploracion=models.F("atr_estrategia"))
                    & ~Q(atr_exploracion=models.F("atr_humor"))
                    & ~Q(atr_interpretacion=models.F("atr_misterio"))
                    & ~Q(atr_interpretacion=models.F("atr_estrategia"))
                    & ~Q(atr_interpretacion=models.F("atr_humor"))
                    & ~Q(atr_misterio=models.F("atr_estrategia"))
                    & ~Q(atr_misterio=models.F("atr_humor"))
                    & ~Q(atr_estrategia=models.F("atr_humor"))
                ),
            ),
        ]

    def __str__(self):
        return self.alias

    # ---- utilidades
    @property
    def dados(self):
        return {campo: getattr(self, campo) for campo, _ in ATRIBUTOS}

    @property
    def dados_completos(self):
        return all(v is not None for v in self.dados.values())

    @property
    def compromisos(self):
        return {c for c, ok in (("one_shot", self.one_shot), ("corta", self.campana_corta), ("larga", self.campana_larga)) if ok}

    @property
    def lista_idiomas(self):
        return {i.strip() for i in self.idiomas.split(",") if i.strip()}

    def es_mayor_de_edad(self, hoy=None):
        hoy = hoy or date.today()
        f = self.fecha_nacimiento
        edad = hoy.year - f.year - ((hoy.month, hoy.day) < (f.month, f.day))
        return edad >= 18

    def clean(self):
        if self.fecha_nacimiento and not self.es_mayor_de_edad():
            raise ValidationError({"fecha_nacimiento": "Por ahora el sitio es solo para mayores de 18 años."})
        valores = [v for v in self.dados.values() if v is not None]
        if valores and sorted(valores, reverse=True) != list(STANDARD_ARRAY):
            raise ValidationError("Reparte los seis dados: 15, 14, 13, 12, 10 y 8, cada uno una vez.")
        if self.mesa_pagada in (self.MesaPagada.PAGA, self.MesaPagada.COBRA) and not self.precio:
            raise ValidationError({"precio": "Indica el precio por sesión."})


class PerfilSistema(models.Model):
    class Relacion(models.TextChoices):
        CONOCE = "conoce", "Lo conozco"
        QUIERE = "quiere", "Quiero probarlo"

    perfil = models.ForeignKey(Perfil, on_delete=models.CASCADE)
    sistema = models.ForeignKey(Sistema, on_delete=models.CASCADE)
    relacion = models.CharField(max_length=8, choices=Relacion.choices, default=Relacion.CONOCE)

    class Meta:
        unique_together = [("perfil", "sistema")]


class Disponibilidad(models.Model):
    """Un bloque de 2 horas en una fecha real ("mi mes")."""

    BLOQUES = [(h, f"{h:02d}–{(h + 2) % 24:02d}") for h in range(10, 25, 2)]  # 10–12 … 24–02

    perfil = models.ForeignKey(Perfil, on_delete=models.CASCADE, related_name="disponibilidad")
    fecha = models.DateField()
    bloque = models.PositiveSmallIntegerField(choices=BLOQUES, help_text="Hora de inicio del bloque")

    class Meta:
        unique_together = [("perfil", "fecha", "bloque")]
        ordering = ["fecha", "bloque"]
        verbose_name_plural = "disponibilidad"


class LimiteTema(models.Model):
    """Líneas y Velos: qué piensa una persona de cada tema. PRIVADO."""

    class Estado(models.TextChoices):
        BUSCO = "busco", "Lo busco"
        OK = "ok", "OK"
        VELO = "velo", "Velo"
        LINEA = "linea", "Línea"

    perfil = models.ForeignKey(Perfil, on_delete=models.CASCADE, related_name="limites")
    tema = models.ForeignKey(Tema, on_delete=models.CASCADE)
    estado = models.CharField(max_length=6, choices=Estado.choices, default=Estado.OK)

    class Meta:
        unique_together = [("perfil", "tema")]
        verbose_name = "límite de tema"
        verbose_name_plural = "límites de temas"


class Interes(models.Model):
    """'de' marcó "Me interesa" en el perfil de 'a'. Si existe también el inverso, hay match mutuo."""

    de = models.ForeignKey(Perfil, on_delete=models.CASCADE, related_name="intereses_dados")
    a = models.ForeignKey(Perfil, on_delete=models.CASCADE, related_name="intereses_recibidos")
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("de", "a")]
        verbose_name_plural = "intereses"
        constraints = [models.CheckConstraint(name="interes_no_a_si_mismo", condition=~Q(de=models.F("a")))]


class Bloqueo(models.Model):
    de = models.ForeignKey(Perfil, on_delete=models.CASCADE, related_name="bloqueos_dados")
    a = models.ForeignKey(Perfil, on_delete=models.CASCADE, related_name="bloqueos_recibidos")
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("de", "a")]


def hay_interes_mutuo(p1: Perfil, p2: Perfil) -> bool:
    return (
        Interes.objects.filter(de=p1, a=p2).exists()
        and Interes.objects.filter(de=p2, a=p1).exists()
    )
