"""Carga datos de prueba. Clave de todos los usuarios: demo123."""
import random
import unicodedata
from datetime import date, time, timedelta
from decimal import Decimal

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from agenda import catalogo, reglas
from agenda.reglas import Estado
from agenda.utils import formatear_rut
from funciones_app.models import (
    Asistencia, Atencion, Cliente, DetalleVenta, Pago, Reserva, Servicio, Sucursal, Trabajador, Turno, Usuario, Venta,
)


def quitar_tildes(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()


def rut_con_dv(cuerpo: int) -> str:
    suma, mult = 0, 2
    for d in reversed(str(cuerpo)):
        suma += int(d) * mult
        mult = 2 if mult == 7 else mult + 1
    r = 11 - (suma % 11)
    dv = "0" if r == 11 else "K" if r == 10 else str(r)
    return formatear_rut(f"{cuerpo}{dv}")


class Command(BaseCommand):
    help = "Carga datos de demostración en las tablas oficiales (usuarios por rol, clave demo123)."

    def add_arguments(self, parser):
        parser.add_argument("--confirmar", action="store_true",
                            help="Confirma que se pueden borrar los datos actuales")

    @transaction.atomic
    def handle(self, *args, **options):
        if not options["confirmar"]:
            self.stdout.write(self.style.WARNING(
                "Esto BORRA reservas, trabajadores, usuarios, servicios, atenciones y ventas de la base de datos.\n"
                "Si estás seguro, corre: python manage.py seed_demo --confirmar"))
            return

        random.seed(7)
        hoy = date.today()
        clave = make_password("demo123")

        # borrar datos anteriores
        Pago.objects.all().delete()
        DetalleVenta.objects.all().delete()
        Venta.objects.all().delete()
        Atencion.objects.all().delete()
        Reserva.objects.all().delete()
        Turno.objects.all().delete()
        Asistencia.objects.all().delete()
        User.objects.filter(username__in=Usuario.objects.values("username")).delete()
        Usuario.objects.all().delete()
        Trabajador.objects.all().delete()

        locales = [("Vargas 1899 (Centro)", "Vargas 1899, Calama", "+56552000001"),
                   ("Bañados Espinoza 1901 (Centro)", "Bañados Espinoza 1901, Calama", "+56941608019"),
                   ("Mall Plaza Calama", "Av. Balmaceda 3242, Calama", "+56552000003")]
        sucursales = [Sucursal.objects.update_or_create(nombre=n, defaults={"direccion": d, "telefono": tel})[0]
                      for n, d, tel in locales]

        rut_n = [20000000]

        def nuevo_trabajador(sucursal, nombre, apellido, rol, especialidad, username, comision=30):
            rut_n[0] += 104729
            t = Trabajador.objects.create(
                sucursal=sucursal, rut=rut_con_dv(rut_n[0]), nombre=nombre, apellido=apellido, correo=username,
                telefono=f"+569{random.randint(10000000, 99999999)}", especialidad=especialidad,
                tipo_contrato="Indefinido", modalidad_pago="Comisión" if rol == "Empleado" else "Sueldo fijo",
                porcentaje_comision=comision if rol == "Empleado" else 0, rol=rol)
            Usuario.objects.create(trabajador=t, username=username, password_hash=clave, activo=True)
            return t

        # propietaria y administradoras
        nuevo_trabajador(sucursales[0], "Antonia", "Propietaria", "Propietaria", None, "propietaria@antonia.cl")
        for s, slug, ap in zip(sucursales, ["vargas", "banados", "mall"], ["Vargas 1899", "Bañados 1901", "Mall Plaza"]):
            nuevo_trabajador(s, "Administradora", ap, "Administradora", None, f"{slug}@antonia.cl")

        # servicios
        Servicio.objects.all().delete()
        serv = {}
        for nombre, cat, dur, precio, nota in catalogo.SERVICIOS:
            serv[(cat, nombre)] = Servicio.objects.create(
                nombre=nombre, categoria_cliente=cat, duracion_minutos=dur, precio_base=Decimal(precio),
                descripcion=nota or None)

        equipo = [("María", "González", "Uñas"),
                  ("Valentina", "Herrera", "Depilación"), ("Javiera", "Morales", "Pestañas")]
        trab = {}
        for s, slug in zip(sucursales, ["vargas", "banados", "mall"]):
            for nombre, apellido, esp in equipo:
                username = f"{quitar_tildes(nombre).lower()}.{slug}@antonia.cl"
                trab[(s.pk, nombre)] = nuevo_trabajador(s, nombre, apellido, "Empleado", esp, username)

        # turnos 10-13 y 14-20, domingo cerrado
        turnos = []
        for delta in range(-30, 15):
            dia = hoy + timedelta(days=delta)
            if dia.weekday() == 6:
                continue
            for t in trab.values():
                turnos += [Turno(trabajador=t, fecha=dia, hora_inicio=time(10), hora_fin=time(13)),
                           Turno(trabajador=t, fecha=dia, hora_inicio=time(14), hora_fin=time(20))]
        Turno.objects.bulk_create(turnos)

        nombres = [("Camila", "Soto"), ("Francisca", "Rojas"), ("Daniela", "Pérez"), ("Josefa", "Muñoz"),
                   ("Antonia", "Vega"), ("Isidora", "Castro"), ("Valentina", "Ríos"), ("Constanza", "Vidal"),
                   ("Fernanda", "Araya"), ("Catalina", "Díaz"), ("Sofía", "Núñez"), ("Martina", "Tapia")]
        clientes = []
        for i, (n, a) in enumerate(nombres):
            c, _ = Cliente.objects.update_or_create(
                rut=rut_con_dv(15000000 + i * 137531),
                defaults={"nombre": n, "apellido": a, "telefono": f"+569{random.randint(10000000, 99999999)}",
                          "correo": quitar_tildes(f"{n}.{a}@email.com").lower()})
            clientes.append(c)
        por_nombre = {reglas.nombre_completo(c): c for c in clientes}

        def reservar(cliente, sucursal, t, servicio, dia, hora, estado):
            return reglas.crear_reserva(cliente=cliente, sucursal=sucursal, trabajador=t, servicios=[servicio],
                                        fecha=dia, hora_inicio=hora, estado=estado,
                                        origen=random.choice([reglas.ORIGEN_WEB, reglas.ORIGEN_SISTEMA]))

        centro = sucursales[0]
        hoy_centro = [
            ("Camila Soto", (catalogo.MANICURA, "Esmaltado permanente un solo tono"), "María", time(10), Estado.CONFIRMADA),
            ("Francisca Rojas", (catalogo.PESTANAS, "Lifting de pestañas"), "Javiera", time(10, 30), Estado.PENDIENTE),
            ("Daniela Pérez", (catalogo.DEP_DAMAS, "Cejas"), "Valentina", time(11), Estado.COMPLETADA),
            ("Josefa Muñoz", (catalogo.PEDICURA, "Esmaltado tradicional"), "María", time(12), Estado.CANCELADA),
            ("Antonia Vega", (catalogo.PESTANAS, "Extensión de pestañas clásica"), "Javiera", time(15), Estado.CONFIRMADA),
            ("Isidora Castro", (catalogo.MANICURA, "Kapping acrílico / polygel / Dipping"), "María", time(16), Estado.PENDIENTE),
            ("Valentina Ríos", (catalogo.DEP_DAMAS, "Piernas completas"), "Valentina", time(17), Estado.CONFIRMADA),
            ("Constanza Vidal", (catalogo.PESTANAS, "Mantenimiento de pestañas (20 días)"), "Javiera", time(18), Estado.PENDIENTE),
        ]
        if hoy.weekday() != 6:
            for cliente, s, t, h, estado in hoy_centro:
                reservar(por_nombre[cliente], centro, trab[(centro.pk, t)], serv[s], hoy, h, estado)

        horas = [time(10), time(10, 30), time(11), time(11, 30), time(12), time(14), time(15), time(16), time(17), time(18)]
        for delta in list(range(-30, 0)) + list(range(1, 6)):
            dia = hoy + timedelta(days=delta)
            if dia.weekday() == 6:
                continue
            for s in sucursales:
                for _ in range(random.randint(3, 6)):
                    t = trab[(s.pk, random.choice(equipo)[0])]
                    servicio = random.choice([x for x in serv.values() if catalogo.area_de(x) == t.especialidad])
                    h = random.choice(horas)
                    fin = reglas.sumar_minutos(dia, h, servicio.duracion_minutos)
                    if fin > reglas.HORA_CIERRE or reglas.hay_conflicto(t, dia, h, fin):
                        continue
                    estado = (random.choices([Estado.COMPLETADA, Estado.CANCELADA], [9, 1])[0] if delta < 0
                              else random.choice([Estado.PENDIENTE, Estado.CONFIRMADA]))
                    reservar(random.choice(clientes), s, t, servicio, dia, h, estado)

        # atención, venta y pago de las reservas completadas
        metodos = ["Efectivo", "Débito", "Crédito", "Transferencia"]
        for r in Reserva.objects.filter(estado=Estado.COMPLETADA).select_related("cliente", "trabajador", "sucursal"):
            atencion = reglas.registrar_atencion(r)
            detalles = list(atencion.detalles.select_related("servicio"))
            total = sum((d.precio_aplicado for d in detalles), Decimal(0))
            venta = Venta.objects.create(cliente=r.cliente, empleado=r.trabajador, sucursal=r.sucursal,
                                         atencion=atencion, total=total, estado="Pagada")
            DetalleVenta.objects.bulk_create([DetalleVenta(venta=venta, servicio=d.servicio, cantidad=1,
                                                           subtotal=d.precio_aplicado) for d in detalles])
            Pago.objects.create(venta=venta, monto=total, metodo=random.choice(metodos))

        if hoy.weekday() != 6:
            Asistencia.objects.bulk_create([Asistencia(trabajador=t, fecha=hoy, hora_entrada=time(9, 55))
                                            for t in trab.values()])

        self.stdout.write(self.style.SUCCESS(
            f"Datos de demo listos: {Reserva.objects.count()} reservas, {Turno.objects.count()} turnos, "
            f"{Atencion.objects.count()} atenciones. Usuarios: propietaria@ / vargas@ / banados@ / mall@antonia.cl; "
            "empleadas: maria.vargas@antonia.cl (y similares). Clave: demo123"))
