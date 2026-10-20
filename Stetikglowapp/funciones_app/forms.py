from django import forms
from .models import Atencion, Servicio, Venta, Pago

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
        fields = ["sucursal", "trabajador", "cliente", "observacion"]
        widgets = {
            "sucursal": forms.Select(attrs={"class": "form-control"}),
            "trabajador": forms.Select(attrs={"class": "form-control"}),
            "cliente": forms.Select(attrs={"class": "form-control"}),
            "observacion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
class InventarioForm(forms.ModelForm):
    class Meta:
        model = Inventario
        fields = ['sucursal', 'producto', 'cantidad']
        widgets = {
            'sucursal': forms.Select(attrs={'class': 'form-control'}),
            'producto': forms.Select(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }
