from django import forms
from .models import *
import secrets
import string

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

class PlanInventarioForm(forms.ModelForm):
    class Meta:
        model = PlanInventario
        fields = ['titulo', 'cantidad', 'producto', 'sucursal']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. [Urgente] Stock de Esmaltes'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Cantidad total'}),
            'producto': forms.Select(attrs={'class': 'form-select'}),
            'sucursal': forms.Select(attrs={'class': 'form-select'}),
        }
          
class ServicioForm(forms.ModelForm):
    class Meta:
        model = Servicio
        fields = ["nombre", "precio_base", "duracion_minutos", "descripcion"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "precio_base": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "duracion_minutos": forms.NumberInput(attrs={"class": "form-control", "min": "5"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

class AtencionForm(forms.ModelForm):
    metodo_pago = forms.ChoiceField(
        choices=[
            ("Efectivo", "Efectivo"),
            ("Tarjeta", "Tarjeta"),
            ("Transferencia", "Transferencia / Otros"),
        ],
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    class Meta:
        model = Atencion
        fields = ["reserva", "observacion"]
        widgets = {
            "reserva": forms.Select(attrs={"class": "form-control"}),
            "observacion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

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
