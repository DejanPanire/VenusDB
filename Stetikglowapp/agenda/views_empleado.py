"""Vistas del empleado: mi agenda, reservas asignadas y perfil."""
from datetime import timedelta

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from funciones_app.models import Atencion

from . import reglas
from .permisos import empleado_requerido
from .reglas import Estado, nombre_completo
from .views import fecha_larga, parse_fecha


def _hoy():
    return timezone.localdate()


# --- Ver agenda propia ---
@empleado_requerido
def mi_agenda(request):
    t = request.trabajador
    fecha = parse_fecha(request.GET.get("fecha"), por_defecto=_hoy())
    reservas = reglas.preparar(reglas.reservas_con_detalle().filter(trabajador=t, fecha=fecha))
    bloqueos = reglas.tramos_no_disponibles(t, fecha)
    items = sorted(
        [("reserva", r.hora_inicio, r) for r in reservas] + [("bloqueo", b.hora_inicio, b) for b in bloqueos],
        key=lambda i: i[1],
    )
    resumen = [(label, sum(1 for r in reservas if r.estado == e)) for e, label in reglas.ESTADOS]
    return render(request, "agenda/empleado/agenda.html", {
        "seccion": "agenda",
        "fecha": fecha,
        "fecha_texto": fecha_larga(fecha),
        "fecha_ant": fecha - timedelta(days=1),
        "fecha_sig": fecha + timedelta(days=1),
        "hoy": _hoy(),
        "items": items,
        "n_reservas": len(reservas),
        "resumen": resumen,
    })


# --- Gestionar reservas asignadas ---
@empleado_requerido
def reservas_asignadas(request):
    t = request.trabajador
    hoy = _hoy()
    filtro = request.GET.get("filtro", "proximas")
    reservas = reglas.reservas_con_detalle().filter(trabajador=t)
    if filtro == "pendientes":
        reservas = reservas.filter(estado=Estado.PENDIENTE, fecha__gte=hoy).order_by("fecha", "hora_inicio")
    elif filtro == "historial":
        reservas = reservas.filter(fecha__lt=hoy).order_by("-fecha", "-hora_inicio")
    else:
        filtro = "proximas"
        reservas = reservas.filter(fecha__gte=hoy).order_by("fecha", "hora_inicio")
    return render(request, "agenda/empleado/reservas.html", {
        "seccion": "reservas",
        "filtro": filtro,
        "filtros": [("proximas", "Próximas"), ("pendientes", "Por confirmar"), ("historial", "Historial")],
        "reservas": reglas.preparar(reservas[:100]),
        "hoy": hoy,
    })


@empleado_requerido
@require_POST
def cambiar_estado_reserva(request, pk):
    reserva = get_object_or_404(reglas.reservas_con_detalle(), pk=pk, trabajador=request.trabajador)
    if reglas.aplicar_accion(reserva, request.POST.get("accion"), {"confirmar", "cancelar"}):
        messages.success(request, f"Reserva de {nombre_completo(reserva.cliente)}: {reserva.estado.lower()}.")
    else:
        messages.error(request, "Esa acción no es válida para el estado actual de la reserva.")
    return redirect(request.POST.get("volver") or "reservas_asignadas")


# --- Ver perfil ---
@empleado_requerido
def perfil(request):
    t = request.trabajador
    return render(request, "agenda/empleado/perfil.html", {
        "seccion": "perfil", "t": t,
        "atenciones_mes": Atencion.objects.filter(
            reserva__trabajador=t, fecha__date__gte=_hoy().replace(day=1)).count(),
    })
