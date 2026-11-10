# Venus — Centro de Estética (antonia_django unificado)

Unión de **antonia_django8.0** (login por rol, agenda, reserva por QR, panel de empleada) y **Stetikglowapp**
(inventario, plan de inventario, atenciones y ventas), con la estética de antonia (`venus.css`),
modelos tradicionales de Django y base de datos **MySQL**.

## Puesta en marcha
1. Crea la base en MySQL / MariaDB (XAMPP, Workbench o consola):
   `CREATE DATABASE VenusDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`
2. Revisa usuario y clave en `config/settings.py` → `DATABASES` (por defecto `root` sin clave en 127.0.0.1:3306).
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate          # crea las tablas oficiales funciones_app_*
python manage.py seed_demo          # datos de demostración
python manage.py createsuperuser    # opcional, para /admin/
python manage.py runserver
```
Entra a http://127.0.0.1:8000 con alguna de estas cuentas (clave `demo123`):

| Rol | Usuario | Qué ve |
|-----|---------|--------|
| Propietaria | `propietaria@antonia.cl` | Los 3 locales (cambia de local desde el menú) |
| Admin local 1 | `vargas@antonia.cl` | Solo Vargas 1899 (Centro) |
| Admin local 2 | `banados@antonia.cl` | Solo Bañados Espinoza 1901 (Centro) |
| Admin local 3 | `mall@antonia.cl` | Solo Mall Plaza Calama |
| Empleada | `maria.vargas@antonia.cl` | Solo su propia agenda, sus reservas y su perfil |

Hay una cuenta de empleada por cada trabajadora: `maria`, `valentina`, `javiera` + `.vargas`, `.banados` o `.mall` + `@antonia.cl`.

## Módulos traídos de Stetikglowapp
| Menú | Vista | Modelos |
|------|-------|---------|
| Inventario de insumos | `/inventario/` (lista por local, agregar, editar, eliminar) | ProductoInsumo, Inventario |
| Plan de inventario | `/inventario/plan/` (crear, editar, **recibir** = suma al stock) | PlanInventario |
| Atenciones y ventas | `/ventas/` (totales y comisiones) y `/ventas/registrar-atencion/` | Atencion, DetalleAtencion, Venta, DetalleVenta, Pago |
| Servicios y precios | `/servicios/` (editar: solo propietaria) | Servicio |

- Vistas en `agenda/views_gestion.py`, formularios en `agenda/forms.py`, templates en
  `agenda/templates/agenda/gestion/` con las clases de `venus.css` (sin Bootstrap).
- "Registrar atención y cobro" toma una reserva confirmada de los últimos 7 días, la marca completada y crea
  atención + venta + pago en una sola transacción.
- La propietaria ve en el menú **Administración**, que abre `/admin/` con su misma sesión
  (personal, usuarios, turnos, locales, clientes).
- Las empleadas marcan **entrada/salida** desde "Mi agenda" (modelo Asistencia).

## Modelos
Todos los datos están en la app **`funciones_app`** (`models.py` oficial, sin cambios; tablas `funciones_app_*`).
La app `agenda` no tiene modelos: solo vistas, templates y JS. La lógica de negocio está en `agenda/reglas.py`.

| Modelo                       | Para qué se usa en el sistema                                                |
|------------------------------|-------------------------------------------------------------------------------|
| Sucursal                     | Los 3 locales                                                                  |
| Trabajador                   | Fichas del personal; `rol` define el acceso y `especialidad` qué servicios atiende |
| Usuario                      | Cuenta de acceso (username + password_hash + activo) de cada Trabajador        |
| Turno                        | Horario de trabajo por día; fuera de los turnos queda bloqueado (colación)    |
| Servicio                     | Catálogo; `categoria_cliente` se compara con `Trabajador.especialidad`         |
| Cliente                      | Clientas (se crean o actualizan por RUT al reservar)                          |
| Reserva + DetalleReserva     | La cita y sus servicios con precio_reservado; `hora_fin` = suma de duraciones |
| Atencion + DetalleAtencion   | Se crean al marcar una reserva como "Completada"                              |
| Asistencia                   | Entrada / salida del personal (datos de demo)                                 |

Servicios, precios y tiempos: **`agenda/catalogo.py`**, copiados del *Formulario Tiempos de Atención*.
`seed_demo` los carga en `Servicio` (`categoria_cliente` = sección del formulario):

| Categoría | Servicios | Lo atiende (`Trabajador.especialidad`) |
|---|---|---|
| Depilación Damas | 31 zonas (rostro, cejas, bozo… brasileña, rebajes, parches) | Depilación (Valentina) |
| Depilación Varones | 32 zonas (incluye pectorales) | Depilación (Valentina) |
| Manicuras y set de uñas | 15 (esmaltados, acrílicas/polygel por talla, esculpidas, kapping, varón) | Uñas (María) |
| Pedicura | 6 (esmaltados, podología, limpieza profunda, varón) | Uñas |
| Retiros, reparación y mantenimiento | 5 | Uñas |
| Para princesas (hasta 8 años) | 4 | Uñas |
| Pestañas | 5 (lifting, retiro, extensión clásica / con efecto, mantenimiento 20 días) | Pestañas (Javiera) |

La relación categoría → especialidad está en `catalogo.AREAS`. Para cambiar un precio en un sistema ya
funcionando, usa `/admin/` → Servicios (el `seed_demo` borra y recarga todo).
Los tiempos de Pestañas son estimados (solo se entregaron precios). "Diseño mano alzada (por uña)" ($3.000–$5.000, sin tiempo) no se carga como servicio reservable.

- Estados de reserva: los oficiales `Pendiente`, `Confirmada`, `Completada`, `Cancelada`.
- `Reserva.origen` guarda `Web/QR` (reservó la clienta por el QR) o `Sistema` (la registró la administración).
- Si un día el trabajador no tiene turnos cargados, se usa el horario del local (10:00–20:00).

## Roles
El rol sale de **`Trabajador.rol`**:
- **Propietario/a**: ve todo y cambia de local desde el menú lateral ("Local activo").
- **Administrador/a**: queda fijo en el local de su ficha (`Trabajador.sucursal`).
- **Empleado** (o cualquier otro valor): solo su agenda, sus reservas asignadas (confirmar/cancelar) y su perfil.
  Solo los trabajadores con este rol aparecen como columnas en la agenda y en el formulario de reserva.
- El login revisa `Usuario.username` + `Usuario.password_hash` (backend `agenda/backends.py`). Si `activo` es
  falso no puede entrar, y si se desactiva con la sesión abierta, queda fuera en la página siguiente.
- Crear un usuario: `/admin/` → Trabajadores → agregar la ficha; luego Usuarios → agregar, elegir el
  trabajador y escribir la contraseña (se guarda cifrada).
- Un superusuario creado con `createsuperuser` se comporta como propietario.

> Nota: en el `models.py` oficial, `Proveedor.__str__` usa `razon_social`, pero ese campo no existe.
> Por eso Proveedor, FacturaCompra y DetalleCompra no están en el admin hasta que el equipo lo corrija.

## Mapa React → Django
| React                | Django                                              |
|----------------------|-----------------------------------------------------|
| App.tsx (estado `view`) | `config/urls.py` + `agenda/urls.py`              |
| Login.tsx            | `login_view` + `templates/agenda/login.html`        |
| CalendarView.tsx     | `calendario`, `cambiar_estado` + `calendario.html`  |
| BookingForm.tsx      | `reservar`, `api_*` + `reservar.html`               |
| Datos mock           | `funciones_app/models.py` + `seed_demo`                  |

## Marca y colores
- Logos en `agenda/static/agenda/img/` (SVG): `venus-logo.svg` (horizontal), `venus-logo-vertical.svg`, `venus-icono.svg` y `favicon.svg`. Los PNG para impresión/redes están en la carpeta `logos_venus/` aparte.
- Estilos en `agenda/static/agenda/css/venus.css` (colores en las variables de `:root`).
- Colores de estado (clases `.estado-*` del CSS): pendiente = amarillo, confirmada = verde claro, completada = verde fuerte, cancelada = rojo. Horarios ocupados en rojo y disponibles en verde. El resto de la interfaz mantiene la paleta rosada.

## Notas
- `/reservar/` es público (para el código QR); el resto exige login.
- La sucursal elegida al iniciar sesión se guarda en la sesión.
- Los conflictos de horario (reservas, fuera de turno, fuera de 10:00–20:00) se validan en el servidor.
- Los íconos (Lucide) se cargan por internet desde `base.html`.
- Administración de servicios, trabajadores, usuarios, turnos y reservas: `/admin/`.
- Antes de producción: cambiar `SECRET_KEY`, `DEBUG=False` y `ALLOWED_HOSTS`.
- Pruebas: `python manage.py test agenda` (el usuario de MySQL debe poder crear la base `test_VenusDB`).
