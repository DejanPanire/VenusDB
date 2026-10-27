import re
from urllib.parse import urlencode
from datetime import date, datetime, time, timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from funciones_app.models import Cliente, Servicio, Sucursal, Trabajador

from . import catalogo, reglas
from .reglas import Estado, HORA_APERTURA, nombre_completo
from .permisos import (
    es_empleado, es_propietario, gestion_requerida, pagina_inicial, rol_de, sucursal_actual,
    sucursales_permitidas,
)
from .utils import formatear_rut, validar_rut

DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]
PX_POR_BLOQUE = 60  # alto de cada bloque de 30 min


def fecha_larga(d: date) -> str:
    return f"{DIAS[d.weekday()]} {d.day} de {MESES[d.month - 1]}"


def parse_fecha(valor, por_defecto=None):
    try:
        return datetime.strptime(valor, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return por_defecto or date.today()


# --- Autenticación ---
def inicio(request):
    return redirect(pagina_inicial(request.user) if request.user.is_authenticated else "login")


def login_view(request):
    if request.user.is_authenticated and rol_de(request.user):
        return redirect(pagina_inicial(request.user))
    error, errores, usuario = "", {}, ""
    if request.method == "POST":
        usuario = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        if not usuario:
            errores["email"] = "El usuario es obligatorio"
        if not password:
            errores["password"] = "La contraseña es obligatoria"
        if not errores:
            user = authenticate(request, username=usuario, password=password)
            if user is None:
                error = ("Tu cuenta no está activa. Contacta a la administración."
                         if getattr(request, "usuario_inactivo", False) else "Credenciales incorrectas.")
            elif rol_de(user) is None:
                error = "Tu usuario no tiene una ficha de trabajador asignada. Contacta a la propietaria."
            else:
                login(request, user)
                local = sucursal_actual(request)
                request.session["sucursal_id"] = local.pk if local else None
                return redirect(request.GET.get("next") or pagina_inicial(user))
    return render(request, "agenda/login.html", {"errores": errores, "error": error, "email": usuario})


@login_required
@require_POST
def cambiar_sucursal(request):
    """Solo la propietaria puede cambiar de local."""
    if not es_propietario(request.user):
        messages.error(request, "No tienes permiso para cambiar de local.")
        return redirect("calendario")
    local = Sucursal.objects.filter(pk=request.POST.get("sucursal") or 0).first()
    if local:
        request.session["sucursal_id"] = local.pk
    return redirect(request.POST.get("volver") or "calendario")


def logout_view(request):
    logout(request)
    return redirect("login")


# --- Calendario ---
@gestion_requerida
def calendario(request):
    sucursal = sucursal_actual(request)
    fecha = parse_fecha(request.GET.get("fecha"))
    tab = request.GET.get("tab", "agenda")
    trabajador_id = request.GET.get("trabajador", "todos")
    servicio_id = request.GET.get("servicio", "todos")
    q = request.GET.get("q", "").strip()

    trabajadores = list(reglas.trabajadores_que_atienden(sucursal))
    reservas = reglas.reservas_con_detalle().filter(sucursal=sucursal, fecha=fecha)
    if trabajador_id.isdigit():
        reservas = reservas.filter(trabajador_id=int(trabajador_id))
    if servicio_id.isdigit():
        reservas = reservas.filter(detalles_reserva__servicio_id=int(servicio_id))
    if q:
        reservas = reservas.filter(cliente__nombre__icontains=q) | reservas.filter(cliente__apellido__icontains=q)
    reservas = reglas.preparar(reservas.distinct().order_by("hora_inicio"))

    def estilo(inicio: time, fin: time):
        ini_min = (inicio.hour - HORA_APERTURA.hour) * 60 + inicio.minute
        dur = (fin.hour - inicio.hour) * 60 + (fin.minute - inicio.minute)
        return f"top:{ini_min / 30 * PX_POR_BLOQUE + 1}px;height:{dur / 30 * PX_POR_BLOQUE - 2}px"

    for r in reservas:
        r.estilo = estilo(r.hora_inicio, r.hora_fin)
        minutos = (r.hora_fin.hour - r.hora_inicio.hour) * 60 + r.hora_fin.minute - r.hora_inicio.minute
        # xs = 1 línea, sm = texto corto, lg = texto completo
        r.tamano = "xs" if minutos < 30 else "sm" if minutos < 60 else "lg"

    columnas = []
    for t in trabajadores:
        bloqueos = reglas.tramos_no_disponibles(t, fecha)
        for b in bloqueos:
            b.estilo = estilo(b.hora_inicio, b.hora_fin)
        columnas.append({
            "trabajador": t,
            "reservas": [r for r in reservas if r.trabajador_id == t.id],
            "bloqueos": bloqueos,
        })
    # reservas sin trabajadora asignada
    sin_asignar = [r for r in reservas if r.trabajador_id is None]

    franjas = []
    for i in range(21):
        h, m = divmod(i * 30, 60)
        franjas.append(f"{HORA_APERTURA.hour + h:02d}:{m:02d}")

    seleccionada = None
    if request.GET.get("reserva", "").isdigit():
        encontrada = reglas.reservas_con_detalle().filter(pk=int(request.GET["reserva"]), sucursal=sucursal)
        seleccionada = next(iter(reglas.preparar(encontrada)), None)

    resumen = [(e, label, sum(1 for r in reservas if r.estado == e)) for e, label in reglas.ESTADOS]
    sala_espera = [r for r in reservas if r.estado == Estado.CONFIRMADA] if fecha == date.today() else []

    libres, ocupados = [], [r for r in reservas if r.estado != Estado.CANCELADA][:3]
    if trabajador_id.isdigit():
        t_sel = next((t for t in trabajadores if t.id == int(trabajador_id)), None)
        if t_sel:
            libres = reglas.horarios_disponibles(t_sel, fecha, 60)[:6]

    return render(request, "agenda/calendario.html", {
        "seccion": "calendario",
        "sucursal": sucursal,
        "fecha": fecha,
        "fecha_texto": fecha_larga(fecha),
        "fecha_ant": fecha - timedelta(days=1),
        "fecha_sig": fecha + timedelta(days=1),
        "hoy": date.today(),
        "tab": tab,
        "qs_base": urlencode({"tab": tab, "trabajador": trabajador_id, "servicio": servicio_id, "q": q}),
        "tabs": [("resumen", "Resumen de citas", "calendar"), ("listado", "Listado de citas", "list"),
                 ("agenda", "Agenda del día", "layout-grid"), ("sala", "Sala de espera", "users")],
        "trabajadores": trabajadores,
        "trabajador_id": trabajador_id,
        "servicios": Servicio.objects.order_by("categoria_cliente", "id"),
        "servicio_id": servicio_id,
        "q": q,
        "columnas": columnas,
        "sin_asignar": sin_asignar,
        "franjas": franjas,
        "reservas": reservas,
        "resumen": resumen,
        "sala_espera": sala_espera,
        "seleccionada": seleccionada,
        "libres": libres,
        "ocupados": ocupados,
    })


@gestion_requerida
@require_POST
def cambiar_estado(request, pk):
    reserva = get_object_or_404(reglas.reservas_con_detalle(), pk=pk, sucursal__in=sucursales_permitidas(request.user))
    if reglas.aplicar_accion(reserva, request.POST.get("accion"), {"confirmar", "completar", "cancelar"}):
        messages.success(request, f"Reserva de {nombre_completo(reserva.cliente)}: {reserva.estado.lower()}.")
    else:
        messages.error(request, "Esa acción no es válida para el estado actual de la reserva.")
    return redirect(request.POST.get("volver") or "calendario")


# --- Reservas ---
def reservar(request):
    """Reserva en 3 pasos. Es pública para el código QR."""
    if es_empleado(request.user):
        return redirect("mi_agenda")
    autenticado = request.user.is_authenticated and rol_de(request.user) is not None
    sucursales = sucursales_permitidas(request.user) if autenticado else Sucursal.objects.order_by("id")
    sucursal_defecto = sucursal_actual(request) if autenticado else sucursales.first()
    datos = request.POST if request.method == "POST" else request.GET
    errores, exito, paso = {}, None, 1

    if request.method == "POST":
        paso = 3
        rut = formatear_rut(datos.get("rut", ""))
        nombre, apellido = datos.get("nombre", "").strip(), datos.get("apellido", "").strip()
        telefono, correo = datos.get("telefono", "").strip(), datos.get("email", "").strip().lower()

        if not rut:
            errores["rut"] = "El RUT es obligatorio"
        elif not validar_rut(rut):
            errores["rut"] = "RUT inválido"
        if not nombre:
            errores["nombre"] = "El nombre es obligatorio"
        if not apellido:
            errores["apellido"] = "El apellido es obligatorio"
        if not telefono:
            errores["telefono"] = "El teléfono es obligatorio"
        elif not re.fullmatch(r"\+?[0-9]{9,12}", telefono.replace(" ", "")):
            errores["telefono"] = "Teléfono inválido"
        if not correo:
            errores["email"] = "El correo es obligatorio"
        elif not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", correo):
            errores["email"] = "Correo inválido"
        elif rut and Cliente.objects.filter(correo__iexact=correo).exclude(rut=rut).exists():
            errores["email"] = "Ese correo ya está registrado con otro RUT"

        servicio = Servicio.objects.filter(pk=datos.get("servicio") or 0).first()
        sucursal = Sucursal.objects.filter(pk=datos.get("sucursal") or 0).first()
        trabajador = Trabajador.objects.filter(pk=datos.get("trabajadora") or 0).first()
        fecha = parse_fecha(datos.get("fecha"), por_defecto=None)
        try:
            hora = datetime.strptime(datos.get("hora", ""), "%H:%M").time()
        except ValueError:
            hora = None
        if not sucursal:
            errores["sucursal"] = "Selecciona un local"
        elif not sucursales.filter(pk=sucursal.pk).exists():
            errores["sucursal"] = "No tienes permiso para reservar en ese local"
            sucursal = None
        if not servicio:
            errores["servicio"] = "Selecciona un servicio"
        if not trabajador:
            errores["trabajadora"] = "Selecciona una trabajadora"
        if not hora:
            errores["hora"] = "Selecciona un horario"
        if fecha < date.today():
            errores["fecha"] = "La fecha no puede ser anterior a hoy"

        if not errores:
            if trabajador.sucursal_id != sucursal.id or not reglas.trabajadores_que_atienden(sucursal).filter(pk=trabajador.pk).exists():
                errores["trabajadora"] = "La trabajadora no atiende en el local elegido"
            else:
                try:
                    with transaction.atomic():
                        cliente, _ = Cliente.objects.update_or_create(
                            rut=rut, defaults={"nombre": nombre, "apellido": apellido, "telefono": telefono, "correo": correo})
                        exito = reglas.crear_reserva(
                            cliente=cliente, sucursal=sucursal, trabajador=trabajador, servicios=[servicio],
                            fecha=fecha, hora_inicio=hora,
                            origen=reglas.ORIGEN_SISTEMA if autenticado else reglas.ORIGEN_WEB)
                    exito = reglas.preparar(reglas.reservas_con_detalle().filter(pk=exito.pk))[0]
                except ValidationError as e:
                    errores["hora"] = " ".join(e.messages)
        if errores and not exito:
            campos_paso1 = {"rut", "nombre", "apellido", "telefono", "email"}
            paso = 1 if campos_paso1 & set(errores) else 2

    return render(request, "agenda/reservar.html", {
        "layout": "agenda/base_app.html" if autenticado else "agenda/base_publica.html",
        "seccion": "reservar",
        "sucursales": sucursales,
        "servicios": Servicio.objects.order_by("categoria_cliente", "id"),
        "sucursal_defecto": datos.get("sucursal") or (sucursal_defecto.pk if sucursal_defecto else ""),
        "d": datos,
        "errores": errores,
        "paso": paso,
        "exito": exito,
        "fecha_defecto": datos.get("fecha") or date.today().isoformat(),
        "hora_defecto": datos.get("hora", ""),
        "trabajadora_defecto": datos.get("trabajadora") or datos.get("trabajador", ""),
        "hoy_iso": date.today().isoformat(),
    })


# --- API ---
def api_trabajadoras(request):
    """Trabajadoras del local que hacen el servicio."""
    sucursal = Sucursal.objects.filter(pk=request.GET.get("sucursal") or 0).first()
    if not sucursal:
        return JsonResponse({"trabajadoras": []})
    qs = reglas.trabajadores_que_atienden(sucursal)
    servicio = Servicio.objects.filter(pk=request.GET.get("servicio") or 0).first()
    if servicio and catalogo.area_de(servicio):
        especialistas = qs.filter(especialidad__iexact=catalogo.area_de(servicio))
        if especialistas.exists():
            qs = especialistas
    return JsonResponse({"trabajadoras": [
        {"id": t.id, "nombre": nombre_completo(t), "especialidad": t.especialidad or t.rol} for t in qs]})


def api_disponibilidad(request):
    trabajador = Trabajador.objects.filter(pk=request.GET.get("trabajadora") or 0).first()
    servicio = Servicio.objects.filter(pk=request.GET.get("servicio") or 0).first()
    fecha = parse_fecha(request.GET.get("fecha"))
    if not (trabajador and servicio):
        return JsonResponse({"horarios": []})
    return JsonResponse({"horarios": reglas.horarios_disponibles(trabajador, fecha, servicio.duracion_minutos)})
