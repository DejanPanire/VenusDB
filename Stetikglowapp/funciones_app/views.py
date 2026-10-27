from django.db import transaction
from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from .forms import *



def InventarioList(request, sucursal_id=None):
    sucursales = Sucursal.objects.all()
    if not sucursal_id and sucursales.exists():
        sucursal_actual = sucursales.first()
    elif sucursal_id:
        sucursal_actual = get_object_or_404(Sucursal, id=sucursal_id)
    else:
        sucursal_actual = None

    inventarios = Inventario.objects.filter(sucursal=sucursal_actual) if sucursal_actual else []

    context = {
        'sucursales': sucursales,
        'sucursal_actual': sucursal_actual,
        'inventarios': inventarios,
    }
    return render(request, 'inventariolista.html', context)

def InventarioCreate(request):
    
    
    if request.method == 'POST':
        form = InventarioForm(request.POST)
        if form.is_valid():
            inv = form.save()
            return redirect('inventario_list_sucursal', sucursal_id=inv.sucursal.id)
    else:
        form = InventarioForm()
    return render(request, 'inventarioFrom.html', {'form': form, 'titulo': 'Agregar Insumo'})

def InventarioUpdate(request, pk):
    
    
    inventario = get_object_or_404(Inventario, pk=pk)
    if request.method == 'POST':
        form = InventarioForm(request.POST, instance=inventario)
        if form.is_valid():
            inv = form.save()
            return redirect('inventario_list_sucursal', sucursal_id=inv.sucursal.id)
    else:
        form = InventarioForm(instance=inventario)
    return render(request, 'inventarioFrom.html', {'form': form, 'titulo': 'Editar Insumo'})

def InventarioDelete(request, pk):
    
    
    inventario = get_object_or_404(Inventario, pk=pk)
    sucursal_id = inventario.sucursal.id
    if request.method == 'POST':
        inventario.delete()
        return redirect('inventario_list_sucursal', sucursal_id=sucursal_id)
    return render(request, 'inventarioDelete.html', {'inventario': inventario})

def PlanInventarioView(request):
    sucursales = Sucursal.objects.all()
    planes_en_proceso = PlanInventario.objects.filter(estado='Processing')
    planes_completados = PlanInventario.objects.filter(estado='Completado')
    
    context = {
        'sucursales': sucursales,
        'planes_en_proceso': planes_en_proceso,
        'planes_completados': planes_completados,
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
            print("Errores en el formulario:", form.errors)
    else:
        form = PlanInventarioForm()
    
    return render(request, 'planinventarioform.html', {'form': form})

def PlanInventarioUpdate(request, pk):
    
    
    sucursales = Sucursal.objects.all()
    if request.method == 'POST':

        return redirect('plan_inventario')
    
    context = {
        'sucursales': sucursales,
        'plan_id': pk,
        'titulo': f'Editar Plan de Inventario #{pk}'
    }
    return render(request, 'planinventarioform.html', context)

def PlanInventarioRecibir(request, pk):
    with transaction.atomic():
        plan = get_object_or_404(PlanInventario, pk=pk)
        plan.estado = 'Completado'
        plan.save()
        
        inventario, creado = Inventario.objects.get_or_create(
            sucursal=plan.sucursal,
            producto=plan.producto,
            defaults={'cantidad': plan.cantidad}
        )
        if not creado:
            inventario.cantidad += plan.cantidad
            inventario.save()
            
    return redirect('plan_inventario')

# --- Módulo de Servicios y Ventas ---

def ServicioList(request):
    """Muestra el catálogo de servicios estéticos disponibles."""
    servicios = Servicio.objects.all()
    return render(request, 'servicios_lista.html', {'servicios': servicios})

def RegistrarAtencion(request):
    """Permite registrar una atención operativa y procesar la venta/pago de forma transaccional."""
    if request.method == 'POST':
        form = AtencionForm(request.POST)
        servicios_ids = request.POST.getlist('servicios')  # Lista de servicios seleccionados
        metodo_pago = request.POST.get('metodo_pago', 'Efectivo')

        if form.is_valid() and servicios_ids:
            with transaction.atomic():
                # 1. Guardar la cabecera de la atención
                atencion = form.save(commit=False)
                atencion.save()

                # Actualizar el estado de la reserva vinculada a 'Completada'
                if atencion.reserva:
                    atencion.reserva.estado = 'Completada'
                    atencion.reserva.save()

                total_venta = 0
                # 2. Registrar cada servicio seleccionado aplicando el precio base
                for s_id in servicios_ids:
                    servicio = Servicio.objects.get(id=s_id)
                    precio = servicio.precio_base
                    DetalleAtencion.objects.create(
                        atencion=atencion,
                        servicio=servicio,
                        precio_aplicado=precio
                    )
                    total_venta += precio

                # 3. Extraer cliente, empleado y sucursal desde la reserva de la atención
                cliente = atencion.reserva.cliente if atencion.reserva else None
                empleado = atencion.reserva.trabajador if atencion.reserva else None
                sucursal = atencion.reserva.sucursal if atencion.reserva else None

                # 4. Generar la Venta y el Pago asociado manteniendo la consistencia ACID
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

            return redirect('ventas_list')  # Redirige al historial de ventas
    else:
        form = AtencionForm()
        servicios = Servicio.objects.all()

    context = {
        'form': form,
        'servicios': servicios,
    }
    return render(request, 'registrar_atencion.html', context)

def VentaList(request):
    """Muestra el historial general de ventas realizadas."""
    ventas = Venta.objects.all().order_by('-fecha_hora')
    return context if False else render(request, 'ventas_lista.html', {'ventas': ventas})
