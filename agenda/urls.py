from django.urls import path
from . import views, views_gestion, views_empleado

urlpatterns = [
   # --- Rutas principales y autenticación (Tus compañeros) ---
    path("", views.inicio, name="inicio"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("cambiar-local/", views.cambiar_sucursal, name="cambiar_sucursal"),
    path("calendario/", views.calendario, name="calendario"),
    path("calendario/reserva/<int:pk>/estado/", views.cambiar_estado, name="cambiar_estado_reserva"),
    path("reservar/", views.reservar, name="reservar"),

    # --- Módulo de Empleados ---
    path("empleado/", views_empleado.mi_agenda, name="mi_agenda"),
    path("empleado/asistencia/", views_empleado.marcar_asistencia, name="marcar_asistencia"),
    path("empleado/reservas/", views_empleado.reservas_asignadas, name="reservas_asignadas"),
    path("empleado/reservas/<int:pk>/estado/", views_empleado.cambiar_estado_reserva, name="emp_cambiar_estado_reserva"),
    path("empleado/perfil/", views_empleado.perfil, name="perfil"),

    # --- Módulo de Inventario e Insumos (Tus rutas) ---
    path("gestion/inventario/", views_gestion.InventarioList, name="inventario"),
    path("gestion/inventario/sucursal/<int:sucursal_id>/", views_gestion.InventarioList, name="inventario_list_sucursal"),
    path("gestion/inventario/nuevo/", views_gestion.InventarioCreate, name="inventario_create"),
    path("gestion/inventario/editar/<int:pk>/", views_gestion.InventarioUpdate, name="inventario_update"),
    path("gestion/inventario/eliminar/<int:pk>/", views_gestion.InventarioDelete, name="inventario_delete"),
    path("gestion/inventario/producto/<int:pk>/", views_gestion.producto_detail, name="producto_detail"),
    path("gestion/inventario/producto/<int:pk>/descontar/", views_gestion.descontarStock, name="descontar_stock"),

    # --- Módulo de Planes de Inventario (Tus rutas) ---
    path("gestion/planes-inventario/", views_gestion.PlanInventarioView, name="plan_inventario"),
    path("gestion/planes-inventario/nuevo/", views_gestion.PlanInventarioCreate, name="plan_inventario_create"),
    path("gestion/planes-inventario/editar/<int:pk>/", views_gestion.PlanInventarioUpdate, name="plan_inventario_update"),
    path("gestion/planes-inventario/recibir/<int:pk>/", views_gestion.PlanInventarioRecibir, name="plan_inventario_recibir"),

    # --- Módulo de Recursos Humanos / Personal (Tus rutas) ---
    path("gestion/personal/", views_gestion.personalList, name="personal_list"),
    path("gestion/personal/nuevo/", views_gestion.personalCreate, name="personal_create"),
    path("gestion/personal/<int:pk>/", views_gestion.personalDetail, name="personal_detail"),
    path("gestion/personal/<int:pk>/editar/", views_gestion.personalUpdate, name="personal_update"),
    path("gestion/personal/<int:pk>/eliminar/", views_gestion.personalDelete, name="personal_delete"),

    # --- Módulo de Servicios y Ventas (Tus rutas) ---
    path("gestion/servicios/", views_gestion.servicios, name="servicios"),
    path("gestion/ventas/", views_gestion.ventas, name="ventas"),
    path("gestion/atencion/registrar/", views_gestion.registrar_atencion, name="registrar_atencion"),
]
