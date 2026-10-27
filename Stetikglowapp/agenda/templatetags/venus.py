"""Filtros para los templates."""
from django import template

from agenda import reglas

register = template.Library()

# color de cada trabajadora según su id
PALETA = ["#F4C2D7", "#E8A1BD", "#D982A5", "#C97B9E", "#B9779A", "#E5A9C2"]


@register.filter
def nombre_completo(persona):
    return reglas.nombre_completo(persona) if persona else ""


@register.filter
def clp(valor):
    return reglas.clp(valor)


@register.filter
def clase_estado(estado):
    return reglas.CLASES_ESTADO.get(estado, "")


@register.filter
def color(trabajador):
    return PALETA[(trabajador.pk or 0) % len(PALETA)] if trabajador else PALETA[0]


@register.filter
def inicial(texto):
    return (texto or "?")[:1].upper()
