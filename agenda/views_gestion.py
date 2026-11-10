"""Módulos de gestión traídos de Stetikglowapp, con la estética de Venus.

- Inventario de insumos (InventarioList / Create / Update / Delete)
- Plan de inventario (PlanInventarioView / Create / Update / Recibir)
- Atenciones y ventas (RegistrarAtencion / VentaList)
- Servicios (ServicioList)
Solo para propietaria y administradoras; cada una ve los locales que le corresponden.
"""
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from funciones_app.models import *
from django.contrib import messages
from django.db import transaction
from django.db.models import Count, F, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from funciones_app.models import *
from django.contrib.auth.hashers import make_password
from . import catalogo
from .forms import *
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
def InventarioList(request, sucursal_id=None):
    sucursales = sucursales_permitidas(request.user) # Usar las sucursales permitidas del usuario
    
    # Determinar la sucursal actual
    if sucursal_id:
        sucursal_actual = get_object_or_404(Sucursal, id=sucursal_id)
    else:
        sucursal_actual = local_elegido(request) # Usar el local elegido del request

    # Filtrar los inventarios de esa sucursal
    inventarios = Inventario.objects.filter(sucursal=sucursal_actual).select_related('producto') if sucursal_actual else []
    alertas_stock = obtener_alertas_stock()

    context = {
        'sucursales': sucursales,
        'sucursal_actual': sucursal_actual,
        'inventarios': inventarios,
        'alertas_stock': alertas_stock,
        'seccion': 'inventario',
        'local': sucursal_actual,
        'locales': sucursales,
    }
    return render(request, 'agenda/gestion/inventariolista.html', context)

@gestion_requerida
def InventarioCreate(request):
    if request.method == 'POST':
        form = InventarioForm(request.POST)
        if form.is_valid():

            producto, created = ProductoInsumo.objects.get_or_create(
                nombre=form.cleaned_data['nombre'],
                defaults={
                    'categoria': form.cleaned_data['categoria'],
                    'descripcion': form.cleaned_data['descripcion'],
                    'marca': form.cleaned_data['marca'],
                    'valor_de_compra': form.cleaned_data['valor_de_compra'],
                    'stock_minimo': form.cleaned_data['stock_minimo'],
                    'unidad_medida': form.cleaned_data['unidad_medida'],
                    'stock': form.cleaned_data['cantidad'],
                }
            )
            if not created:
                producto.stock += form.cleaned_data['cantidad']
                producto.save()

            sucursal = form.cleaned_data['sucursal']
            inv, inv_created = Inventario.objects.get_or_create(
                sucursal=sucursal,
                producto=producto,
                defaults={'cantidad': form.cleaned_data['cantidad']}
            )
            if not inv_created:
                inv.cantidad += form.cleaned_data['cantidad']
                inv.save()

            return redirect('inventario_list_sucursal', sucursal_id=sucursal.id)
    else:
        form = InventarioForm()

@gestion_requerida
def InventarioUpdate(request, pk):
    inventario = get_object_or_404(Inventario, pk=pk)
    if request.method == 'POST':
        form = InventarioForm(request.POST)
        if form.is_valid():
            inv = inventario
            inv.sucursal = form.cleaned_data['sucursal']
            inv.cantidad = form.cleaned_data['cantidad']
            inv.save()
            return redirect('inventario_list_sucursal', sucursal_id=inv.sucursal.id)
    else:
        initial_data = {
            'nombre': inventario.producto.nombre if hasattr(inventario, 'producto') and inventario.producto else '',
            'sucursal': inventario.sucursal,
            'cantidad': getattr(inventario, 'cantidad', 1),
        }
        form = InventarioForm(initial=initial_data)
    
    context = {
        'form': form,
        'titulo': 'Editar Insumo',
        'alertas_stock': obtener_alertas_stock()
    }
    return render(request, 'agenda/gestion/inventarioFrom.html', context)

@gestion_requerida
def InventarioDelete(request, pk):
    inventario = get_object_or_404(Inventario, pk=pk)
    sucursal_id = inventario.sucursal.id
    if request.method == 'POST':
        inventario.delete()
        return redirect('inventario_list_sucursal', sucursal_id=sucursal_id)
    
    context = {
        'inventario': inventario,
        'alertas_stock': obtener_alertas_stock()
    }
    return render(request, 'agenda/gestion/inventarioDelete.html', context)

@gestion_requerida
def producto_detail(request, pk):
    item = get_object_or_404(ProductoInsumo, pk=pk)
    
    inventarios = Inventario.objects.filter(producto=item)
    stock_disponible = sum(inv.cantidad for inv in inventarios) if inventarios.exists() else item.stock

    context = {
        'item': item,
        'stock_disponible': stock_disponible,
        'alertas_stock': obtener_alertas_stock()
    }
    return render(request, 'agenda/gestion/productoDetail.html', context)


@gestion_requerida
@require_POST
def descontarStock(request, pk):
    item = get_object_or_404(ProductoInsumo, pk=pk)
    if request.method == 'POST':
        try:
            cantidad_a_restar = int(request.POST.get('cantidad', 1))
            if cantidad_a_restar > 0:
                with transaction.atomic():
                    inventarios = Inventario.objects.filter(producto=item)
                    for inv in inventarios:
                        if inv.cantidad >= cantidad_a_restar:
                            inv.cantidad -= cantidad_a_restar
                        else:
                            inv.cantidad = 0
                        inv.save()

                    total_actualizado = sum(inv.cantidad for inv in inventarios) if inventarios.exists() else (item.stock - cantidad_a_restar)
                    item.stock = max(0, total_actualizado)
                    item.save()
        except ValueError:
            pass
    return redirect('producto_detail', pk=item.pk)
# ======================================================================
# Plan de inventario
# ======================================================================
@gestion_requerida
def PlanInventarioView(request):
    sucursales = Sucursal.objects.all()
    planes_en_proceso = PlanInventario.objects.filter(estado='Processing')
    planes_completados = PlanInventario.objects.filter(estado='Completado')
    
    context = {
        'sucursales': sucursales,
        'planes_en_proceso': planes_en_proceso,
        'planes_completados': planes_completados,
        'alertas_stock': obtener_alertas_stock(),
    }
    return render(request, 'agenda/gestion/planinventario.html', context)



@gestion_requerida
def PlanInventarioCreate(request):
    if request.method == 'POST':
        form = PlanInventarioForm(request.POST)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.estado = 'Processing'  
            plan.save()
            return redirect('plan_inventario')  
    else:
        form = PlanInventarioForm()
    
    context = {
        'form': form,
        'alertas_stock': obtener_alertas_stock()
    }
    return render(request, 'agenda/gestion/planinventarioform.html', context)

@gestion_requerida
def PlanInventarioUpdate(request, pk):
    sucursales = Sucursal.objects.all()
    if request.method == 'POST':
        return redirect('plan_inventario')
    
    context = {
        'sucursales': sucursales,
        'plan_id': pk,
        'titulo': f'Editar Plan de Inventario #{pk}',
        'alertas_stock': obtener_alertas_stock()
    }
    return render(request, 'agenda/gestion/planinventarioform.html', context)


@gestion_requerida
@require_POST
def PlanInventarioRecibir(request, pk):
    with transaction.atomic():
        plan = get_object_or_404(PlanInventario, pk=pk)
        plan.estado = 'Completado'
        plan.save()
        
        # Actualizar stock del producto asociado
        if plan.producto:
            plan.producto.stock += plan.cantidad
            plan.producto.save()
        
        inventario, creado = Inventario.objects.get_or_create(
            sucursal=plan.sucursal,
            producto=plan.producto,
            defaults={'cantidad': plan.cantidad}
        )
        if not creado:
            inventario.cantidad += plan.cantidad
            inventario.save()
            
    return redirect('plan_inventario')

def obtener_alertas_stock(sucursal=None):
    if sucursal:
        # Si quieres alertas filtradas por sucursal específica
        return Inventario.objects.filter(sucursal=sucursal, cantidad__lte=F('producto__stock_minimo'))
    # O a nivel general de productos/insumos
    return ProductoInsumo.objects.filter(stock__lte=F('stock_minimo'))

@gestion_requerida
@require_POST
def InventarioDelete(request, pk):
    inventario = get_object_or_404(Inventario, pk=pk)
    sucursal_id = inventario.sucursal.id
    if request.method == 'POST':
        inventario.delete()
        return redirect('inventario_list_sucursal', sucursal_id=sucursal_id)
    
    context = {
        'inventario': inventario,
        'alertas_stock': obtener_alertas_stock()
    }
    return render(request, 'agenda/gestion/inventarioDelete.html', context)
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

# --- Módulo de RRHH (Personal y Usuarios) ---
@gestion_requerida
def personalList(request):
    empleados = Trabajador.objects.all()
    context = {
        'empleados': empleados,
        'alertas_stock': obtener_alertas_stock()
    }
    return render(request, 'agenda/gestion/personalList.html', context)
@gestion_requerida
def personalDetail(request, pk):
    trabajador = get_object_or_404(Trabajador, pk=pk)
    context = {
        'trabajador': trabajador,
        'alertas_stock': obtener_alertas_stock()
    }
    return render(request, 'agenda/gestion/personalDetail.html', context)

@gestion_requerida
@gestion_requerida
def personal_detail(request, pk):
    trabajador = get_object_or_404(Trabajador, pk=pk)
    return render(request, 'agenda/gestion/personalDetail.html', {
        "seccion": "personal",
        'trabajador': trabajador,
    })


@gestion_requerida
def personalCreate(request):
    if request.method == 'POST':
        form = PersonalForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                trabajador = form.save()
                
                raw_password = form.cleaned_data.get('password_temporal')
                if not raw_password:
                    raw_password = "StetikGlow2026*"
                
                username_base = f"{trabajador.nombre.lower()}.{trabajador.apellido.lower()}".replace(" ", "")
                username = username_base
                counter = 1
                while Usuario.objects.filter(username=username).exists():
                    username = f"{username_base}{counter}"
                    counter += 1

                Usuario.objects.create(
                    username=username,
                    password_hash=make_password(raw_password),
                    activo=True,
                    trabajador=trabajador
                )

            return redirect('personal_list')
    else:
        form = PersonalForm()
    
    context = {
        'form': form, 
        'accion': 'Crear',
        'alertas_stock': obtener_alertas_stock()
    }
    return render(request, 'agenda/gestion/personalForm.html', context)


@gestion_requerida
def personalUpdate(request, pk):
    trabajador = get_object_or_404(Trabajador, pk=pk)
    if request.method == 'POST':
        form = PersonalForm(request.POST, instance=trabajador)
        if form.is_valid():
            form.save()
            return redirect('personal_detail', pk=trabajador.pk)
    else:
        form = PersonalForm(instance=trabajador)
    
    context = {
        'form': form, 
        'accion': 'Editar',
        'alertas_stock': obtener_alertas_stock()
    }
    return render(request, 'agenda/gestion/personalForm.html', context)


@gestion_requerida
def personalDelete(request, pk):
    trabajador = get_object_or_404(Trabajador, pk=pk)
    trabajador.delete()
    return redirect('personal_list')