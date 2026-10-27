from django.contrib import admin
from .models import PlanInventario, Sucursal, ProductoInsumo

# Registramos los modelos para que aparezcan en el panel de administración
admin.site.register(PlanInventario)
admin.site.register(Sucursal)
admin.site.register(ProductoInsumo)