from django import forms
from .models import *

class InventarioForm(forms.Form):

    nombre = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del insumo (ej. Guantes de Nitrilo)'})
    )
    categoria = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Categoría (ej. Higiene, Capilar, Facial)'})
    )
    descripcion = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Descripción u observaciones del insumo'})
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
    """Formulario para la gestión de servicios estéticos."""
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
    """Formulario para el registro de la atención operativa."""
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