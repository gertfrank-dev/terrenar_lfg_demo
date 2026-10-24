"""Pruebas de privacidad y reglas de los perfiles."""
from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import Interes, LimiteTema, Perfil, Tema

DADOS = dict(atr_combate=15, atr_exploracion=14, atr_interpretacion=13, atr_misterio=12, atr_estrategia=10, atr_humor=8)


def crear(nombre, **kw):
    u = get_user_model().objects.create_user(username=nombre, email=f"{nombre}@x.cl", password="clave-larga-123")
    return Perfil.objects.create(usuario=u, alias=nombre, fecha_nacimiento=date(1990, 1, 1), publicado=True,
                                 contacto_discord=f"{nombre}#1", **DADOS, **kw)


class Privacidad(TestCase):
    def setUp(self):
        self.ana = crear("ana")
        self.beto = crear("beto")
        tema = Tema.objects.create(nombre="Tortura gráfica", categoria="Violencia")
        LimiteTema.objects.create(perfil=self.beto, tema=tema, estado="linea")
        self.client.force_login(self.ana.usuario)

    def test_sin_interes_mutuo_no_se_ven_lineas_ni_contacto(self):
        html = self.client.get(f"/p/{self.beto.pk}/").content.decode()
        self.assertNotIn("Tortura gráfica", html)
        self.assertNotIn("beto#1", html)

    def test_interes_de_un_solo_lado_no_basta(self):
        Interes.objects.create(de=self.ana, a=self.beto)
        html = self.client.get(f"/p/{self.beto.pk}/").content.decode()
        self.assertNotIn("Tortura gráfica", html)

    def test_con_interes_mutuo_se_ven_automaticamente(self):
        Interes.objects.create(de=self.ana, a=self.beto)
        Interes.objects.create(de=self.beto, a=self.ana)
        html = self.client.get(f"/p/{self.beto.pk}/").content.decode()
        self.assertIn("Tortura gráfica", html)
        self.assertIn("beto#1", html)

    def test_la_edad_nunca_aparece(self):
        html = self.client.get(f"/p/{self.beto.pk}/").content.decode()
        self.assertNotIn("1990", html)


class Reglas(TestCase):
    def test_menor_de_18_no_pasa_la_validacion(self):
        p = crear("carla")
        p.fecha_nacimiento = date.today().replace(year=date.today().year - 17)
        with self.assertRaises(ValidationError):
            p.full_clean()

    def test_la_base_de_datos_rechaza_dados_repetidos(self):
        p = crear("dani")
        p.atr_humor = 15  # el 15 ya está en combate
        with self.assertRaises(IntegrityError), transaction.atomic():
            p.save()


class Onboarding(TestCase):
    """Recorre los 5 pasos de la ficha como lo haría una persona nueva."""

    def setUp(self):
        from perfiles.models import Plataforma, Sistema
        self.plataforma = Plataforma.objects.create(nombre="Discord")
        self.sistema = Sistema.objects.create(nombre="Sistema de prueba")
        self.tema = Tema.objects.create(nombre="Arañas", categoria="Fobias")
        u = get_user_model().objects.create_user(username="nueva", email="nueva@x.cl", password="clave-larga-123")
        self.client.force_login(u)

    def quien(self, **extra):
        datos = dict(alias="Nueva", fecha_nacimiento="1995-05-05", rol="jugador", experiencia="nuevo",
                     novatos="igual", contacto_discord="nueva#1", idiomas_lista=["es"])
        datos.update(extra)
        return self.client.post("/ficha/quien/", datos)

    def test_sin_ficha_mi_perfil_lleva_al_primer_paso(self):
        self.assertRedirects(self.client.get("/mi-perfil/"), "/ficha/quien/")

    def test_menor_de_18_no_avanza(self):
        r = self.quien(fecha_nacimiento=f"{date.today().year - 16}-01-01")
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Perfil.objects.exists())

    def test_dados_repetidos_no_avanzan(self):
        self.quien()
        datos = {c: 15 for c in DADOS} | {f"sis_{self.sistema.pk}": "conoce"}
        datos |= dict(eje_enfoque=3, eje_mundo=3, eje_reglas=3, eje_ritmo=3, eje_profundidad=3,
                      eje_intensidad=3, letalidad=3)
        r = self.client.post("/ficha/estilo/", datos)
        self.assertContains(r, "Cada dado se usa una sola vez")

    def test_recorrido_completo_publica_la_ficha(self):
        self.assertRedirects(self.quien(), "/ficha/logistica/")
        hoy = date.today().isoformat()
        r = self.client.post("/ficha/logistica/", dict(
            modalidad="online", plataformas=[self.plataforma.pk], one_shot="on", mesa_pagada="gratis",
            bloques=[f"{hoy}|18", f"{hoy}|20"]))
        self.assertRedirects(r, "/ficha/estilo/")
        datos = dict(DADOS) | {f"sis_{self.sistema.pk}": "quiere"}
        datos |= dict(eje_enfoque=2, eje_mundo=3, eje_reglas=4, eje_ritmo=3, eje_profundidad=5,
                      eje_intensidad=3, letalidad=2)
        self.assertRedirects(self.client.post("/ficha/estilo/", datos), "/ficha/seguridad/")
        r = self.client.post("/ficha/seguridad/", {f"tema_{self.tema.pk}": "linea"})
        self.assertRedirects(r, "/ficha/vibra/")
        r = self.client.post("/ficha/vibra/", dict(ambiente=3, alcohol="igual", comida="si", tabaco="no"))
        self.assertRedirects(r, "/explorar/")

        p = Perfil.objects.get(alias="Nueva")
        self.assertTrue(p.publicado)
        self.assertEqual(p.disponibilidad.count(), 2)
        self.assertEqual(p.limites.get().estado, "linea")
        self.assertEqual(p.perfilsistema_set.get().relacion, "quiere")
