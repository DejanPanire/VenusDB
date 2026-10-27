# Agenda y reservas

App `agenda` del proyecto: login, agenda múltiple, formulario de reservas (público, para el QR)
y panel de empleada. Usa los modelos de `funciones_app` y no tiene modelos propios.

## Cómo probarla
```bash
python manage.py migrate
python manage.py seed_demo --confirmar   # OJO: borra reservas, trabajadores, usuarios, servicios y ventas
python manage.py runserver
```
Entrar a http://127.0.0.1:8000/agenda/ (clave de todos: `demo123`):

| Rol | Usuario |
|-----|---------|
| Propietaria | `propietaria@antonia.cl` |
| Administradora (Vargas 1899) | `vargas@antonia.cl` |
| Empleada | `maria.vargas@antonia.cl` |

## Archivos
- `reglas.py`: horarios, turnos y reservas.
- `catalogo.py`: servicios, precios y tiempos.
- `permisos.py` y `backends.py`: roles y login con la tabla `Usuario`.
- `static/agenda/css/venus.css`: estilos.
- En `settings.py` se agregó `agenda` a `INSTALLED_APPS`, el context processor `agenda.context_processors.rol`
  y `AUTHENTICATION_BACKENDS`. En `urls.py` se agregó `path('agenda/', include('agenda.urls'))`.
