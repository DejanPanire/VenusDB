"""
URL configuration for Stetikglowapp project.

The `urlpatterns` list routes URLs to  For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from funciones_app.views import *
urlpatterns = [
    path('admin/', admin.site.urls),
    path('agenda/', include('agenda.urls')),
    path('', InventarioList, name='inventario_list'),
    path('sucursal/<int:sucursal_id>/', InventarioList, name='inventario_list_sucursal'),
    path('plan/', PlanInventarioView, name='plan_inventario'),
    path('plan/nuevo/', PlanInventarioCreate, name='plan_inventario_create'),
    path('plan/editar/<int:pk>/', PlanInventarioUpdate, name='plan_inventario_update'),
    path('plan/recibir/<int:pk>/', PlanInventarioRecibir, name='plan_inventario_recibir'), 
    path('nuevo/', InventarioCreate, name='inventario_create'),
    path('editar/<int:pk>/', InventarioUpdate, name='inventario_update'),
    path('eliminar/<int:pk>/', InventarioDelete, name='inventario_delete'),
]