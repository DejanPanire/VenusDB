"""Formularios de los módulos de inventario y ventas (traídos de Stetikglowapp)."""
from django import forms
import secrets
import string
from funciones_app.models import *

from funciones_app.models import *


class EstiloVenus:
    """Agrega la clase 'entrada' de venus.css a todos los campos."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            if not isinstance(campo.widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
                campo.widget.attrs.setdefault("class", "entrada")


class InventarioForm(forms.Form):
    nombre = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del insumo (ej. Guantes de Nitrilo)'})
    )
    marca = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Marca del producto'})
    )
    categoria = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Categoría (ej. Higiene, Capilar, Facial)'})
    )
    descripcion = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Descripción u observaciones'})
    )
    valor_de_compra = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'})
    )
    unidad_medida = forms.ChoiceField(
        choices=[
            ('Unidades', 'Unidades'),
            ('Litros', 'Litros'),
            ('Mililitros', 'Mililitros'),
            ('Gramos', 'Gramos'),
            ('Kilos', 'Kilos'),
            ('Cajas', 'Cajas'),
            ('Potes', 'Potes'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    stock_minimo = forms.IntegerField(
        initial=5,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0'})
    )
    sucursal = forms.ModelChoiceField(
        queryset=Sucursal.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    cantidad = forms.IntegerField(
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0'})
    )

class PlanInventarioForm(EstiloVenus, forms.ModelForm):
    class Meta:
        model = PlanInventario
        fields = ["titulo", "producto", "cantidad", "sucursal"]
        labels = {"titulo": "Título de la solicitud", "producto": "Producto / insumo", "sucursal": "Local"}
        widgets = {"titulo": forms.TextInput(attrs={"placeholder": "Ej. [Urgente] Stock de esmaltes"})}

    def __init__(self, *args, sucursales=None, **kwargs):
        super().__init__(*args, **kwargs)
        if sucursales is not None:
            self.fields["sucursal"].queryset = sucursales
        self.fields["producto"].queryset = ProductoInsumo.objects.order_by("nombre")


class ServicioForm(EstiloVenus, forms.ModelForm):
    class Meta:
        model = Servicio
        fields = ["nombre", "categoria_cliente", "precio_base", "duracion_minutos", "descripcion"]
        labels = {"categoria_cliente": "Categoría", "precio_base": "Precio base ($)",
                  "duracion_minutos": "Duración (minutos)", "descripcion": "Descripción / nota"}
        widgets = {"descripcion": forms.Textarea(attrs={"rows": 2}),
                   "categoria_cliente": forms.TextInput(attrs={"list": "categorias"})}


METODOS_PAGO = [("Efectivo", "Efectivo"), ("Débito", "Débito"), ("Crédito", "Crédito"),
                ("Transferencia", "Transferencia")]


class AtencionForm(EstiloVenus, forms.ModelForm):
    """Registro de la atención y su cobro (RegistrarAtencion de Stetikglowapp)."""
    servicios = forms.ModelMultipleChoiceField(label="Servicios realizados", queryset=Servicio.objects.none(),
                                               widget=forms.SelectMultiple(attrs={"size": 8}),
                                               help_text="Mantén Ctrl (o Cmd) para elegir varios.")
    metodo_pago = forms.ChoiceField(label="Método de pago", choices=METODOS_PAGO)

    class Meta:
        model = Atencion
        fields = ["reserva", "observacion"]
        labels = {"reserva": "Reserva", "observacion": "Observación"}
        widgets = {"observacion": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, reservas=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["reserva"].queryset = reservas if reservas is not None else Reserva.objects.none()
        self.fields["reserva"].required = True
        self.fields["reserva"].empty_label = "Selecciona una reserva"
        self.fields["reserva"].label_from_instance = (
            lambda r: f"{r.fecha:%d/%m} {r.hora_inicio:%H:%M} · {r.cliente.nombre} {r.cliente.apellido or ''} · "
                      f"{r.trabajador.nombre if r.trabajador else 'Sin asignar'} ({r.estado})")
        self.fields["servicios"].queryset = Servicio.objects.order_by("categoria_cliente", "id")
        self.fields["servicios"].label_from_instance = (
            lambda s: f"{s.nombre} ({s.categoria_cliente}) · ${int(s.precio_base):,}".replace(",", "."))

def generar_contrasena_aleatoria(length=8):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))


class PersonalForm(forms.ModelForm):

    password_temporal = forms.CharField(
        required=False,
        initial=generar_contrasena_aleatoria,
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        label="Contraseña de Acceso (Generada Automáticamente)"
    )

    class Meta:
        model = Trabajador
        fields = [
            'sucursal', 
            'rut', 
            'nombre', 
            'apellido', 
            'correo', 
            'telefono', 
            'especialidad', 
            'tipo_contrato', 
            'modalidad_pago', 
            'porcentaje_comision', 
            'rol'
        ]
        widgets = {
            'sucursal': forms.Select(attrs={'class': 'form-select'}),
            'rut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 12.345.678-9'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@estudio.com'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+569...'}),
            'especialidad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Cosmetología'}),
            'tipo_contrato': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Indefinido'}),
            'modalidad_pago': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Comisión / Sueldo'}),
            'porcentaje_comision': forms.NumberInput(attrs={'class': 'form-control'}),
            'rol': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Administrador / Empleado'}),
        }