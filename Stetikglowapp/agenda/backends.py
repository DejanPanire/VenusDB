"""Login con la tabla Usuario (username + password_hash).

Django necesita un User para la sesión, así que se crea uno con el mismo username
y sin contraseña propia.
"""
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User

from funciones_app.models import Usuario


class UsuarioVenusBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None
        cuenta = (Usuario.objects.select_related("trabajador")
                  .filter(username__iexact=username.strip()).first())
        if cuenta is None or not check_password(password, cuenta.password_hash):
            return None
        if not cuenta.activo:
            # para mostrar el mensaje en el login
            if request is not None:
                request.usuario_inactivo = True
            return None
        t = cuenta.trabajador
        user, creado = User.objects.get_or_create(username=cuenta.username)
        cambios = creado or user.first_name != t.nombre or user.last_name != t.apellido or user.email != (t.correo or "")
        if cambios:
            user.first_name, user.last_name, user.email = t.nombre, t.apellido, t.correo or ""
            if creado:
                user.set_unusable_password()
            user.save()
        return user

    def get_user(self, user_id):
        return User.objects.filter(pk=user_id).first()
