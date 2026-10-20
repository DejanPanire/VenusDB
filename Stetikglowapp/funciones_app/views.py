from django.db import transaction
from django.shortcuts import render, get_object_or_404, redirect
from .models import Sucursal, Inventario, Servicio, Atencion, DetalleAtencion, Venta, Pago
from .forms import InventarioForm, AtencionForm

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
    return render(request, 'inventarioFrom.html', {'form': form, 'titulo': 'Agregar Stock'})

def InventarioUpdate(request, pk):
    inventario = get_object_or_404(Inventario, pk=pk)
    if request.method == 'POST':
        form = InventarioForm(request.POST, instance=inventario)
        if form.is_valid():
            inv = form.save()
            return redirect('inventario_list_sucursal', sucursal_id=inv.sucursal.id)
    else:
        form = InventarioForm(instance=inventario)
    return render(request, 'inventarioFrom.html', {'form': form, 'titulo': 'Editar Stock'})

def InventarioDelete(request, pk):
    inventario = get_object_or_404(Inventario, pk=pk)
    sucursal_id = inventario.sucursal.id
    if request.method == 'POST':
        inventario.delete()
        return redirect('inventario_list_sucursal', sucursal_id=sucursal_id)
    return render(request, 'inventarioDelete.html', {'inventario': inventario})

def PlanInventarioView(request):
    sucursales = Sucursal.objects.all()
    context = {
        'sucursales': sucursales,
    }
    return render(request, 'planinventario.html', context)

def PlanInventarioCreate(request):
    sucursales = Sucursal.objects.all()
    if request.method == 'POST':
        return redirect('plan_inventario')
    return render(request, 'planinventarioform.html', {'sucursales': sucursales, 'titulo': 'Crear Nuevo Plan de Inventario'})
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
                atencion.estado = 'Completada'
                atencion.save()

                total_venta = 0
                # 2. Registrar cada servicio seleccionado aplicando el precio base
                for s_id in servicios_ids:
                    servicio = Servicio.objects.get(id=s_id)
                    precio = servicio.precio_base
                    DetalleAtencion.objects.create(
                        atencion=atencion,
                        servicio=servicio,
                        precio_aplicado=precio)
                    total_venta += precio

                # 3. Generar la Venta y el Pago asociado (Garantiza consistencia ACID en MySQL)
                venta = Venta.objects.create(
                    cliente=atencion.cliente,
                    empleado=atencion.trabajador,
                    sucursal=atencion.sucursal,
                    atencion=atencion,
                    total=total_venta,
                    estado='Pagada',)
                Pago.objects.create(
                    venta=venta,
                    monto=total_venta,
                    metodo=metodo_pago)

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
