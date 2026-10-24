"""
Motor de match.

Recibe dos "fichas" (resúmenes de perfil) y responde:
  1. si pasan los filtros duros,
  2. si la seguridad bloquea el match,
  3. el puntaje de 0 a 100 y la explicación.

Trabaja con fichas simples (no con la base de datos) para poder probarlo
rápido y sin depender de Django. `ficha_desde_perfil` las arma desde un Perfil.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

PESOS = {"atributos": 35, "ejes": 25, "sistemas": 20, "gustos": 10, "vibra": 10}
CASTIGO_VELO = 5
DIAS_HORIZONTE = 28  # "mi mes": las próximas 4 semanas

NOMBRES_ATR = {
    "atr_combate": "combate", "atr_exploracion": "exploración", "atr_interpretacion": "interpretación",
    "atr_misterio": "misterio", "atr_estrategia": "estrategia", "atr_humor": "humor",
}
NOMBRES_EJE = {
    "eje_enfoque": ("enfoque", "narrativo", "táctico"),
    "eje_mundo": ("mundo", "sandbox", "lineal"),
    "eje_reglas": ("reglas", "RAW estricto", "regla de lo genial"),
    "eje_ritmo": ("ritmo", "ágil", "pausado"),
    "eje_profundidad": ("profundidad", "ligera", "inmersiva"),
    "eje_intensidad": ("intensidad", "liviana", "intensa"),
    "letalidad": ("letalidad", "baja", "alta"),
}


@dataclass
class Ficha:
    id: int
    alias: str = ""
    rol: str = "jugador"
    modalidad: str = "ambas"  # presencial | online | ambas
    comunas: set = field(default_factory=set)
    plataformas: set = field(default_factory=set)
    compromisos: set = field(default_factory=lambda: {"one_shot"})
    idiomas: set = field(default_factory=lambda: {"es"})
    mesa_pagada: str = "gratis"  # gratis | paga | cobra
    precio: int | None = None
    bloques: set = field(default_factory=set)  # {(fecha, hora_inicio)}
    atributos: dict = field(default_factory=dict)  # {campo: valor del standard array}
    ejes: dict = field(default_factory=dict)  # {campo: 1..5}
    sistemas: dict = field(default_factory=dict)  # {nombre: "conoce" | "quiere"}
    tonos: set = field(default_factory=set)
    arquetipos: set = field(default_factory=set)
    ambientaciones: set = field(default_factory=set)
    temas: dict = field(default_factory=dict)  # {tema: "busco" | "ok" | "velo" | "linea"}  PRIVADO
    vibra: dict = field(default_factory=dict)  # ambiente 1..5, alcohol/comida/tabaco si|igual|no, amistad bool
    bloqueados: set = field(default_factory=set)  # ids que esta persona bloqueó


@dataclass
class Resultado:
    visible: bool
    puntaje: int = 0
    coinciden: list = field(default_factory=list)
    difieren: list = field(default_factory=list)
    motivo_oculto: str = ""  # solo para pruebas y depuración; NUNCA se muestra al usuario
    sesion_en_comun: tuple | None = None


# ------------------------------------------------------------ paso 1: filtros duros
def _modalidad_ok(a: Ficha, b: Ficha) -> bool:
    presencial = (a.modalidad in ("presencial", "ambas") and b.modalidad in ("presencial", "ambas")
                  and bool(a.comunas & b.comunas))
    online = (a.modalidad in ("online", "ambas") and b.modalidad in ("online", "ambas")
              and bool(a.plataformas & b.plataformas))
    return presencial or online


def _mesa_pagada_ok(a: Ficha, b: Ficha) -> bool:
    for cobra, otro in ((a, b), (b, a)):
        if cobra.mesa_pagada == "cobra":
            if otro.mesa_pagada == "cobra":
                continue  # dos másters que cobran pueden jugar juntos como pares
            if otro.mesa_pagada != "paga":
                return False
            if (otro.precio or 0) < (cobra.precio or 0):
                return False
    return True


def sesion_en_comun(a: Ficha, b: Ficha):
    """Primera sesión posible: dos bloques seguidos (4 horas) el mismo día que ambos tienen libres."""
    comunes = a.bloques & b.bloques
    for fecha, hora in sorted(comunes):
        if (fecha, hora + 2) in comunes:
            return (fecha, hora)
    return None


def filtros_duros(a: Ficha, b: Ficha) -> str:
    """Devuelve '' si pasan, o el nombre del filtro que falló."""
    if b.id in a.bloqueados or a.id in b.bloqueados:
        return "bloqueo"
    if not (a.idiomas & b.idiomas):
        return "idioma"
    if not (a.compromisos & b.compromisos):
        return "compromiso"
    if not _modalidad_ok(a, b):
        return "modalidad"
    if not _mesa_pagada_ok(a, b):
        return "mesa_pagada"
    if sesion_en_comun(a, b) is None:
        return "horario"
    return ""


# ------------------------------------------------------------ paso 2: seguridad
def conflicto_de_lineas(a: Ficha, b: Ficha) -> bool:
    """Línea de uno contra 'lo busco' del otro: el match se oculta."""
    for x, y in ((a, b), (b, a)):
        for tema, estado in x.temas.items():
            if estado == "linea" and y.temas.get(tema) == "busco":
                return True
    return False


def velos_en_conflicto(a: Ficha, b: Ficha) -> int:
    n = 0
    for x, y in ((a, b), (b, a)):
        for tema, estado in x.temas.items():
            if estado == "velo" and y.temas.get(tema) == "busco":
                n += 1
    return n


# ------------------------------------------------------------ paso 3: puntaje
def _jaccard(x: set, y: set) -> float:
    if not x and not y:
        return 0.5  # sin datos: neutro
    return len(x & y) / len(x | y)


def _sim_atributos(a: Ficha, b: Ficha) -> float:
    campos = [c for c in NOMBRES_ATR if a.atributos.get(c) and b.atributos.get(c)]
    if not campos:
        return 0.5
    return sum(1 - abs(a.atributos[c] - b.atributos[c]) / 7 for c in campos) / len(campos)


def _sim_ejes(a: Ficha, b: Ficha) -> float:
    campos = [c for c in NOMBRES_EJE if c in a.ejes and c in b.ejes]
    if not campos:
        return 0.5
    return sum(1 - abs(a.ejes[c] - b.ejes[c]) / 4 for c in campos) / len(campos)


def _sim_sistemas(a: Ficha, b: Ficha) -> float:
    return _jaccard(set(a.sistemas), set(b.sistemas))


def _sim_gustos(a: Ficha, b: Ficha) -> float:
    return (_jaccard(a.tonos, b.tonos) + _jaccard(a.arquetipos, b.arquetipos) + _jaccard(a.ambientaciones, b.ambientaciones)) / 3


def _sim_vibra(a: Ficha, b: Ficha) -> float:
    partes = []
    if "ambiente" in a.vibra and "ambiente" in b.vibra:
        partes.append(1 - abs(a.vibra["ambiente"] - b.vibra["ambiente"]) / 4)
    for k in ("alcohol", "comida", "tabaco"):
        va, vb = a.vibra.get(k), b.vibra.get(k)
        if va and vb:
            partes.append(0.0 if {va, vb} == {"si", "no"} else 1.0)
    if "amistad" in a.vibra and "amistad" in b.vibra:
        partes.append(1.0 if a.vibra["amistad"] == b.vibra["amistad"] else 0.6)
    return sum(partes) / len(partes) if partes else 0.5


def explicar(a: Ficha, b: Ficha):
    coinciden, difieren = [], []
    # Atributos: misma prioridad máxima o mínima
    top_a = max(a.atributos, key=a.atributos.get) if a.atributos else None
    top_b = max(b.atributos, key=b.atributos.get) if b.atributos else None
    if top_a and top_a == top_b:
        coinciden.append(f"los dos pusieron su 15 en {NOMBRES_ATR[top_a]}")
    for c, nombre in NOMBRES_ATR.items():
        va, vb = a.atributos.get(c), b.atributos.get(c)
        if va and vb and abs(va - vb) >= 5:
            difieren.append(f"{nombre} (tú {va}, {b.alias or 'la otra persona'} {vb})")
    for c, (nombre, bajo, alto) in NOMBRES_EJE.items():
        va, vb = a.ejes.get(c), b.ejes.get(c)
        if va is None or vb is None:
            continue
        if va == vb and va != 3:
            coinciden.append(f"{nombre} {bajo if va < 3 else alto}")
        elif abs(va - vb) >= 3:
            difieren.append(f"{nombre} (tú {va}, {b.alias or 'la otra persona'} {vb})")
    comunes = sorted(set(a.sistemas) & set(b.sistemas))
    if comunes:
        coinciden.append(", ".join(comunes[:2]))
    tonos = sorted(a.tonos & b.tonos)
    if tonos:
        coinciden.append(f"tono {tonos[0].lower()}")
    return coinciden[:4], difieren[:3]


def evaluar(a: Ficha, b: Ficha) -> Resultado:
    """Evalúa a 'b' desde el punto de vista de 'a'."""
    if a.id == b.id:
        return Resultado(visible=False, motivo_oculto="misma_persona")
    fallo = filtros_duros(a, b)
    if fallo:
        return Resultado(visible=False, motivo_oculto=fallo)
    if conflicto_de_lineas(a, b):
        return Resultado(visible=False, motivo_oculto="seguridad")

    total = (
        PESOS["atributos"] * _sim_atributos(a, b)
        + PESOS["ejes"] * _sim_ejes(a, b)
        + PESOS["sistemas"] * _sim_sistemas(a, b)
        + PESOS["gustos"] * _sim_gustos(a, b)
        + PESOS["vibra"] * _sim_vibra(a, b)
        - CASTIGO_VELO * velos_en_conflicto(a, b)
    )
    puntaje = max(0, min(100, round(total)))
    coinciden, difieren = explicar(a, b)
    return Resultado(True, puntaje, coinciden, difieren, sesion_en_comun=sesion_en_comun(a, b))


def prioridad_rol(a: Ficha, b: Ficha) -> int:
    """0 = se muestra primero. Un máster ve antes a jugadores y viceversa."""
    if a.rol == "master" and b.rol in ("jugador", "ambos"):
        return 0
    if a.rol == "jugador" and b.rol in ("master", "ambos"):
        return 0
    return 1


def ordenar(a: Ficha, candidatas: list[Ficha]):
    resultados = []
    for b in candidatas:
        r = evaluar(a, b)
        if r.visible:
            resultados.append((b, r))
    resultados.sort(key=lambda br: (prioridad_rol(a, br[0]), -br[1].puntaje))
    return resultados


# ------------------------------------------------------------ puente con la base de datos
def ficha_desde_perfil(p, hoy: date | None = None) -> Ficha:
    hoy = hoy or date.today()
    fin = hoy + timedelta(days=DIAS_HORIZONTE)
    from perfiles.models import ATRIBUTOS, EJES  # import tardío: el motor no depende de Django al probarse

    return Ficha(
        id=p.pk,
        alias=p.alias,
        rol=p.rol,
        modalidad=p.modalidad,
        comunas={c.pk for c in p.comunas.all()},
        plataformas={x.pk for x in p.plataformas.all()},
        compromisos=p.compromisos,
        idiomas=p.lista_idiomas,
        mesa_pagada=p.mesa_pagada,
        precio=p.precio,
        bloques={(d.fecha, d.bloque) for d in p.disponibilidad.all() if hoy <= d.fecha < fin},
        atributos={c: getattr(p, c) for c, _ in ATRIBUTOS if getattr(p, c)},
        ejes={c: getattr(p, c) for c, *_ in EJES},
        sistemas={ps.sistema.nombre: ps.relacion for ps in p.perfilsistema_set.all()},
        tonos={t.nombre for t in p.tonos.all()},
        arquetipos={t.nombre for t in p.arquetipos.all()},
        ambientaciones={t.nombre for t in p.ambientaciones.all()},
        temas={lt.tema_id: lt.estado for lt in p.limites.all()},
        vibra={"ambiente": p.ambiente, "alcohol": p.alcohol, "comida": p.comida, "tabaco": p.tabaco, "amistad": p.busca_amistad},
        bloqueados={b.a_id for b in p.bloqueos_dados.all()},
    )


PREFETCH = (
    "comunas", "plataformas", "disponibilidad", "perfilsistema_set__sistema", "tonos", "arquetipos",
    "ambientaciones", "limites", "bloqueos_dados",
)
