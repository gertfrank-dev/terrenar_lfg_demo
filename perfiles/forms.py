"""
Formularios del onboarding: un formulario por paso.
Cada uno edita solo una parte del Perfil, así se puede guardar de a poco.
"""
from datetime import date, timedelta

from django import forms

from .models import (
    ATRIBUTOS, EJES, STANDARD_ARRAY, Disponibilidad, LimiteTema, Perfil, PerfilSistema, Sistema, Tema,
)

IDIOMAS = [("es", "Español"), ("en", "Inglés"), ("pt", "Portugués")]


class PasoQuienEres(forms.ModelForm):
    idiomas_lista = forms.MultipleChoiceField(
        label="Idiomas en que puedes jugar", choices=IDIOMAS, widget=forms.CheckboxSelectMultiple, initial=["es"]
    )

    class Meta:
        model = Perfil
        fields = ["alias", "fecha_nacimiento", "rol", "experiencia", "novatos", "contacto_discord",
                  "contacto_correo", "retrato"]
        labels = {
            "alias": "¿Cómo te llamamos?",
            "fecha_nacimiento": "Fecha de nacimiento",
            "rol": "Buscas jugar como",
            "experiencia": "Tu experiencia",
            "novatos": "Con personas nuevas en el rol",
            "contacto_discord": "Usuario de Discord",
            "contacto_correo": "Correo de contacto",
        }
        help_texts = {
            "alias": "Tu nombre visible. Puede ser tu nombre y la inicial del apellido.",
            "fecha_nacimiento": "Solo para comprobar que eres mayor de 18. Nadie la ve y no se puede buscar por edad.",
            "contacto_discord": "Solo se muestra a quien tenga interés mutuo contigo.",
            "contacto_correo": "Opcional. También se muestra solo con interés mutuo.",
        }
        widgets = {
            "fecha_nacimiento": forms.DateInput(attrs={"type": "date", "autocomplete": "bday"}, format="%Y-%m-%d"),
            "rol": forms.RadioSelect, "experiencia": forms.RadioSelect, "novatos": forms.RadioSelect,
            "alias": forms.TextInput(attrs={"autocomplete": "nickname", "maxlength": 40}),
            "contacto_correo": forms.EmailInput(attrs={"autocomplete": "email"}),
        }

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        if self.instance.pk:
            self.fields["idiomas_lista"].initial = sorted(self.instance.lista_idiomas)

    def clean(self):
        datos = super().clean()
        if not datos.get("contacto_discord") and not datos.get("contacto_correo"):
            raise forms.ValidationError("Deja al menos una forma de contacto: Discord o correo.")
        return datos

    def save(self, commit=True):
        self.instance.idiomas = ",".join(self.cleaned_data["idiomas_lista"])
        return super().save(commit)


class PasoLogistica(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ["modalidad", "comunas", "plataformas", "one_shot", "campana_corta", "campana_larga",
                  "anfitrion", "mesa_pagada", "precio"]
        labels = {
            "modalidad": "Quieres jugar",
            "comunas": "Comunas donde puedes jugar presencial",
            "plataformas": "Plataformas que usas online",
            "one_shot": "One-shot (una sesión)",
            "campana_corta": "Campaña corta (2 a 6 sesiones)",
            "campana_larga": "Campaña larga",
            "anfitrion": "Puedo recibir la mesa en mi casa",
            "mesa_pagada": "Mesas pagadas",
        }
        help_texts = {"precio": "Lo que cobras, o lo máximo que pagarías, por sesión."}
        widgets = {
            "modalidad": forms.RadioSelect, "mesa_pagada": forms.RadioSelect,
            "comunas": forms.CheckboxSelectMultiple, "plataformas": forms.CheckboxSelectMultiple,
            "precio": forms.NumberInput(attrs={"inputmode": "numeric", "min": 0, "step": 500}),
        }

    bloques = forms.MultipleChoiceField(required=False, widget=forms.CheckboxSelectMultiple)

    def __init__(self, *a, hoy=None, **kw):
        super().__init__(*a, **kw)
        self.hoy = hoy or date.today()
        self.dias = [self.hoy + timedelta(days=i) for i in range(28)]
        self.fields["bloques"].choices = [
            (f"{d.isoformat()}|{h}", f"{d:%d/%m} {h}") for d in self.dias for h, _ in Disponibilidad.BLOQUES
        ]
        if self.instance.pk:
            self.fields["bloques"].initial = [
                f"{x.fecha.isoformat()}|{x.bloque}" for x in self.instance.disponibilidad.filter(fecha__gte=self.hoy)
            ]

    def clean(self):
        d = super().clean()
        if not (d.get("one_shot") or d.get("campana_corta") or d.get("campana_larga")):
            raise forms.ValidationError("Marca al menos un tipo de partida.")
        modalidad = d.get("modalidad")
        if modalidad in ("presencial", "ambas") and not d.get("comunas"):
            self.add_error("comunas", "Elige al menos una comuna para jugar presencial.")
        if modalidad in ("online", "ambas") and not d.get("plataformas"):
            self.add_error("plataformas", "Elige al menos una plataforma para jugar online.")
        if d.get("mesa_pagada") in ("paga", "cobra") and not d.get("precio"):
            self.add_error("precio", "Indica el precio por sesión.")
        if len(d.get("bloques") or []) < 2:
            self.add_error("bloques", "Marca al menos dos bloques seguidos (una sesión de 4 horas).")
        return d

    def save(self, commit=True):
        perfil = super().save(commit)
        perfil.disponibilidad.filter(fecha__gte=self.hoy).delete()
        nuevos = []
        for v in self.cleaned_data["bloques"]:
            f, h = v.split("|")
            nuevos.append(Disponibilidad(perfil=perfil, fecha=date.fromisoformat(f), bloque=int(h)))
        Disponibilidad.objects.bulk_create(nuevos)
        return perfil

    def semanas(self):
        """Para la plantilla: semanas → días → bloques con su casilla."""
        marcados = set(self["bloques"].value() or [])
        sem = []
        for s in range(4):
            dias = []
            for d in self.dias[s * 7:(s + 1) * 7]:
                dias.append({
                    "fecha": d,
                    "bloques": [{"valor": f"{d.isoformat()}|{h}", "hora": h, "on": f"{d.isoformat()}|{h}" in marcados}
                                for h, _ in Disponibilidad.BLOQUES],
                })
            sem.append(dias)
        return sem


class PasoEstilo(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = [c for c, _ in ATRIBUTOS] + [c for c, *_ in EJES] + ["tonos", "arquetipos", "ambientaciones"]
        widgets = {"tonos": forms.CheckboxSelectMultiple, "arquetipos": forms.CheckboxSelectMultiple,
                   "ambientaciones": forms.CheckboxSelectMultiple}
        labels = {"tonos": "Tonos que disfrutas", "arquetipos": "Qué tipo de jugador eres",
                  "ambientaciones": "Mundos que te gustan"}

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        for campo, nombre in ATRIBUTOS:
            f = self.fields[campo]
            f.label, f.required = nombre, True
            f.choices = [("", "—")] + [(v, v) for v in STANDARD_ARRAY]
        for campo, nombre, bajo, alto in EJES:
            f = self.fields[campo]
            f.label = nombre
            f.widget = forms.NumberInput(attrs={"type": "range", "min": 1, "max": 5, "step": 1,
                                                "data-bajo": bajo, "data-alto": alto})
        # Sistemas: un selector por sistema (no, lo conozco, quiero probarlo)
        actuales = dict(PerfilSistema.objects.filter(perfil=self.instance).values_list("sistema_id", "relacion")) if self.instance.pk else {}
        self.sistemas = list(Sistema.objects.all())
        for s in self.sistemas:
            self.fields[f"sis_{s.pk}"] = forms.ChoiceField(
                label=s.nombre, required=False, initial=actuales.get(s.pk, ""),
                choices=[("", "No"), ("conoce", "Lo conozco"), ("quiere", "Quiero probarlo")],
                widget=forms.RadioSelect,
            )

    def campos_atributos(self):
        return [self[c] for c, _ in ATRIBUTOS]

    def campos_ejes(self):
        return [(self[c], bajo, alto) for c, _, bajo, alto in EJES]

    def campos_sistemas(self):
        return [self[f"sis_{s.pk}"] for s in self.sistemas]

    def clean(self):
        d = super().clean()
        valores = [d.get(c) for c, _ in ATRIBUTOS]
        if None not in valores and sorted(valores, reverse=True) != list(STANDARD_ARRAY):
            raise forms.ValidationError("Cada dado se usa una sola vez: reparte 15, 14, 13, 12, 10 y 8.")
        if not any(d.get(f"sis_{s.pk}") for s in self.sistemas):
            raise forms.ValidationError("Marca al menos un sistema que conozcas o quieras probar.")
        return d

    def save(self, commit=True):
        perfil = super().save(commit)
        PerfilSistema.objects.filter(perfil=perfil).delete()
        PerfilSistema.objects.bulk_create([
            PerfilSistema(perfil=perfil, sistema=s, relacion=self.cleaned_data[f"sis_{s.pk}"])
            for s in self.sistemas if self.cleaned_data.get(f"sis_{s.pk}")
        ])
        return perfil


class PasoSeguridad(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ["herramientas", "conductas_no_tolera"]
        widgets = {"herramientas": forms.CheckboxSelectMultiple, "conductas_no_tolera": forms.CheckboxSelectMultiple}
        labels = {"herramientas": "Herramientas de seguridad que esperas en la mesa",
                  "conductas_no_tolera": "Conductas que no toleras"}

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        actuales = dict(LimiteTema.objects.filter(perfil=self.instance).values_list("tema_id", "estado")) if self.instance.pk else {}
        self.temas = list(Tema.objects.all())
        for t in self.temas:
            self.fields[f"tema_{t.pk}"] = forms.ChoiceField(
                label=t.nombre, choices=LimiteTema.Estado.choices, widget=forms.RadioSelect,
                initial=actuales.get(t.pk, t.estado_por_defecto),
            )

    def grupos_temas(self):
        grupos = {}
        for t in self.temas:
            grupos.setdefault(t.categoria, []).append(self[f"tema_{t.pk}"])
        return grupos.items()

    def save(self, commit=True):
        perfil = super().save(commit)
        LimiteTema.objects.filter(perfil=perfil).delete()
        LimiteTema.objects.bulk_create([
            LimiteTema(perfil=perfil, tema=t, estado=self.cleaned_data[f"tema_{t.pk}"]) for t in self.temas
        ])
        return perfil


class PasoVibra(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ["ambiente", "alcohol", "comida", "tabaco", "busca_amistad", "historia"]
        labels = {"ambiente": "Ambiente de la mesa", "alcohol": "Alcohol en la mesa", "comida": "Comida en la mesa",
                  "tabaco": "Tabaco", "busca_amistad": "También me gustaría hacer amigos",
                  "historia": "La mejor sesión que has jugado"}
        help_texts = {"historia": "Opcional, pero es lo que más ayuda a que alguien quiera jugar contigo."}
        widgets = {
            "ambiente": forms.NumberInput(attrs={"type": "range", "min": 1, "max": 5, "step": 1,
                                                 "data-bajo": "Sesión enfocada", "data-alto": "Casual con chela"}),
            "alcohol": forms.RadioSelect, "comida": forms.RadioSelect, "tabaco": forms.RadioSelect,
            "historia": forms.Textarea(attrs={"rows": 4, "maxlength": 800}),
        }


PASOS = [
    ("quien", "Quién eres", PasoQuienEres),
    ("logistica", "Logística y mi mes", PasoLogistica),
    ("estilo", "Tu estilo", PasoEstilo),
    ("seguridad", "Líneas y velos", PasoSeguridad),
    ("vibra", "Vibra y publicar", PasoVibra),
]
