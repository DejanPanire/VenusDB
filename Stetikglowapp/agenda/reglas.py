"""Lógica de la agenda: horarios, turnos y reservas.

Los turnos marcan cuándo atiende cada trabajadora; lo que queda fuera (por ejemplo
la colación) se bloquea. Si un día no tiene turnos se usa el horario del local.
"""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from funciones_app.models import Atencion, DetalleAtencion, DetalleReserva, Reserva, Trabajador, Turno

HORA_APERTURA = time(10, 0)
HORA_CIERRE = time(20, 0)


class Estado:
    PENDIENTE = "Pendiente"
    CONFIRMADA = "Confirmada"
    COMPLETADA = "Completada"
    CANCELADA = "Cancelada"


ESTADOS = Reserva.ESTADOS
ORIGEN_WEB = "Web/QR"         # reservó la clienta
ORIGEN_SISTEMA = "Sistema"    # la ingresó el local

# clases de venus.css
CLASES_ESTADO = {
    Estado.PENDIENTE: "estado-pendiente",
    Estado.CONFIRMADA: "estado-confirmada",
    Estado.COMPLETADA: "estado-completada",
    Estado.CANCELADA: "estado-cancelada",
}


# --- Utilidades ---
def clp(valor) -> str:
    return "$" + f"{int(Decimal(valor or 0)):,}".replace(",", ".")


def nombre_completo(persona) -> str:
    return f"{persona.nombre} {persona.apellido or ''}".strip()


def ahora_local() -> datetime:
    return timezone.localtime().replace(tzinfo=None)


def sumar_minutos(fecha: date, hora: time, minutos: int) -> time:
    return (datetime.combine(fecha, hora) + timedelta(minutes=minutos)).time()


def nombre_servicio(servicio) -> str:
    # con la categoría, porque hay nombres repetidos
    return f"{servicio.nombre} ({servicio.categoria_cliente})" if servicio.categoria_cliente else servicio.nombre


def reservas_con_detalle():
    return Reserva.objects.select_related("cliente", "trabajador", "sucursal").prefetch_related(
        "detalles_reserva__servicio")


def preparar(reservas):
    """Agrega servicios, precio y duración a cada reserva."""
    reservas = list(reservas)
    for r in reservas:
        detalles = list(r.detalles_reserva.all())
        r.servicios = [d.servicio for d in detalles]
        r.servicio_txt = ", ".join(nombre_servicio(s) for s in r.servicios) or "Sin servicio"
        r.precio_total = sum((d.precio_reservado for d in detalles), Decimal(0))
        r.precio_txt = clp(r.precio_total)
        r.duracion = sum(s.duracion_minutos for s in r.servicios)
    return reservas


def trabajadores_que_atienden(sucursal):
    """Trabajadoras del local, sin propietaria ni administradoras."""
    return (Trabajador.objects.filter(sucursal=sucursal)
            .exclude(Q(rol__istartswith="propiet") | Q(rol__istartswith="admin")).order_by("id"))


# --- Turnos y bloqueos ---
@dataclass
class Tramo:
    """Horario bloqueado (fuera de turno o colación)."""
    hora_inicio: time
    hora_fin: time
    motivo: str
    estilo: str = ""


def turnos_del_dia(trabajador, fecha):
    return Turno.objects.filter(trabajador=trabajador, fecha=fecha).order_by("hora_inicio")


def tramos_no_disponibles(trabajador, fecha):
    turnos = list(turnos_del_dia(trabajador, fecha))
    if not turnos:
        return []
    tramos, cursor = [], HORA_APERTURA
    for i, tu in enumerate(turnos):
        ini = max(tu.hora_inicio, HORA_APERTURA)
        if ini > cursor:
            tramos.append(Tramo(cursor, ini, "Colación" if i else "Fuera de turno"))
        cursor = max(cursor, min(tu.hora_fin, HORA_CIERRE))
    if cursor < HORA_CIERRE:
        tramos.append(Tramo(cursor, HORA_CIERRE, "Fuera de turno"))
    return tramos


def hay_conflicto(trabajador, fecha, inicio, fin, excluir=None) -> bool:
    reservas = Reserva.objects.filter(trabajador=trabajador, fecha=fecha).exclude(estado=Estado.CANCELADA)
    if excluir:
        reservas = reservas.exclude(pk=excluir)
    if reservas.filter(hora_inicio__lt=fin, hora_fin__gt=inicio).exists():
        return True
    return any(t.hora_inicio < fin and t.hora_fin > inicio for t in tramos_no_disponibles(trabajador, fecha))


def horarios_disponibles(trabajador, fecha: date, duracion_min: int):
    """Horas libres cada 30 minutos."""
    libres = []
    actual = datetime.combine(fecha, HORA_APERTURA)
    cierre = datetime.combine(fecha, HORA_CIERRE)
    ahora = ahora_local()
    while actual + timedelta(minutes=duracion_min) <= cierre:
        fin = actual + timedelta(minutes=duracion_min)
        if actual > ahora and not hay_conflicto(trabajador, fecha, actual.time(), fin.time()):
            libres.append(actual.strftime("%H:%M"))
        actual += timedelta(minutes=30)
    return libres


# --- Reservas ---
def validar_horario(trabajador, fecha, inicio, fin, excluir=None):
    if inicio < HORA_APERTURA or fin > HORA_CIERRE:
        raise ValidationError("La reserva queda fuera del horario de atención (10:00 - 20:00).")
    if hay_conflicto(trabajador, fecha, inicio, fin, excluir=excluir):
        raise ValidationError("La trabajadora ya tiene una reserva o está fuera de turno en ese horario.")


@transaction.atomic
def crear_reserva(*, cliente, sucursal, trabajador, servicios, fecha, hora_inicio, origen, estado=Estado.PENDIENTE):
    """Crea la reserva con su detalle."""
    servicios = list(servicios)
    if not servicios:
        raise ValidationError("Selecciona al menos un servicio.")
    fin = sumar_minutos(fecha, hora_inicio, sum(s.duracion_minutos for s in servicios))
    if estado != Estado.CANCELADA:
        validar_horario(trabajador, fecha, hora_inicio, fin)
    reserva = Reserva.objects.create(cliente=cliente, sucursal=sucursal, trabajador=trabajador, fecha=fecha,
                                     hora_inicio=hora_inicio, hora_fin=fin, estado=estado, origen=origen)
    DetalleReserva.objects.bulk_create(
        [DetalleReserva(reserva=reserva, servicio=s, precio_reservado=s.precio_base) for s in servicios])
    return reserva


@transaction.atomic
def registrar_atencion(reserva, observacion=""):
    """Registra la atención de una reserva completada."""
    atencion = Atencion.objects.filter(reserva=reserva).first()
    if atencion:
        return atencion
    atencion = Atencion.objects.create(reserva=reserva, observacion=observacion or None)
    DetalleAtencion.objects.bulk_create([
        DetalleAtencion(atencion=atencion, servicio=d.servicio, precio_aplicado=d.precio_reservado)
        for d in reserva.detalles_reserva.select_related("servicio")
    ])
    return atencion


def aplicar_accion(reserva, accion, permitidas):
    """Cambia el estado de la reserva. Devuelve False si no se puede."""
    transiciones = {
        "confirmar": ((Estado.PENDIENTE,), Estado.CONFIRMADA),
        "completar": ((Estado.CONFIRMADA,), Estado.COMPLETADA),
        "cancelar": ((Estado.PENDIENTE, Estado.CONFIRMADA), Estado.CANCELADA),
    }
    if accion not in permitidas or accion not in transiciones or reserva.estado not in transiciones[accion][0]:
        return False
    with transaction.atomic():
        reserva.estado = transiciones[accion][1]
        reserva.save(update_fields=["estado"])
        if reserva.estado == Estado.COMPLETADA:
            registrar_atencion(reserva)
    return True
