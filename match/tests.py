"""Pruebas del motor de match. Se corren con: python manage.py test"""
from datetime import date

from django.test import SimpleTestCase

from .motor import Ficha, evaluar, ordenar, sesion_en_comun

VIERNES = date(2026, 10, 30)
VIERNES_2 = date(2026, 11, 13)


def ficha(id, **kw):
    base = dict(
        id=id, alias=f"P{id}", modalidad="online", plataformas={1}, compromisos={"larga"},
        bloques={(VIERNES, 20), (VIERNES, 22)},
        atributos={"atr_combate": 8, "atr_exploracion": 15, "atr_interpretacion": 14,
                   "atr_misterio": 13, "atr_estrategia": 10, "atr_humor": 12},
        ejes={"eje_enfoque": 2, "eje_mundo": 2, "eje_reglas": 4, "eje_ritmo": 4,
              "eje_profundidad": 4, "eje_intensidad": 4, "letalidad": 3},
        sistemas={"D&D 5e": "conoce"}, tonos={"Oscuro"},
    )
    base.update(kw)
    return Ficha(**base)


class FiltrosDuros(SimpleTestCase):
    def test_iguales_hacen_match_alto(self):
        r = evaluar(ficha(1), ficha(2))
        self.assertTrue(r.visible)
        self.assertGreaterEqual(r.puntaje, 85)

    def test_sin_bloques_seguidos_en_comun_no_hay_match(self):
        r = evaluar(ficha(1), ficha(2, bloques={(VIERNES, 20), (VIERNES_2, 22)}))
        self.assertFalse(r.visible)
        self.assertEqual(r.motivo_oculto, "horario")

    def test_sesion_en_comun_requiere_cuatro_horas(self):
        self.assertEqual(sesion_en_comun(ficha(1), ficha(2)), (VIERNES, 20))

    def test_presencial_necesita_comuna_en_comun(self):
        a = ficha(1, modalidad="presencial", comunas={10})
        self.assertFalse(evaluar(a, ficha(2, modalidad="presencial", comunas={11})).visible)
        self.assertTrue(evaluar(a, ficha(2, modalidad="presencial", comunas={10, 11})).visible)

    def test_ambas_calza_por_cualquiera(self):
        a = ficha(1, modalidad="ambas", comunas={10}, plataformas={1})
        self.assertTrue(evaluar(a, ficha(2, modalidad="presencial", comunas={10}, plataformas=set())).visible)

    def test_master_que_cobra_solo_con_quien_acepta_pagar_ese_precio(self):
        master = ficha(1, rol="master", mesa_pagada="cobra", precio=8000)
        self.assertFalse(evaluar(master, ficha(2, mesa_pagada="gratis")).visible)
        self.assertFalse(evaluar(master, ficha(2, mesa_pagada="paga", precio=5000)).visible)
        self.assertTrue(evaluar(master, ficha(2, mesa_pagada="paga", precio=10000)).visible)

    def test_bloqueo_en_cualquier_sentido(self):
        self.assertFalse(evaluar(ficha(1, bloqueados={2}), ficha(2)).visible)
        self.assertFalse(evaluar(ficha(1), ficha(2, bloqueados={1})).visible)

    def test_idioma_y_compromiso(self):
        self.assertEqual(evaluar(ficha(1), ficha(2, idiomas={"en"})).motivo_oculto, "idioma")
        self.assertEqual(evaluar(ficha(1), ficha(2, compromisos={"one_shot"})).motivo_oculto, "compromiso")


class Seguridad(SimpleTestCase):
    def test_linea_contra_lo_busco_oculta_el_match(self):
        r = evaluar(ficha(1, temas={"gore": "linea"}), ficha(2, temas={"gore": "busco"}))
        self.assertFalse(r.visible)
        self.assertEqual(r.motivo_oculto, "seguridad")

    def test_es_simetrico(self):
        self.assertFalse(evaluar(ficha(1, temas={"gore": "busco"}), ficha(2, temas={"gore": "linea"})).visible)

    def test_linea_contra_ok_si_se_muestra(self):
        self.assertTrue(evaluar(ficha(1, temas={"gore": "linea"}), ficha(2, temas={"gore": "ok"})).visible)

    def test_velo_contra_lo_busco_resta_puntos(self):
        base = evaluar(ficha(1), ficha(2)).puntaje
        con_velo = evaluar(ficha(1, temas={"gore": "velo"}), ficha(2, temas={"gore": "busco"})).puntaje
        self.assertEqual(base - con_velo, 5)


class Puntaje(SimpleTestCase):
    def test_estilos_opuestos_puntuan_menos(self):
        opuesto = ficha(
            2,
            atributos={"atr_combate": 15, "atr_exploracion": 8, "atr_interpretacion": 10,
                       "atr_misterio": 12, "atr_estrategia": 14, "atr_humor": 13},
            ejes={k: 6 - v for k, v in ficha(1).ejes.items()},
            sistemas={"Pathfinder 2e": "conoce"}, tonos={"Humor"},
        )
        self.assertLess(evaluar(ficha(1), opuesto).puntaje, evaluar(ficha(1), ficha(2)).puntaje - 30)

    def test_explicacion_menciona_coincidencias(self):
        r = evaluar(ficha(1), ficha(2))
        self.assertIn("los dos pusieron su 15 en exploración", r.coinciden)

    def test_un_master_ve_primero_jugadores(self):
        yo = ficha(1, rol="master")
        orden = ordenar(yo, [ficha(2, rol="master"), ficha(3, rol="jugador")])
        self.assertEqual(orden[0][0].id, 3)
