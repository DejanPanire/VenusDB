"""Formularios de los módulos de inventario y ventas (traídos de Stetikglowapp)."""
from django import forms

from funciones_app.models import Atencion, PlanInventario, ProductoInsumo, Reserva, Servicio, Sucursal


class EstiloVenus:
    """Agrega la clase 'entrada' de venus.css a todos los campos."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            if not isinstance(campo.widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
                campo.widget.attrs.setdefault("class", "entrada")


class InventarioForm(EstiloVenus, forms.Form):
    """Crea o edita el insumo (ProductoInsumo) y su stock en un local (Inventario)."""
    nombre = forms.CharField(label="Nombre del insumo", max_length=100,
                             widget=forms.TextInput(attrs={"placeholder": "Ej. Guantes de nitrilo"}))
    categoria = forms.CharField(label="Categoría", max_length=50, required=False,
                                widget=forms.TextInput(attrs={"placeholder": "Ej. Higiene, Uñas, Pestañas"}))
    descripcion = forms.CharField(label="Descripción", required=False,
                                  widget=forms.Textarea(attrs={"rows": 2, "placeholder": "Observaciones del insumo"}))
    sucursal = forms.ModelChoiceField(label="Local", queryset=Sucursal.objects.none(), empty_label=None)
    cantidad = forms.IntegerField(label="Stock actual", min_value=0, initial=1)
    stock_minimo = forms.IntegerField(label="Stock mínimo", min_value=0, initial=5)
    es_insumo = forms.BooleanField(label="Es insumo (no se vende)", required=False, initial=True)

    def __init__(self, *args, sucursales=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sucursal"].queryset = sucursales if sucursales is not None else Sucursal.objects.all()


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
