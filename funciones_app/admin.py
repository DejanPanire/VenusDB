"""Admin de los modelos."""
from django import forms
from django.contrib import admin
from django.contrib.auth.hashers import make_password

from .models import (
    Asistencia, Atencion, Cliente, DetalleAtencion, DetalleReserva, DetalleVenta, Inventario, Pago,
    PlanInventario, ProductoInsumo, Reserva, Servicio, Sucursal, Trabajador, Turno, Usuario, Venta,
)


@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ("nombre", "direccion", "telefono")


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("rut", "nombre", "apellido", "correo", "telefono")
    search_fields = ("rut", "nombre", "apellido", "correo")


@admin.register(Trabajador)
class TrabajadorAdmin(admin.ModelAdmin):
    list_display = ("nombre", "apellido", "rol", "especialidad", "sucursal", "porcentaje_comision")
    list_filter = ("sucursal", "rol")
    search_fields = ("nombre", "apellido", "rut")


class UsuarioForm(forms.ModelForm):
    """La contraseña se guarda cifrada."""
    nueva_clave = forms.CharField(
        label="Contraseña", required=False, widget=forms.PasswordInput(render_value=False),
        help_text="Escríbela solo para crearla o cambiarla. Se guarda cifrada.",
    )

    class Meta:
        model = Usuario
        fields = ("trabajador", "username", "activo")

    def clean(self):
        datos = super().clean()
        if not self.instance.pk and not datos.get("nueva_clave"):
            self.add_error("nueva_clave", "Un usuario nuevo necesita contraseña.")
        return datos

    def save(self, commit=True):
        usuario = super().save(commit=False)
        if self.cleaned_data.get("nueva_clave"):
            usuario.password_hash = make_password(self.cleaned_data["nueva_clave"])
        if commit:
            usuario.save()
        return usuario


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    form = UsuarioForm
    list_display = ("username", "trabajador", "activo")
    list_filter = ("activo",)


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ("nombre", "categoria_cliente", "duracion_minutos", "precio_base")


class DetalleReservaInline(admin.TabularInline):
    model = DetalleReserva
    extra = 0


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "trabajador", "sucursal", "fecha", "hora_inicio", "hora_fin", "estado", "origen")
    list_filter = ("estado", "sucursal", "origen")
    date_hierarchy = "fecha"
    inlines = [DetalleReservaInline]


@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    list_display = ("trabajador", "fecha", "hora_inicio", "hora_fin")
    list_filter = ("trabajador__sucursal", "trabajador")
    date_hierarchy = "fecha"


@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ("trabajador", "fecha", "hora_entrada", "hora_salida")
    date_hierarchy = "fecha"


class DetalleAtencionInline(admin.TabularInline):
    model = DetalleAtencion
    extra = 0


@admin.register(Atencion)
class AtencionAdmin(admin.ModelAdmin):
    list_display = ("id", "reserva", "fecha")
    inlines = [DetalleAtencionInline]


class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 0


class PagoInline(admin.TabularInline):
    model = Pago
    extra = 0


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "empleado", "sucursal", "total", "estado", "fecha_hora")
    list_filter = ("estado", "sucursal")
    inlines = [DetalleVentaInline, PagoInline]


# Proveedor no se registra: su __str__ usa razon_social, que no existe en el modelo.
admin.site.register(ProductoInsumo)
admin.site.register(Inventario)
admin.site.register(PlanInventario)
