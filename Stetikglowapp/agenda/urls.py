from django.urls import path

from . import views, views_empleado as emp

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("cambiar-local/", views.cambiar_sucursal, name="cambiar_sucursal"),
    path("calendario/", views.calendario, name="calendario"),
    path("calendario/reserva/<int:pk>/estado/", views.cambiar_estado, name="cambiar_estado"),
    path("reservar/", views.reservar, name="reservar"),
    # empleado
    path("empleado/", emp.mi_agenda, name="mi_agenda"),
    path("empleado/reservas/", emp.reservas_asignadas, name="reservas_asignadas"),
    path("empleado/reservas/<int:pk>/estado/", emp.cambiar_estado_reserva, name="cambiar_estado_reserva"),
    path("empleado/perfil/", emp.perfil, name="perfil"),
    path("api/disponibilidad/", views.api_disponibilidad, name="api_disponibilidad"),
    path("api/trabajadoras/", views.api_trabajadoras, name="api_trabajadoras"),
]
