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
