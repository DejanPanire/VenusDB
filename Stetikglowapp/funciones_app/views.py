from django.db import transaction
from django.db.models import F
from django.contrib.auth.hashers import make_password
from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from .forms import *

def obtener_alertas_stock():
    return ProductoInsumo.objects.filter(stock__lte=F('stock_minimo'))

def InventarioList(request, sucursal_id=None):
    sucursales = Sucursal.objects.all()
    if not sucursal_id and sucursales.exists():
        sucursal_actual = sucursales.first()
    elif sucursal_id:
        sucursal_actual = get_object_or_404(Sucursal, id=sucursal_id)
    else:
        sucursal_actual = None

    inventarios = Inventario.objects.filter(sucursal=sucursal_actual).select_related('producto') if sucursal_actual else []
    alertas_stock = obtener_alertas_stock()

    context = {
        'sucursales': sucursales,
        'sucursal_actual': sucursal_actual,
        'inventarios': inventarios,
        'alertas_stock': alertas_stock,
    }
    return render(request, 'inventariolista.html', context)
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
    
    context = {
        'form': form,
        'titulo': 'Agregar Insumo',
        'alertas_stock': obtener_alertas_stock()
    }
    return render(request, 'inventarioFrom.html', context)

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
    return render(request, 'inventarioFrom.html', context)

def producto_detail(request, pk):
    item = get_object_or_404(ProductoInsumo, pk=pk)
    
    inventarios = Inventario.objects.filter(producto=item)
    stock_disponible = sum(inv.cantidad for inv in inventarios) if inventarios.exists() else item.stock

    context = {
        'item': item,
        'stock_disponible': stock_disponible,
        'alertas_stock': obtener_alertas_stock()
    }
    return render(request, 'productoDetail.html', context)

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
    return render(request, 'inventarioDelete.html', context)

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
    return render(request, 'planinventario.html', context)

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
    return render(request, 'planinventarioform.html', context)

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
    return render(request, 'planinventarioform.html', context)

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

#----------------RRHH-----------------------------------------------------------------------
def personalList(request):
    empleados = Trabajador.objects.all()
    context = {
        'empleados': empleados,
        'alertas_stock': obtener_alertas_stock()
    }
    return render(request, 'personalList.html', context)

def personalDetail(request, pk):
    trabajador = get_object_or_404(Trabajador, pk=pk)
    context = {
        'trabajador': trabajador,
        'alertas_stock': obtener_alertas_stock()
    }
    return render(request, 'personalDetail.html', context)

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
    return render(request, 'personalForm.html', context)

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
    return render(request, 'personalForm.html', context)

def personalDelete(request, pk):
    trabajador = get_object_or_404(Trabajador, pk=pk)
    trabajador.delete()
    return redirect('personal_list')

# --- Módulo de Servicios y Ventas ---

def ServicioList(request):
    servicios = Servicio.objects.all()
    context = {
        'servicios': servicios,
        'alertas_stock': obtener_alertas_stock()
    }
    return render(request, 'servicios_lista.html', context)

def RegistrarAtencion(request):
    if request.method == 'POST':
        form = AtencionForm(request.POST)
        servicios_ids = request.POST.getlist('servicios') 
        metodo_pago = request.POST.get('metodo_pago', 'Efectivo')

        if form.is_valid() and servicios_ids:
            with transaction.atomic():
                atencion = form.save(commit=False)
                atencion.save()

                if atencion.reserva:
                    atencion.reserva.estado = 'Completada'
                    atencion.reserva.save()

                total_venta = 0
                for s_id in servicios_ids:
                    servicio = Servicio.objects.get(id=s_id)
                    precio = servicio.precio_base
                    DetalleAtencion.objects.create(
                        atencion=atencion,
                        servicio=servicio,
                        precio_aplicado=precio
                    )
                    total_venta += precio

                cliente = atencion.reserva.cliente if atencion.reserva else None
                empleado = atencion.reserva.trabajador if atencion.reserva else None
                sucursal = atencion.reserva.sucursal if atencion.reserva else None

                venta = Venta.objects.create(
                    cliente=cliente,
                    empleado=empleado,
                    sucursal=sucursal,
                    atencion=atencion,
                    total=total_venta,
                    estado='Pagada',
                )
                Pago.objects.create(
                    venta=venta,
                    monto=total_venta,
                    metodo=metodo_pago
                )

            return redirect('ventas_list') 
    else:
        form = AtencionForm()
        servicios = Servicio.objects.all()

    context = {
        'form': form,
        'servicios': servicios,
        'alertas_stock': obtener_alertas_stock()
    }
    return render(request, 'registrar_atencion.html', context)

def VentaList(request):
    ventas = Venta.objects.all().order_by('-fecha_hora')
    context = {
        'ventas': ventas,
        'alertas_stock': obtener_alertas_stock()
    }
    return render(request, 'ventas_lista.html', context)