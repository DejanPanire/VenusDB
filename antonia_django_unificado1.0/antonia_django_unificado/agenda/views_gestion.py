"""Módulos de gestión traídos de Stetikglowapp, con la estética de Venus.

- Inventario de insumos (InventarioList / Create / Update / Delete)
- Plan de inventario (PlanInventarioView / Create / Update / Recibir)
- Atenciones y ventas (RegistrarAtencion / VentaList)
- Servicios (ServicioList)
Solo para propietaria y administradoras; cada una ve los locales que le corresponden.
"""
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.db.models import Count, F, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from funciones_app.models import (
    Atencion, DetalleAtencion, DetalleVenta, Inventario, Pago, PlanInventario, ProductoInsumo, Reserva, Servicio,
    Venta,
)

from . import catalogo
from .forms import AtencionForm, InventarioForm, PlanInventarioForm, ServicioForm
from .permisos import es_propietario, gestion_requerida, sucursal_actual, sucursales_permitidas
from .reglas import Estado
from .views import parse_fecha

EN_PROCESO, COMPLETADO = "Processing", "Completado"   # estados de PlanInventario


def local_elegido(request):
    """Local del selector (?local=) si está permitido; si no, el local activo."""
    permitidas = sucursales_permitidas(request.user)
    pedido = request.GET.get("local", "")
    return (permitidas.filter(pk=pedido).first() if pedido.isdigit() else None) or sucursal_actual(request)


def url_con_local(nombre, sucursal):
    return f"{reverse(nombre)}?local={sucursal.pk}"


def formulario(request, form, titulo, volver, seccion, bajada="", **extra):
    return render(request, "agenda/gestion/formulario.html", {
        "form": form, "titulo": titulo, "volver": volver, "seccion": seccion, "bajada": bajada, **extra})


# ======================================================================
# Inventario de insumos
# ======================================================================
@gestion_requerida
def inventario(request):
    sucursal = local_elegido(request)
    q = request.GET.get("q", "").strip()
    items = Inventario.objects.filter(sucursal=sucursal).select_related("producto").order_by("producto__nombre")
    if q:
        items = items.filter(Q(producto__nombre__icontains=q) | Q(producto__categoria__icontains=q))
    return render(request, "agenda/gestion/inventario.html", {
        "seccion": "inventario",
        "local": sucursal,
        "locales": sucursales_permitidas(request.user),
        "inventarios": items,
        "stock_bajo": Inventario.objects.filter(sucursal=sucursal, cantidad__lte=F("producto__stock_minimo")).count(),
        "planes_activos": PlanInventario.objects.filter(sucursal=sucursal, estado=EN_PROCESO).count(),
        "q": q,
    })


@gestion_requerida
def inventario_nuevo(request):
    sucursal = local_elegido(request)
    form = InventarioForm(request.POST or None, sucursales=sucursales_permitidas(request.user),
                          initial={"sucursal": sucursal})
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        with transaction.atomic():
            producto, creado = ProductoInsumo.objects.get_or_create(
                nombre__iexact=d["nombre"].strip(),
                defaults={"nombre": d["nombre"].strip(), "categoria": d["categoria"] or None,
                          "descripcion": d["descripcion"] or None, "stock_minimo": d["stock_minimo"],
                          "es_insumo": d["es_insumo"]})
            if Inventario.objects.filter(sucursal=d["sucursal"], producto=producto).exists():
                form.add_error("nombre", "Ese insumo ya está en el inventario de este local: edítalo desde la lista.")
            else:
                Inventario.objects.create(sucursal=d["sucursal"], producto=producto, cantidad=d["cantidad"])
                messages.success(request, f"Insumo «{producto.nombre}» agregado.")
                return redirect(url_con_local("inventario", d["sucursal"]))
    return formulario(request, form, "Agregar insumo", url_con_local("inventario", sucursal), "inventario",
                      "Si el producto ya existe en otro local se reutiliza su ficha.")


@gestion_requerida
def inventario_editar(request, pk):
    item = get_object_or_404(Inventario.objects.select_related("producto", "sucursal"), pk=pk,
                             sucursal__in=sucursales_permitidas(request.user))
    p = item.producto
    form = InventarioForm(request.POST or None, sucursales=sucursales_permitidas(request.user).filter(pk=item.sucursal_id),
                          initial={"nombre": p.nombre, "categoria": p.categoria, "descripcion": p.descripcion,
                                   "sucursal": item.sucursal, "cantidad": item.cantidad,
                                   "stock_minimo": p.stock_minimo, "es_insumo": p.es_insumo})
    form.fields["sucursal"].disabled = True
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        with transaction.atomic():
            p.nombre, p.categoria, p.descripcion = d["nombre"], d["categoria"] or None, d["descripcion"] or None
            p.stock_minimo, p.es_insumo = d["stock_minimo"], d["es_insumo"]
            p.save()
            item.cantidad = d["cantidad"]
            item.save()
        messages.success(request, "Insumo actualizado.")
        return redirect(url_con_local("inventario", item.sucursal))
    return formulario(request, form, "Editar insumo", url_con_local("inventario", item.sucursal), "inventario",
                      f"{item.sucursal.nombre} · el stock mínimo es del producto (aplica a todos los locales).")


@gestion_requerida
def inventario_eliminar(request, pk):
    item = get_object_or_404(Inventario.objects.select_related("producto", "sucursal"), pk=pk,
                             sucursal__in=sucursales_permitidas(request.user))
    volver = url_con_local("inventario", item.sucursal)
    if request.method == "POST":
        item.delete()
        messages.success(request, f"«{item.producto.nombre}» se retiró del inventario de {item.sucursal.nombre}.")
        return redirect(volver)
    return render(request, "agenda/gestion/confirmar.html", {
        "seccion": "inventario", "titulo": "¿Eliminar este registro?", "volver": volver, "boton": "Sí, eliminar",
        "texto": f"Vas a retirar del inventario el insumo «{item.producto.nombre}» del local {item.sucursal.nombre}. "
                 "La ficha del producto se mantiene."})


# ======================================================================
# Plan de inventario
# ======================================================================
@gestion_requerida
def plan_inventario(request):
    sucursal = local_elegido(request)
    planes = PlanInventario.objects.filter(sucursal=sucursal).select_related("producto", "sucursal")
    return render(request, "agenda/gestion/plan_inventario.html", {
        "seccion": "inventario",
        "local": sucursal,
        "locales": sucursales_permitidas(request.user),
        "en_proceso": planes.filter(estado=EN_PROCESO).order_by("-fecha_solicitud", "-id"),
        "completados": planes.filter(estado=COMPLETADO).order_by("-fecha_actualizacion"),
    })


@gestion_requerida
def plan_nuevo(request):
    sucursal = local_elegido(request)
    form = PlanInventarioForm(request.POST or None, sucursales=sucursales_permitidas(request.user),
                              initial={"sucursal": sucursal})
    if request.method == "POST" and form.is_valid():
        plan = form.save(commit=False)
        plan.estado = EN_PROCESO
        plan.save()
        messages.success(request, f"Plan «{plan.titulo}» creado.")
        return redirect(url_con_local("plan_inventario", plan.sucursal))
    return formulario(request, form, "Crear plan de inventario", url_con_local("plan_inventario", sucursal),
                      "inventario", "Solicitud de reposición: al recibirla, las unidades se suman al inventario.")


@gestion_requerida
def plan_editar(request, pk):
    plan = get_object_or_404(PlanInventario, pk=pk, estado=EN_PROCESO,
                             sucursal__in=sucursales_permitidas(request.user))
    form = PlanInventarioForm(request.POST or None, instance=plan, sucursales=sucursales_permitidas(request.user))
    if request.method == "POST" and form.is_valid():
        plan = form.save()
        messages.success(request, "Plan actualizado.")
        return redirect(url_con_local("plan_inventario", plan.sucursal))
    return formulario(request, form, f"Editar plan #{plan.pk}", url_con_local("plan_inventario", plan.sucursal),
                      "inventario")


@gestion_requerida
@require_POST
def plan_recibir(request, pk):
    plan = get_object_or_404(PlanInventario.objects.select_related("producto", "sucursal"), pk=pk,
                             sucursal__in=sucursales_permitidas(request.user))
    if plan.estado == EN_PROCESO:
        with transaction.atomic():
            plan.estado = COMPLETADO
            plan.save()
            item, creado = Inventario.objects.get_or_create(sucursal=plan.sucursal, producto=plan.producto,
                                                            defaults={"cantidad": plan.cantidad})
            if not creado:
                item.cantidad = F("cantidad") + plan.cantidad
                item.save()
        messages.success(request, f"Recibido: +{plan.cantidad} de «{plan.producto.nombre}» en {plan.sucursal.nombre}.")
    return redirect(url_con_local("plan_inventario", plan.sucursal))


# ======================================================================
# Atenciones y ventas
# ======================================================================
@gestion_requerida
def ventas(request):
    sucursal = local_elegido(request)
    hoy = date.today()
    desde = parse_fecha(request.GET.get("desde"), hoy - timedelta(days=30))
    hasta = parse_fecha(request.GET.get("hasta"), hoy)
    # rango con datetimes (fecha_hora__date necesita las tablas de zonas horarias en MySQL)
    inicio = timezone.make_aware(datetime.combine(desde, time.min))
    fin = timezone.make_aware(datetime.combine(hasta + timedelta(days=1), time.min))
    qs = (Venta.objects.filter(sucursal=sucursal, fecha_hora__gte=inicio, fecha_hora__lt=fin)
          .select_related("cliente", "empleado").prefetch_related("detalles__servicio", "pagos")
          .order_by("-fecha_hora"))
    lista = list(qs)
    for v in lista:
        v.servicios_txt = ", ".join(d.servicio.nombre for d in v.detalles.all() if d.servicio) or "—"
        v.metodo = ", ".join(p.metodo for p in v.pagos.all()) or "—"
        pct = v.empleado.porcentaje_comision if v.empleado else 0
        v.comision = (v.total * Decimal(pct) / 100) if v.estado != "Anulada" else Decimal(0)
    validas = [v for v in lista if v.estado != "Anulada"]
    por_trabajadora = (qs.exclude(estado="Anulada").exclude(empleado=None)
                       .values("empleado__nombre", "empleado__apellido", "empleado__porcentaje_comision")
                       .annotate(n=Count("id"), total=Sum("total")).order_by("-total"))
    comisiones = [{"NOMBRE": f"{c['empleado__nombre']} {c['empleado__apellido']}", "SERVICIOS": c["n"],
                   "TOTAL": c["total"], "COMISION": c["total"] * c["empleado__porcentaje_comision"] / 100}
                  for c in por_trabajadora]
    return render(request, "agenda/gestion/ventas.html", {
        "seccion": "ventas",
        "local": sucursal,
        "locales": sucursales_permitidas(request.user),
        "ventas": lista,
        "desde": desde,
        "hasta": hasta,
        "total": sum((v.total for v in validas), Decimal(0)),
        "n_ventas": len(validas),
        "total_comision": sum((v.comision for v in validas), Decimal(0)),
        "comisiones": comisiones,
        "extra_qs": f"desde={desde:%Y-%m-%d}&hasta={hasta:%Y-%m-%d}",
    })


@gestion_requerida
def registrar_atencion(request):
    """Atención + detalle + venta + pago en una sola transacción (RegistrarAtencion de Stetikglowapp)."""
    sucursal = local_elegido(request)
    reservas = (Reserva.objects.filter(sucursal=sucursal, estado__in=[Estado.CONFIRMADA, Estado.COMPLETADA],
                                       fecha__gte=date.today() - timedelta(days=7), fecha__lte=date.today())
                .filter(Q(atencion__isnull=True) | Q(atencion__venta__isnull=True))
                .select_related("cliente", "trabajador").order_by("-fecha", "hora_inicio"))
    inicial = {}
    elegida = reservas.filter(pk=request.GET.get("reserva") or 0).first()
    if elegida:
        inicial = {"reserva": elegida, "servicios": [d.servicio for d in elegida.detalles_reserva.all()]}
    form = AtencionForm(request.POST or None, reservas=reservas, initial=inicial)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        reserva = d["reserva"]
        with transaction.atomic():
            atencion, _ = Atencion.objects.get_or_create(reserva=reserva)
            atencion.observacion = d["observacion"] or atencion.observacion
            atencion.save()
            atencion.detalles.all().delete()
            total = Decimal(0)
            for s in d["servicios"]:
                DetalleAtencion.objects.create(atencion=atencion, servicio=s, precio_aplicado=s.precio_base)
                total += s.precio_base
            reserva.estado = Estado.COMPLETADA
            reserva.save(update_fields=["estado"])
            venta = Venta.objects.create(cliente=reserva.cliente, empleado=reserva.trabajador,
                                         sucursal=reserva.sucursal, atencion=atencion, total=total, estado="Pagada")
            DetalleVenta.objects.bulk_create([DetalleVenta(venta=venta, servicio=s, cantidad=1, subtotal=s.precio_base)
                                              for s in d["servicios"]])
            Pago.objects.create(venta=venta, monto=total, metodo=d["metodo_pago"])
        messages.success(request, f"Atención registrada y venta #{venta.pk} pagada ({d['metodo_pago']}).")
        return redirect(url_con_local("ventas", sucursal))
    if not reservas.exists():
        messages.info(request, "No hay reservas confirmadas de los últimos 7 días pendientes de cobro.")
    return formulario(request, form, "Registrar atención y cobro", url_con_local("ventas", sucursal), "ventas",
                      f"{sucursal.nombre} · marca la reserva como completada, registra la atención, la venta y el pago.")


# ======================================================================
# Servicios
# ======================================================================
@gestion_requerida
def servicios(request):
    return render(request, "agenda/gestion/servicios.html", {
        "seccion": "servicios", "servicios": Servicio.objects.order_by("categoria_cliente", "id"),
        "puede_editar": es_propietario(request.user)})


@gestion_requerida
def servicio_form(request, pk=None):
    if not es_propietario(request.user):
        messages.error(request, "Solo la propietaria puede cambiar servicios y precios.")
        return redirect("servicios")
    servicio = get_object_or_404(Servicio, pk=pk) if pk else None
    form = ServicioForm(request.POST or None, instance=servicio)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Servicio guardado. Las reservas ya hechas mantienen su precio.")
        return redirect("servicios")
    return formulario(request, form, f"Editar servicio" if servicio else "Nuevo servicio", reverse("servicios"),
                      "servicios", categorias=catalogo.AREAS)
