from django import forms
from .models import Inventario, Atencion

class InventarioForm(forms.ModelForm):
    class Meta:
        model = Inventario
        fields = ['sucursal', 'producto', 'cantidad']
        widgets = {
            'sucursal': forms.Select(attrs={'class': 'form-control'}),
            'producto': forms.Select(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }
class AtencionForm(forms.ModelForm):
    """Formulario para registrar la atención operativa y seleccionar los campos base."""
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
