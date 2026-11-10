from datetime import time, timedelta
from decimal import Decimal

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from funciones_app.models import Atencion, Cliente, DetalleReserva, Reserva, Servicio, Sucursal, Trabajador, Turno, Usuario

from . import reglas
from .reglas import Estado


def crear_trabajador(sucursal, nombre, rol="Empleado", especialidad=None, username=None, rut=None, comision=30):
    t = Trabajador.objects.create(sucursal=sucursal, rut=rut or f"{nombre[:8]}-r", nombre=nombre, apellido="Test",
                                  especialidad=especialidad, rol=rol, porcentaje_comision=comision)
    if username:
        Usuario.objects.create(trabajador=t, username=username, password_hash=make_password("x"))
    return t


class Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.local1 = Sucursal.objects.create(nombre="Local 1", direccion="Calle 1")
        cls.local2 = Sucursal.objects.create(nombre="Local 2", direccion="Calle 2")
        cls.s_mani = Servicio.objects.create(nombre="Manicure", categoria_cliente="Uñas",
                                             duracion_minutos=60, precio_base=Decimal(15000))
        cls.s_dep = Servicio.objects.create(nombre="Depilación", categoria_cliente="Depilación",
                                            duracion_minutos=45, precio_base=Decimal(20000))
        cls.maria = crear_trabajador(cls.local1, "María", especialidad="Uñas", username="maria@x.cl", comision=40)
        cls.otra = crear_trabajador(cls.local1, "Valentina", especialidad="Depilación", username="vale@x.cl")
        cls.admin_t = crear_trabajador(cls.local1, "Admin", rol="Administradora", username="admin@x.cl")
        cls.duena = crear_trabajador(cls.local1, "Antonia", rol="Propietaria", username="duena@x.cl")
        cls.cliente = Cliente.objects.create(rut="11.111.111-1", nombre="Ana", apellido="Paz",
                                             telefono="+56911111111", correo="a@a.cl")

    def entrar(self, username):
        self.assertTrue(self.client.login(username=username, password="x"))

    def reserva(self, trabajador=None, estado=Estado.CONFIRMADA, dias=0, hora=time(11), servicio=None):
        return reglas.crear_reserva(cliente=self.cliente, sucursal=self.local1, trabajador=trabajador or self.maria,
                                    servicios=[servicio or self.s_mani],
                                    fecha=timezone.localdate() + timedelta(days=dias), hora_inicio=hora,
                                    origen=reglas.ORIGEN_SISTEMA, estado=estado)


class Login(Base):
    def test_login_con_tabla_usuario(self):
        r = self.client.post(reverse("login"), {"email": "maria@x.cl", "password": "x"})
        self.assertRedirects(r, reverse("mi_agenda"))
        self.assertTrue(User.objects.filter(username="maria@x.cl").exists())

    def test_clave_incorrecta(self):
        r = self.client.post(reverse("login"), {"email": "maria@x.cl", "password": "mala"})
        self.assertContains(r, "Credenciales incorrectas")

    def test_usuario_inactivo(self):
        Usuario.objects.filter(username="maria@x.cl").update(activo=False)
        r = self.client.post(reverse("login"), {"email": "maria@x.cl", "password": "x"})
        self.assertContains(r, "no está activa")

    def test_admin_va_al_calendario(self):
        r = self.client.post(reverse("login"), {"email": "admin@x.cl", "password": "x"})
        self.assertRedirects(r, reverse("calendario"))

    def test_desactivar_cuenta_saca_de_la_sesion(self):
        self.entrar("maria@x.cl")
        Usuario.objects.filter(username="maria@x.cl").update(activo=False)
        self.assertRedirects(self.client.get(reverse("mi_agenda")), reverse("login"))


class Roles(Base):
    def test_admin_solo_ve_su_local(self):
        self.entrar("admin@x.cl")
        r = self.client.get(reverse("calendario"))
        self.assertEqual(r.context["sucursal"], self.local1)
        self.client.post(reverse("cambiar_sucursal"), {"sucursal": self.local2.pk})
        self.assertEqual(self.client.get(reverse("calendario")).context["sucursal"], self.local1)

    def test_propietaria_cambia_de_local(self):
        self.entrar("duena@x.cl")
        self.client.post(reverse("cambiar_sucursal"), {"sucursal": self.local2.pk})
        self.assertEqual(self.client.get(reverse("calendario")).context["sucursal"], self.local2)

    def test_agenda_no_muestra_admin_ni_propietaria_como_columnas(self):
        self.entrar("admin@x.cl")
        cols = [c["trabajador"] for c in self.client.get(reverse("calendario")).context["columnas"]]
        self.assertEqual(cols, [self.maria, self.otra])

    def test_empleada_no_entra_a_administracion(self):
        self.entrar("maria@x.cl")
        self.assertRedirects(self.client.get(reverse("calendario")), reverse("mi_agenda"))
        self.assertRedirects(self.client.get(reverse("reservar")), reverse("mi_agenda"))

    def test_admin_no_entra_a_zona_empleado(self):
        self.entrar("admin@x.cl")
        for nombre in ("mi_agenda", "perfil", "reservas_asignadas"):
            self.assertRedirects(self.client.get(reverse(nombre)), reverse("calendario"), msg_prefix=nombre)


class Reservas(Base):
    def test_crea_reserva_con_detalle_y_hora_fin(self):
        r = self.reserva(servicio=self.s_dep, trabajador=self.otra, hora=time(10))
        self.assertEqual(r.hora_fin, time(10, 45))
        d = DetalleReserva.objects.get(reserva=r)
        self.assertEqual((d.servicio, d.precio_reservado), (self.s_dep, Decimal(20000)))

    def test_conflicto_de_horario(self):
        from django.core.exceptions import ValidationError
        self.reserva(hora=time(11))
        with self.assertRaises(ValidationError):
            self.reserva(hora=time(11, 30))

    def test_turnos_bloquean_colacion(self):
        hoy = timezone.localdate() + timedelta(days=1)
        Turno.objects.create(trabajador=self.maria, fecha=hoy, hora_inicio=time(10), hora_fin=time(13))
        Turno.objects.create(trabajador=self.maria, fecha=hoy, hora_inicio=time(14), hora_fin=time(20))
        libres = reglas.horarios_disponibles(self.maria, hoy, 60)
        self.assertIn("12:00", libres)
        self.assertNotIn("12:30", libres)
        self.assertNotIn("13:00", libres)
        self.assertIn("14:00", libres)

    def test_formulario_publico_crea_cliente_y_reserva(self):
        manana = (timezone.localdate() + timedelta(days=1)).isoformat()
        r = self.client.post(reverse("reservar"), {
            "rut": "12.345.678-5", "nombre": "Lu", "apellido": "Rey", "telefono": "+56922222222",
            "email": "lu@x.cl", "sucursal": self.local1.pk, "servicio": self.s_mani.pk,
            "trabajadora": self.maria.pk, "fecha": manana, "hora": "15:00"})
        self.assertContains(r, "ha sido registrada")
        reserva = Reserva.objects.get(cliente__correo="lu@x.cl")
        self.assertEqual((reserva.estado, reserva.origen, reserva.hora_fin), ("Pendiente", "Web/QR", time(16)))

    def test_completar_registra_atencion(self):
        self.entrar("admin@x.cl")
        r = self.reserva()
        self.client.post(reverse("cambiar_estado", args=[r.pk]), {"accion": "completar"})
        r.refresh_from_db()
        self.assertEqual(r.estado, "Completada")
        atencion = Atencion.objects.get(reserva=r)
        self.assertEqual(atencion.detalles.get().precio_aplicado, Decimal(15000))

    def test_api_filtra_por_especialidad(self):
        r = self.client.get(reverse("api_trabajadoras"), {"sucursal": self.local1.pk, "servicio": self.s_dep.pk})
        self.assertEqual([t["id"] for t in r.json()["trabajadoras"]], [self.otra.pk])


class Empleada(Base):
    def setUp(self):
        self.entrar("maria@x.cl")

    def test_agenda_solo_muestra_sus_reservas(self):
        self.reserva()
        self.reserva(trabajador=self.otra, hora=time(15), servicio=self.s_dep)
        self.assertEqual(self.client.get(reverse("mi_agenda")).context["n_reservas"], 1)

    def test_gestiona_sus_reservas(self):
        r = self.reserva(estado=Estado.PENDIENTE)
        self.client.post(reverse("cambiar_estado_reserva", args=[r.pk]), {"accion": "confirmar"})
        r.refresh_from_db()
        self.assertEqual(r.estado, "Confirmada")

    def test_no_toca_reservas_de_otra(self):
        r = self.reserva(trabajador=self.otra, estado=Estado.PENDIENTE, servicio=self.s_dep)
        resp = self.client.post(reverse("cambiar_estado_reserva", args=[r.pk]), {"accion": "cancelar"})
        self.assertEqual(resp.status_code, 404)

    def test_no_puede_completar(self):
        r = self.reserva()
        self.client.post(reverse("cambiar_estado_reserva", args=[r.pk]), {"accion": "completar"})
        r.refresh_from_db()
        self.assertEqual(r.estado, "Confirmada")

    def test_perfil(self):
        r = self.client.get(reverse("perfil"))
        for txt in ("María", "Local 1", "Uñas", "40%"):
            self.assertContains(r, txt)

    def test_paginas_cargan(self):
        self.reserva()
        for nombre in ("mi_agenda", "reservas_asignadas", "perfil"):
            self.assertEqual(self.client.get(reverse(nombre)).status_code, 200, nombre)


class PaginasAdministracion(Base):
    def test_calendario_en_todas_las_pestanas(self):
        self.entrar("admin@x.cl")
        r = self.reserva(estado=Estado.PENDIENTE)
        for tab in ("agenda", "listado", "resumen", "sala"):
            resp = self.client.get(reverse("calendario"), {"tab": tab, "reserva": r.pk, "trabajador": self.maria.pk})
            self.assertEqual(resp.status_code, 200, tab)
            self.assertContains(resp, "Ana Paz")


class InventarioYVentas(Base):
    def setUp(self):
        self.entrar("admin@x.cl")

    def test_crear_insumo(self):
        from funciones_app.models import Inventario
        self.client.post(reverse("inventario_nuevo"), {"nombre": "Guantes", "categoria": "Higiene", "descripcion": "",
                                                       "sucursal": self.local1.pk, "cantidad": 3, "stock_minimo": 5,
                                                       "es_insumo": "on"})
        item = Inventario.objects.get(sucursal=self.local1)
        self.assertEqual((item.producto.nombre, item.cantidad, item.producto.stock_minimo), ("Guantes", 3, 5))

    def test_recibir_plan_suma_stock(self):
        from funciones_app.models import Inventario, PlanInventario, ProductoInsumo
        p = ProductoInsumo.objects.create(nombre="Cera")
        Inventario.objects.create(sucursal=self.local1, producto=p, cantidad=2)
        plan = PlanInventario.objects.create(titulo="Cera", sucursal=self.local1, producto=p, cantidad=5)
        self.client.post(reverse("plan_recibir", args=[plan.pk]))
        self.assertEqual(Inventario.objects.get(producto=p).cantidad, 7)
        plan.refresh_from_db()
        self.assertEqual(plan.estado, "Completado")

    def test_no_ve_inventario_de_otro_local(self):
        from funciones_app.models import Inventario, ProductoInsumo
        item = Inventario.objects.create(sucursal=self.local2, producto=ProductoInsumo.objects.create(nombre="X"))
        self.assertEqual(self.client.get(reverse("inventario_editar", args=[item.pk])).status_code, 404)

    def test_registrar_atencion_crea_venta_y_pago(self):
        from funciones_app.models import Pago, Venta
        r = self.reserva()
        resp = self.client.post(reverse("registrar_atencion"), {"reserva": r.pk, "servicios": [self.s_mani.pk],
                                                                "metodo_pago": "Débito", "observacion": ""})
        self.assertEqual(resp.status_code, 302)
        venta = Venta.objects.get(atencion__reserva=r)
        self.assertEqual((venta.total, venta.empleado, Pago.objects.get(venta=venta).metodo),
                         (Decimal(15000), self.maria, "Débito"))
        r.refresh_from_db()
        self.assertEqual(r.estado, "Completada")

    def test_paginas_gestion_cargan(self):
        for nombre in ("inventario", "inventario_nuevo", "plan_inventario", "plan_nuevo", "ventas",
                       "registrar_atencion", "servicios"):
            self.assertEqual(self.client.get(reverse(nombre)).status_code, 200, nombre)

    def test_empleada_marca_asistencia(self):
        from funciones_app.models import Asistencia
        self.client.logout()
        self.entrar("maria@x.cl")
        self.client.post(reverse("marcar_asistencia"))
        self.client.post(reverse("marcar_asistencia"))
        a = Asistencia.objects.get(trabajador=self.maria)
        self.assertIsNotNone(a.hora_salida)

    def test_propietaria_entra_al_admin(self):
        self.client.logout()
        self.entrar("duena@x.cl")
        self.assertEqual(self.client.get("/admin/").status_code, 200)
