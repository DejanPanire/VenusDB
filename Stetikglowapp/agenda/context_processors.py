from .permisos import ADMIN_LOCAL, EMPLEADO, PROPIETARIO, rol_de, sucursal_actual, sucursales_permitidas, trabajador_de


MENU_EMPLEADO = [
    ("agenda", "mi_agenda", "calendar-days", "Mi agenda"),
    ("reservas", "reservas_asignadas", "clipboard-list", "Reservas asignadas"),
    ("perfil", "perfil", "user", "Mi perfil"),
]


def rol(request):
    if not request.user.is_authenticated:
        return {}
    rol_actual = rol_de(request.user)
    t = trabajador_de(request.user)
    texto = {
        PROPIETARIO: "Propietaria",
        ADMIN_LOCAL: "Administradora de local",
        EMPLEADO: (t.especialidad or t.rol) if t else "Empleada",
    }.get(rol_actual, "Sin rol")
    return {
        "es_propietario": rol_actual == PROPIETARIO,
        "es_empleado": rol_actual == EMPLEADO,
        "mi_trabajador": t if rol_actual == EMPLEADO else None,
        "menu_empleado": MENU_EMPLEADO if rol_actual == EMPLEADO else [],
        "locales_menu": sucursales_permitidas(request.user) if rol_actual == PROPIETARIO else [],
        "local_activo": sucursal_actual(request),
        "rol_texto": texto,
    }
