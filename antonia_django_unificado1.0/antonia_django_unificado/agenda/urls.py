from django.urls import path

from . import views, views_empleado as emp, views_gestion as g

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
    path("empleado/asistencia/", emp.marcar_asistencia, name="marcar_asistencia"),
    path("empleado/reservas/", emp.reservas_asignadas, name="reservas_asignadas"),
    path("empleado/reservas/<int:pk>/estado/", emp.cambiar_estado_reserva, name="cambiar_estado_reserva"),
    path("empleado/perfil/", emp.perfil, name="perfil"),
    # inventario y plan de inventario (Stetikglowapp)
    path("inventario/", g.inventario, name="inventario"),
    path("inventario/nuevo/", g.inventario_nuevo, name="inventario_nuevo"),
    path("inventario/<int:pk>/editar/", g.inventario_editar, name="inventario_editar"),
    path("inventario/<int:pk>/eliminar/", g.inventario_eliminar, name="inventario_eliminar"),
    path("inventario/plan/", g.plan_inventario, name="plan_inventario"),
    path("inventario/plan/nuevo/", g.plan_nuevo, name="plan_nuevo"),
    path("inventario/plan/<int:pk>/editar/", g.plan_editar, name="plan_editar"),
    path("inventario/plan/<int:pk>/recibir/", g.plan_recibir, name="plan_recibir"),
    # atenciones, ventas y servicios (Stetikglowapp)
    path("ventas/", g.ventas, name="ventas"),
    path("ventas/registrar-atencion/", g.registrar_atencion, name="registrar_atencion"),
    path("servicios/", g.servicios, name="servicios"),
    path("servicios/nuevo/", g.servicio_form, name="servicio_nuevo"),
    path("servicios/<int:pk>/editar/", g.servicio_form, name="servicio_editar"),
    path("api/disponibilidad/", views.api_disponibilidad, name="api_disponibilidad"),
    path("api/trabajadoras/", views.api_trabajadoras, name="api_trabajadoras"),
]
