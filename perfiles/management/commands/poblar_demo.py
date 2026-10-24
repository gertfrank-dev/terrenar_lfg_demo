"""
Carga los catálogos y ~25 perfiles ficticios para la demo.

Uso:  python manage.py poblar_demo
Es seguro correrlo varias veces: borra y recrea solo los perfiles de demo.
"""
import random
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from perfiles import models as m

CATALOGOS = {
    m.Comuna: ["Santiago Centro", "Providencia", "Ñuñoa", "Las Condes", "La Florida", "Maipú", "Puente Alto",
               "San Miguel", "Macul", "La Reina", "Valparaíso", "Viña del Mar", "Concepción"],
    m.Plataforma: ["Roll20", "Foundry VTT", "Discord", "Owlbear Rodeo"],
    m.Sistema: ["D&D 5e", "D&D 2024", "Pathfinder 2e", "Call of Cthulhu", "Vampiro: La Mascarada", "Powered by the Apocalypse",
                "Blades in the Dark", "OSR", "Savage Worlds", "Mothership"],
    m.Tono: ["Épico", "Oscuro", "Humor", "Terror"],
    m.Arquetipo: ["Actor", "Táctico", "Explorador", "Coleccionista de botín", "El que hace reír", "Optimizador"],
    m.Ambientacion: ["Fantasía clásica", "Ciencia ficción", "Steampunk", "Horror cósmico", "Western", "Postapocalíptico"],
    m.HerramientaSeguridad: ["X-Card", "Sesión Cero", "Pausas", "Líneas y Velos escritos"],
    m.Conducta: ["Celulares en la mesa", "Metagaming", "\"Es lo que haría mi personaje\"", "Llegar tarde sin avisar",
                 "Interrumpir a otros"],
}
TEMAS = [
    ("Arañas e insectos", "Fobias", "ok"), ("Espacios cerrados", "Fobias", "ok"), ("Gore", "Violencia", "ok"),
    ("Tortura gráfica", "Violencia", "ok"), ("Daño a niños", "Violencia", "linea"), ("Daño a animales", "Violencia", "ok"),
    ("Suicidio", "Salud mental", "ok"), ("Autolesiones", "Salud mental", "ok"), ("Adicciones", "Salud mental", "ok"),
    ("Racismo", "Discriminación", "ok"), ("Esclavitud", "Discriminación", "ok"), ("Religión real", "Sociedad", "ok"),
    ("Romance entre personajes", "Relaciones", "ok"), ("Contenido sexual explícito", "Relaciones", "ok"),
    ("Violencia sexual", "Relaciones", "linea"), ("PvP entre jugadores", "Mesa", "ok"),
]

ALIAS = ["Valentina R.", "Tomás F.", "Camila S.", "Matías H.", "Javiera P.", "Benjamín C.", "Antonia M.", "Diego L.",
         "Catalina V.", "Sebastián O.", "Fernanda A.", "Nicolás B.", "Isidora G.", "Vicente T.", "Martina Q.",
         "Joaquín E.", "Florencia N.", "Cristóbal D.", "Josefa I.", "Agustín K.", "Constanza Y.", "Ignacio U.",
         "Trinidad Z.", "Maximiliano W.", "Amanda J."]
HISTORIAS = [
    "Un one-shot de Cthulhu donde el investigador más escéptico terminó leyendo el libro prohibido en voz alta.",
    "Defendimos un puente contra un ejército entero solo con barriles de aceite y mucha suerte en los dados.",
    "Mi pícara convenció al dragón de que ella era su madre perdida. Nadie lo vio venir, ni el máster.",
    "Tres sesiones negociando con un gremio de ladrones y no tiramos un solo dado de ataque.",
    "La campaña terminó con el villano llorando y pidiéndonos perdón. Todavía lo comentamos.",
    "Una partida de Blades donde el golpe salió perfecto y después todo se fue al carajo. La mejor.",
]


# Retratos originales (generados con IA para la demo) y a quién pertenecen.
RETRATOS = {
    "Valentina R.": "mago-reglamento.jpg",
    "Matías H.": "enano-taburete.jpg",
    "Trinidad Z.": "hechicera-en-llamas.jpg",
    "Cristóbal D.": "barbaro-tejedor.jpg",
    "Constanza Y.": "sacerdotisa-curita.jpg",
    "Catalina V.": "mediana-pastel.jpg",
    "Maximiliano W.": "gnomo-bardo.jpg",
    "Tomás F.": "montaraz-y-oso.jpg",
}


class Command(BaseCommand):
    help = "Carga catálogos y perfiles de demo"

    @transaction.atomic
    def handle(self, *args, **opts):
        rnd = random.Random(42)
        for modelo, nombres in CATALOGOS.items():
            for i, n in enumerate(nombres):
                modelo.objects.get_or_create(nombre=n, defaults={"orden": i})
        for i, (n, cat, defecto) in enumerate(TEMAS):
            m.Tema.objects.update_or_create(nombre=n, defaults={"categoria": cat, "estado_por_defecto": defecto, "orden": i})

        User = get_user_model()
        User.objects.filter(email__contains="@demo.").delete()

        comunas = list(m.Comuna.objects.all())
        plataformas = list(m.Plataforma.objects.all())
        sistemas = list(m.Sistema.objects.all())
        tonos = list(m.Tono.objects.all())
        arquetipos = list(m.Arquetipo.objects.all())
        ambientaciones = list(m.Ambientacion.objects.all())
        herramientas = list(m.HerramientaSeguridad.objects.all())
        conductas = list(m.Conducta.objects.all())
        temas = list(m.Tema.objects.all())
        hoy = date.today()

        for n, alias in enumerate(ALIAS):
            user = User.objects.create_user(
                username=f"demo{n}", email=f"demo{n}@demo.terrenar", password=None
            )
            rol = rnd.choices(["jugador", "master", "ambos"], weights=[6, 3, 2])[0]
            modalidad = rnd.choices(["presencial", "online", "ambas"], weights=[2, 3, 5])[0]
            mesa = "gratis"
            precio = None
            if rol == "master" and rnd.random() < 0.3:
                mesa, precio = "cobra", rnd.choice([5000, 8000, 10000])
            elif rol == "jugador" and rnd.random() < 0.3:
                mesa, precio = "paga", rnd.choice([6000, 10000, 12000])
            dados = list(m.STANDARD_ARRAY)
            rnd.shuffle(dados)
            p = m.Perfil.objects.create(
                usuario=user, alias=alias, es_demo=True, publicado=True,
                fecha_nacimiento=date(rnd.randint(1980, 2003), rnd.randint(1, 12), rnd.randint(1, 28)),
                historia=rnd.choice(HISTORIAS),
                contacto_discord=f"{alias.split()[0].lower()}_rol",
                rol=rol, modalidad=modalidad, mesa_pagada=mesa, precio=precio,
                one_shot=rnd.random() < 0.6, campana_corta=rnd.random() < 0.75, campana_larga=rnd.random() < 0.7,
                idiomas=rnd.choice(["es", "es", "es", "es,en"]), anfitrion=rnd.random() < 0.3,
                experiencia=rnd.choice(["nuevo", "intermedio", "intermedio", "veterano"]),
                novatos=rnd.choice(["ensena", "igual", "expertos"]),
                **{campo: v for (campo, _), v in zip(m.ATRIBUTOS, dados)},
                **{campo: rnd.randint(1, 5) for campo, *_ in m.EJES},
                ambiente=rnd.randint(1, 5), alcohol=rnd.choice(["si", "igual", "no"]),
                comida=rnd.choice(["si", "igual"]), tabaco=rnd.choice(["igual", "no", "no"]),
                busca_amistad=rnd.random() < 0.5,
            )
            if not p.compromisos:
                p.campana_corta = True
                p.save(update_fields=["campana_corta"])
            p.comunas.set(rnd.sample(comunas[:5], rnd.randint(1, 3)))
            plats = set(rnd.sample(plataformas, rnd.randint(1, 2)))
            if rnd.random() < 0.8:
                plats.add(plataformas[2])  # Discord, la más común
            p.plataformas.set(plats)
            for s in rnd.sample(sistemas, rnd.randint(1, 4)):
                m.PerfilSistema.objects.create(perfil=p, sistema=s, relacion=rnd.choice(["conoce", "conoce", "quiere"]))
            p.tonos.set(rnd.sample(tonos, rnd.randint(1, 2)))
            p.arquetipos.set(rnd.sample(arquetipos, rnd.randint(1, 2)))
            p.ambientaciones.set(rnd.sample(ambientaciones, rnd.randint(1, 3)))
            p.herramientas.set(rnd.sample(herramientas, rnd.randint(1, 3)))
            p.conductas_no_tolera.set(rnd.sample(conductas, rnd.randint(0, 2)))

            for t in temas:
                estado = t.estado_por_defecto
                r = rnd.random()
                if estado != "linea":
                    estado = "busco" if r < 0.12 else "velo" if r < 0.25 else "linea" if r < 0.32 else "ok"
                m.LimiteTema.objects.create(perfil=p, tema=t, estado=estado)

            # "Mi mes": uno o dos días fijos, semanal o semana por medio, 2–3 bloques seguidos
            dias = {rnd.choice([4, 5, 4, 5, 2, 6])}
            if rnd.random() < 0.5:
                dias.add(rnd.choice([4, 5, 6]))
            inicio = rnd.choice([18, 20, 20]) if rnd.random() < 0.8 else rnd.choice([14, 16])
            n_bloques = rnd.choice([2, 2, 3])
            cada = rnd.choice([1, 1, 1, 2])
            bloques = []
            for d in range(28):
                f = hoy + timedelta(days=d)
                if f.weekday() in dias and (d // 7) % cada == 0:
                    for k in range(n_bloques):
                        h = inicio + 2 * k
                        if h <= 24:
                            bloques.append(m.Disponibilidad(perfil=p, fecha=f, bloque=h))
            m.Disponibilidad.objects.bulk_create(bloques)

        # Un caso garantizado de "línea oculta el match": Valentina tiene Gore como línea; Diego lo busca.
        val = m.Perfil.objects.get(alias="Valentina R.")
        die = m.Perfil.objects.get(alias="Diego L.")
        # Valentina es la cuenta de prueba de la demo: máster online, viernes y sábado de noche.
        for x in (val, die):
            x.modalidad, x.mesa_pagada, x.precio, x.idiomas = "ambas", "gratis", None, "es"
            x.one_shot = x.campana_corta = x.campana_larga = True
            x.save()
            x.plataformas.add(m.Plataforma.objects.get(nombre="Discord"))
        val.rol = "master"
        val.save(update_fields=["rol"])
        hoy_ = date.today()
        for x in (val, die):
            for d in range(28):
                f = hoy_ + timedelta(days=d)
                if f.weekday() in (4, 5):
                    for h in (20, 22):
                        m.Disponibilidad.objects.get_or_create(perfil=x, fecha=f, bloque=h)
        gore = m.Tema.objects.get(nombre="Gore")
        m.LimiteTema.objects.filter(perfil=val, tema=gore).update(estado="linea")
        m.LimiteTema.objects.filter(perfil=die, tema=gore).update(estado="busco")

        from django.conf import settings

        carpeta = settings.BASE_DIR / "static" / "demo"
        for alias, archivo in RETRATOS.items():
            if (carpeta / archivo).exists():
                m.Perfil.objects.filter(alias=alias, es_demo=True).update(retrato_demo=archivo)

        self.stdout.write(self.style.SUCCESS(f"Listo: {m.Perfil.objects.filter(es_demo=True).count()} perfiles de demo."))
