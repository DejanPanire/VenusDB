"""Permisos según el rol del trabajador (Trabajador.rol).

- Propietaria: ve todos los locales.
- Administradora: solo su local.
- Empleado: solo su agenda, sus reservas y su perfil.
"""
import unicodedata
from functools import wraps

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from funciones_app.models import Sucursal, Usuario

PROPIETARIO, ADMIN_LOCAL, EMPLEADO = "propietario", "admin_local", "empleado"


def _normalizar(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode().strip().lower()


def rol_de_trabajador(trabajador) -> str:
    rol = _normalizar(trabajador.rol)
    if rol.startswith("propiet"):
        return PROPIETARIO
    if rol.startswith("admin"):
        return ADMIN_LOCAL
    return EMPLEADO


def cuenta_de(user):
    """Cuenta activa del usuario conectado."""
    if not user.is_authenticated:
        return None
    if not hasattr(user, "_cuenta_venus"):
        user._cuenta_venus = (Usuario.objects.select_related("trabajador__sucursal")
                              .filter(username=user.username, activo=True).first())
    return user._cuenta_venus


def trabajador_de(user):
    """Trabajador del usuario conectado."""
    cuenta = cuenta_de(user)
    return cuenta.trabajador if cuenta else None


def rol_de(user):
    if not user.is_authenticated:
        return None
    t = trabajador_de(user)
    if t:
        return rol_de_trabajador(t)
    return PROPIETARIO if user.is_superuser else None


def es_empleado(user) -> bool:
    return rol_de(user) == EMPLEADO


def es_propietario(user) -> bool:
    return rol_de(user) == PROPIETARIO


def sucursales_permitidas(user):
    """Locales que puede ver el usuario."""
    rol = rol_de(user)
    if rol == PROPIETARIO:
        return Sucursal.objects.all().order_by("id")
    t = trabajador_de(user)
    if t:
        return Sucursal.objects.filter(pk=t.sucursal_id)
    return Sucursal.objects.none()


def sucursal_actual(request):
    """Local activo. Solo la propietaria puede cambiarlo."""
    permitidas = sucursales_permitidas(request.user)
    if es_propietario(request.user):
        return permitidas.filter(pk=request.session.get("sucursal_id") or 0).first() or permitidas.first()
    return permitidas.first()


def pagina_inicial(user) -> str:
    return "mi_agenda" if es_empleado(user) else "calendario"


def gestion_requerida(vista):
    """Solo propietaria y administradoras."""
    @wraps(vista)
    @login_required
    def envoltura(request, *args, **kwargs):
        rol = rol_de(request.user)
        if rol is None:
            logout(request)
            messages.error(request, "Tu cuenta no está activa o no tiene una ficha de trabajador.")
            return redirect("login")
        if rol == EMPLEADO:
            messages.error(request, "Esa sección es solo para administración.")
            return redirect("mi_agenda")
        if sucursal_actual(request) is None:
            messages.error(request, "Aún no hay locales registrados. Créalos en /admin/.")
            return redirect("logout")
        return vista(request, *args, **kwargs)
    return envoltura


def empleado_requerido(vista):
    """Solo empleados. Deja su ficha en request.trabajador."""
    @wraps(vista)
    @login_required
    def envoltura(request, *args, **kwargs):
        rol = rol_de(request.user)
        if rol is None:
            logout(request)
            messages.error(request, "Tu cuenta no está activa. Contacta a la administración.")
            return redirect("login")
        if rol != EMPLEADO:
            return redirect("calendario")
        request.trabajador = trabajador_de(request.user)
        return vista(request, *args, **kwargs)
    return envoltura
