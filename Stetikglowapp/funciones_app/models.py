from django.db import models


class Sucursal(models.Model):
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=200)
    telefono = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = "funciones_app_sucursal"
        verbose_name = "Sucursal"
        verbose_name_plural = "Sucursales"


class Cliente(models.Model):
    rut = models.CharField(max_length=12, unique=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100, blank=True, null=True)
    correo = models.EmailField(max_length=150, unique=True, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido or ''} ({self.rut})"

    class Meta:
        db_table = "funciones_app_cliente"
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"


class Trabajador(models.Model):
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.CASCADE,
        db_column="sucursal_id",
        related_name="trabajadores",
    )
    rut = models.CharField(max_length=12, unique=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    correo = models.EmailField(max_length=150, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    especialidad = models.CharField(max_length=100, blank=True, null=True)
    tipo_contrato = models.CharField(max_length=50, blank=True, null=True)
    modalidad_pago = models.CharField(max_length=50, blank=True, null=True)
    porcentaje_comision = models.PositiveIntegerField(default=0)
    rol = models.CharField(max_length=30, default="Empleado")

    def __str__(self):
        return f"{self.nombre} {self.apellido} - {self.rol}"

    class Meta:
        db_table = "funciones_app_trabajador"
        verbose_name = "Trabajador"
        verbose_name_plural = "Trabajadores"


class Usuario(models.Model):
    trabajador = models.OneToOneField(
        Trabajador,
        on_delete=models.CASCADE,
        db_column="trabajador_id",
        related_name="usuario",
    )
    username = models.CharField(max_length=50, unique=True)
    password_hash = models.CharField(max_length=255)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.username

    class Meta:
        db_table = "funciones_app_usuario"


class Asistencia(models.Model):
    trabajador = models.ForeignKey(
        Trabajador,
        on_delete=models.CASCADE,
        db_column="trabajador_id",
        related_name="asistencias",
    )
    fecha = models.DateField()
    hora_entrada = models.TimeField()
    hora_salida = models.TimeField(blank=True, null=True)

    def __str__(self):
        return f"Asistencia: {self.trabajador.nombre} ({self.fecha})"

    class Meta:
        db_table = "funciones_app_asistencia"


class Turno(models.Model):
    trabajador = models.ForeignKey(
        Trabajador,
        on_delete=models.CASCADE,
        db_column="trabajador_id",
        related_name="turnos",
    )
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    def __str__(self):
        return f"Turno de {self.trabajador.nombre} - {self.fecha}"

    class Meta:
        db_table = "funciones_app_turno"


class ProductoInsumo(models.Model):
    nombre = models.CharField(max_length=100)
    categoria = models.CharField(max_length=50, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)

    stock_minimo = models.PositiveIntegerField(default=5)
    es_insumo = models.BooleanField(default=False)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = "funciones_app_productoinsumo"
        verbose_name = "Producto o Insumo"
        verbose_name_plural = "Productos e Insumos"


class Inventario(models.Model):
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.CASCADE,
        db_column="sucursal_id",
        related_name="inventarios",
    )
    producto = models.ForeignKey(
        ProductoInsumo,
        on_delete=models.CASCADE,
        db_column="producto_id",
        related_name="stocks",
    )
    cantidad = models.PositiveIntegerField(default=0)
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.producto.nombre} ({self.cantidad} un.)"

    class Meta:
        db_table = "funciones_app_inventario"


class Proveedor(models.Model):
    rut = models.CharField(max_length=12, unique=True)

    contacto = models.CharField(max_length=100, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.razon_social

    class Meta:
        db_table = "funciones_app_proveedor"


class FacturaCompra(models.Model):
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.PROTECT,
        db_column="proveedor_id",
        related_name="facturas",
    )
    fecha = models.DateTimeField(auto_now_add=True)
    total_factura = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"Compra #{self.id} - {self.proveedor.razon_social}"

    class Meta:
        db_table = "funciones_app_facturacompra"


class DetalleCompra(models.Model):
    compra = models.ForeignKey(
        FacturaCompra,
        on_delete=models.CASCADE,
        db_column="compra_id",
        related_name="detalles",
    )
    producto = models.ForeignKey(
        ProductoInsumo,
        on_delete=models.PROTECT,
        db_column="producto_id",
        related_name="compras_detalle",
    )
    cantidad = models.PositiveIntegerField()
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = "funciones_app_detallecompra"


class Servicio(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    precio_base = models.DecimalField(max_digits=10, decimal_places=2)
    duracion_minutos = models.PositiveIntegerField(help_text="Duración en minutos")
    categoria_cliente = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = "funciones_app_servicio"


class Reserva(models.Model):
    ESTADOS = [
        ("Pendiente", "Pendiente"),
        ("Confirmada", "Confirmada"),
        ("Completada", "Completada"),
        ("Cancelada", "Cancelada"),
    ]
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        db_column="cliente_id",
        related_name="reservas",
    )
    trabajador = models.ForeignKey(
        Trabajador,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="trabajador_id",
        related_name="reservas",
    )
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.CASCADE,
        db_column="sucursal_id",
        related_name="reservas",
    )
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    estado = models.CharField(max_length=30, choices=ESTADOS, default="Pendiente")
    origen = models.CharField(max_length=30, blank=True, null=True)

    def __str__(self):
        return f"Reserva #{self.id} - {self.cliente.nombre}"

    class Meta:
        db_table = "funciones_app_reserva"


class DetalleReserva(models.Model):
    reserva = models.ForeignKey(
        Reserva,
        on_delete=models.CASCADE,
        db_column="reserva_id",
        related_name="detalles_reserva",
    )
    servicio = models.ForeignKey(
        Servicio,
        on_delete=models.PROTECT,
        db_column="servicio_id",
        related_name="reservas_incluidas",
    )
    precio_reservado = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "funciones_app_detallereserva"


class Atencion(models.Model):
    reserva = models.OneToOneField(
        Reserva,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="reserva_id",
        related_name="atencion",
    )
    fecha = models.DateTimeField(auto_now_add=True)
    observacion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Atención #{self.id}"

    class Meta:
        db_table = "funciones_app_atencion"


class DetalleAtencion(models.Model):
    atencion = models.ForeignKey(
        Atencion,
        on_delete=models.CASCADE,
        db_column="atencion_id",
        related_name="detalles",
    )
    servicio = models.ForeignKey(
        Servicio,
        on_delete=models.PROTECT,
        db_column="servicio_id",
        related_name="atenciones_detalle",
    )
    precio_aplicado = models.DecimalField(max_digits=10, decimal_places=2)
    complementario = models.BooleanField(default=False)

    class Meta:
        db_table = "funciones_app_detalleatencion"


class Venta(models.Model):
    ESTADOS_VENTA = [
        ("Emitida", "Emitida"),
        ("Pagada", "Pagada"),
        ("Anulada", "Anulada"),
    ]
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="cliente_id",
        related_name="ventas",
    )
    empleado = models.ForeignKey(
        Trabajador,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="empleado_id",
        related_name="ventas_realizadas",
    )
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.CASCADE,
        db_column="sucursal_id",
        related_name="ventas",
    )
    atencion = models.OneToOneField(
        Atencion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="atencion_id",
        related_name="venta",
    )
    fecha_hora = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    estado = models.CharField(
        max_length=30, choices=ESTADOS_VENTA, default="Emitida"
    )

    def __str__(self):
        return f"Venta #{self.id} - ${self.total}"

    class Meta:
        db_table = "funciones_app_venta"


class DetalleVenta(models.Model):
    venta = models.ForeignKey(
        Venta,
        on_delete=models.CASCADE,
        db_column="venta_id",
        related_name="detalles",
    )
    producto = models.ForeignKey(
        ProductoInsumo,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        db_column="producto_id",
        related_name="ventas_detalle",
    )
    servicio = models.ForeignKey(
        Servicio,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        db_column="servicio_id",
        related_name="ventas_detalle",
    )
    cantidad = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "funciones_app_detalleventa"


class Pago(models.Model):
    venta = models.ForeignKey(
        Venta,
        on_delete=models.CASCADE,
        db_column="venta_id",
        related_name="pagos",
    )
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    metodo = models.CharField(max_length=30)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pago ${self.monto} ({self.metodo})"

    class Meta:
        db_table = "funciones_app_pago"

class PlanInventario(models.Model):
    ESTADOS_PLAN = [
        ("Processing", "Processing"),
        ("Completado", "Completado"),
    ]
    
    titulo = models.CharField(max_length=150)
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.CASCADE,
        db_column="sucursal_id",
        related_name="planes_inventario"
    )
    producto = models.ForeignKey(
        ProductoInsumo,
        on_delete=models.CASCADE,
        db_column="producto_id",
        related_name="planes_inventario"
    )
    cantidad = models.PositiveIntegerField(default=1)
    estado = models.CharField(max_length=30, choices=ESTADOS_PLAN, default="Processing")
    fecha_solicitud = models.DateField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.titulo} - {self.sucursal.nombre} ({self.estado})"

    class Meta:
        db_table = "funciones_app_planinventario"
        verbose_name = "Plan de Inventario"
        verbose_name_plural = "Planes de Inventario"