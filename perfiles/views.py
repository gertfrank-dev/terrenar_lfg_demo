"""
Vistas: la "cocina" que arma cada página.
"""
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from match.motor import PREFETCH, ficha_desde_perfil, ordenar

from .models import ATRIBUTOS, EJES, Interes, LimiteTema, Perfil, hay_interes_mutuo

ATR_CORTOS = ("COMBATE", "EXPLOR.", "INTERP.", "MISTERIO", "ESTRAT.", "HUMOR")
DEMO_EMAIL = "demo0@demo.bestiario"  # Valentina R., máster de la demo


def portada(request):
    return render(request, "portada.html", {"total": Perfil.objects.filter(publicado=True).count()})


@require_POST
def entrar_demo(request):
    """Entra como un perfil de demo para recorrer el sitio sin registrarse."""
    if not getattr(settings, "DEMO_LOGIN", True):
        raise Http404
    user = get_object_or_404(get_user_model(), email=DEMO_EMAIL)
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    messages.info(request, "Entraste como Valentina R., una máster de prueba.")
    return redirect("explorar")


def _mi_perfil(request):
    return Perfil.objects.filter(usuario=request.user).prefetch_related(*PREFETCH).first()


@login_required
def mi_perfil(request):
    yo = _mi_perfil(request)
    if not yo:
        return render(request, "sin_perfil.html")
    return redirect("perfil", pk=yo.pk)


@login_required
def explorar(request):
    yo = _mi_perfil(request)
    if not yo:
        return redirect("mi_perfil")
    filtro_rol = request.GET.get("rol", "todos")
    candidatas = Perfil.objects.filter(publicado=True).exclude(pk=yo.pk).prefetch_related(*PREFETCH)
    if filtro_rol in ("jugador", "master"):
        candidatas = candidatas.filter(rol__in=[filtro_rol, "ambos"])
    por_id = {p.pk: p for p in candidatas}
    yo_f = ficha_desde_perfil(yo)
    resultados = [
        {"perfil": por_id[f.id], "r": r}
        for f, r in ordenar(yo_f, [ficha_desde_perfil(p) for p in candidatas])
    ]
    ctx = {"yo": yo, "resultados": resultados, "filtro_rol": filtro_rol, "ocultos": len(por_id) - len(resultados)}
    plantilla = "parciales/resultados.html" if request.htmx else "explorar.html"
    return render(request, plantilla, ctx)


def _contexto_perfil(request, p):
    yo = _mi_perfil(request) if request.user.is_authenticated else None
    propio = yo is not None and yo.pk == p.pk
    mutuo = bool(yo) and not propio and hay_interes_mutuo(yo, p)
    mi_interes = bool(yo) and not propio and Interes.objects.filter(de=yo, a=p).exists()
    resultado = None
    if yo and not propio:
        from match.motor import evaluar

        resultado = evaluar(ficha_desde_perfil(yo), ficha_desde_perfil(p))
    # PRIVACIDAD: las líneas y el contacto solo se cargan si es tu perfil o hay interés mutuo.
    limites = None
    if propio or mutuo:
        limites = LimiteTema.objects.filter(perfil=p).exclude(estado="ok").select_related("tema").order_by("estado", "tema__orden")
    return {
        "p": p,
        "yo": yo,
        "propio": propio,
        "mutuo": mutuo,
        "mi_interes": mi_interes,
        "resultado": resultado,
        "limites": limites,
        "atributos": [(corto, getattr(p, campo)) for (campo, _), corto in zip(ATRIBUTOS, ATR_CORTOS)],
        "campanas": " · ".join(n for n, ok in (("one-shot", p.one_shot), ("campaña corta", p.campana_corta), ("campaña larga", p.campana_larga)) if ok),
        "ejes": [(nombre, bajo, alto, getattr(p, campo)) for campo, nombre, bajo, alto in EJES],
    }


def perfil(request, pk):
    p = get_object_or_404(Perfil.objects.prefetch_related(*PREFETCH), pk=pk, publicado=True)
    return render(request, "perfil.html", _contexto_perfil(request, p))


@login_required
@require_POST
def interes(request, pk):
    yo = _mi_perfil(request)
    p = get_object_or_404(Perfil, pk=pk, publicado=True)
    if not yo or yo.pk == p.pk:
        raise Http404
    existente = Interes.objects.filter(de=yo, a=p)
    if existente.exists():
        existente.delete()
    else:
        Interes.objects.create(de=yo, a=p)
        # En la demo, los perfiles ficticios responden: así se puede ver cómo se revela el match mutuo.
        if p.es_demo and yo.es_demo:
            Interes.objects.get_or_create(de=p, a=yo)
    p = Perfil.objects.prefetch_related(*PREFETCH).get(pk=p.pk)
    ctx = _contexto_perfil(request, p)
    if request.htmx:
        return render(request, "parciales/interes.html", ctx)
    return redirect("perfil", pk=pk)
