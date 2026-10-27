"""Servicios, precios y tiempos del centro (Formulario Tiempos de Atención).

Los tiempos de Pestañas son estimados.
"""

DEP_DAMAS = "Depilación Damas"
DEP_VARONES = "Depilación Varones"
MANICURA = "Manicuras y set de uñas"
PEDICURA = "Pedicura"
RETIROS = "Retiros, reparación y mantenimiento"
PRINCESAS = "Para princesas (hasta 8 años)"
PESTANAS = "Pestañas"

AREAS = {
    DEP_DAMAS: "Depilación",
    DEP_VARONES: "Depilación",
    MANICURA: "Uñas",
    PEDICURA: "Uñas",
    RETIROS: "Uñas",
    PRINCESAS: "Uñas",
    PESTANAS: "Pestañas",
}

_NO_INCLUYE_TAPON = "No incluye tapón de oído y nariz."

# Depilación: (zona, precio damas, min damas, precio varones, min varones, nota)
_ZONAS_DEPILACION = [
    ("Rostro completo", 12000, 20, 15000, 30, _NO_INCLUYE_TAPON),
    ("Cejas", 6000, 10, 8000, 15, ""),
    ("Bozo", 4000, 5, 5000, 10, ""),
    ("Mentón", 4000, 5, 7000, 10, ""),
    ("Pómulos", 4000, 5, 5000, 10, ""),
    ("Nariz (superficial)", 4000, 5, 3000, 10, ""),
    ("Patillas", 4000, 5, 5000, 10, ""),
    ("Tapón oídos", 4000, 5, 4000, 10, ""),
    ("Tapón nariz", 4000, 5, 4000, 10, ""),
    ("Frente", 4000, 5, 4000, 10, ""),
    ("Cuello", 4000, 5, 4000, 15, ""),
    ("Axilas", 6000, 5, 7000, 10, ""),
    ("Brazos completos", 9000, 30, 12000, 40, ""),
    ("1/2 brazos", 6000, 20, 8000, 25, ""),
    ("Abdomen", 6000, 15, 7000, 25, ""),
    ("Pectorales", None, None, 7000, 15, ""),  # solo varones
    ("Línea ombligo", 3000, 5, 5000, 10, ""),
    ("Espalda completa", 10000, 20, 14000, 35, ""),
    ("1/2 espalda", 4000, 10, 7000, 20, ""),
    ("Dedos", 3000, 5, 3000, 10, ""),
    ("Manos", 3000, 5, 4000, 10, ""),
    ("Piernas completas", 15000, 40, 20000, 50, ""),
    ("1/2 piernas", 8000, 25, 10000, 30, ""),
    ("Glúteos completos", 9000, 25, 10000, 30, ""),
    ("1/2 glúteos", 5000, 15, 6000, 20, ""),
    ("Entre glúteos", 5000, 10, 6000, 15, ""),
    ("Brasileña completa", 17000, 30, 21000, 40, ""),
    ("Brasileña sin *", 14000, 20, 18000, 25, "Así figura en el formulario (el * no está explicado)."),
    ("Rebaje extra", 8000, 15, 11000, 25, ""),
    ("Rebaje lateral ropa íntima", 5000, 10, 9000, 15, ""),
    ("Rebaje especial (moicano)", 14000, 30, 16000, 40, ""),
    ("Parches extras", 3000, 5, 3000, 10, ""),
]

SERVICIOS = []  # (nombre, categoría, minutos, precio, nota)
for zona, p_dama, m_dama, p_varon, m_varon, nota in _ZONAS_DEPILACION:
    if p_dama is not None:
        SERVICIOS.append((zona, DEP_DAMAS, m_dama, p_dama, nota))
for zona, p_dama, m_dama, p_varon, m_varon, nota in _ZONAS_DEPILACION:
    SERVICIOS.append((zona, DEP_VARONES, m_varon, p_varon, nota))

SERVICIOS += [
    # Manicuras y set de uñas
    ("Esmaltado permanente un solo tono", MANICURA, 60, 20000, ""),
    ("Esmaltado permanente con diseño", MANICURA, 60, 25000, ""),
    ("Esmaltado tradicional", MANICURA, 60, 17000, ""),
    ("Uñas acrílicas / polygel talla n°1", MANICURA, 120, 30000, ""),
    ("Uñas acrílicas / polygel talla n°2", MANICURA, 120, 33000, ""),
    ("Uñas acrílicas / polygel talla n°3", MANICURA, 150, 37000, ""),
    ("Uñas acrílicas / polygel talla n°4-5", MANICURA, 150, 40000,
     "En el formulario dice: talla 3 y 4 en Excel."),
    ("Esculpidas hasta n°3", MANICURA, 120, 42000, ""),
    ("Esculpidas hasta n°4-5", MANICURA, 150, 45000, ""),
    ("Kapping Rubber gel / Bio builder / Tratamientos", MANICURA, 90, 30000, ""),
    ("Kapping acrílico / polygel / Dipping", MANICURA, 120, 30000, ""),
    ("Limpieza de manicura profunda", MANICURA, 35, 15000, ""),
    ("Manicura varón + esmaltado tradicional", MANICURA, 60, 17000, ""),
    ("Manicura varón + esmaltado permanente", MANICURA, 60, 20000, ""),
    ("Manicura varón + esmaltado permanente C/D", MANICURA, 60, 25000, "C/D = con diseño."),
    # Pedicura
    ("Esmaltado permanente un tono", PEDICURA, 60, 22000, ""),
    ("Esmaltado permanente con diseños", PEDICURA, 60, 25000, ""),
    ("Esmaltado tradicional", PEDICURA, 60, 20000, ""),
    ("Podología (previa cita)", PEDICURA, 90, 27000, ""),
    ("Limpieza profunda", PEDICURA, 60, 17000, ""),
    ("Pedicura varón", PEDICURA, 60, 20000, ""),
    # Retiros, reparación y mantenimiento
    ("Retiro de esmaltado permanente / Rubber", RETIROS, 30, 5000, ""),
    ("Retiro de uñas acrílicas de otro salón", RETIROS, 60, 12000, ""),
    ("Retiro de uñas acrílicas del salón", RETIROS, 60, 10000, "Uñas hechas en nuestros locales."),
    ("Reparación de una adicional de acrílico y polygel", RETIROS, 20, 4000, ""),
    ("Mantenimiento uñas acrílicas / polygel", RETIROS, 120, 30000, ""),
    # Para princesas (hasta 8 años)
    ("Esmaltado tradicional", PRINCESAS, 60, 12000, ""),
    ("Esmaltado permanente", PRINCESAS, 60, 15000, ""),
    ("Pedicura + esmaltado tradicional", PRINCESAS, 60, 12000, ""),
    ("Pedicura + esmaltado permanente", PRINCESAS, 60, 15000, ""),
    # Pestañas
    ("Lifting de pestañas", PESTANAS, 60, 25000, "Tiempo estimado."),
    ("Retiro de pestañas", PESTANAS, 30, 8000, "Tiempo estimado."),
    ("Extensión de pestañas clásica", PESTANAS, 120, 40000, "Tiempo estimado."),
    ("Extensión de pestañas con efecto", PESTANAS, 150, 45000, "Tiempo estimado."),
    ("Mantenimiento de pestañas (20 días)", PESTANAS, 90, 28000, "Tiempo estimado."),
]
# "Diseño mano alzada" ($3.000 a $5.000 por uña) se cobra aparte, no se reserva.


def area_de(servicio) -> str:
    """Especialidad que atiende el servicio."""
    return AREAS.get(servicio.categoria_cliente or "", servicio.categoria_cliente or "")
