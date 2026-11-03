import re


def limpiar_rut(rut: str) -> str:
    return re.sub(r"[^0-9kK]", "", rut or "").upper()


def validar_rut(rut: str) -> bool:
    """Valida el RUT (módulo 11)."""
    limpio = limpiar_rut(rut)
    if not 8 <= len(limpio) <= 9:
        return False
    cuerpo, dv = limpio[:-1], limpio[-1]
    if not cuerpo.isdigit():
        return False
    suma, mult = 0, 2
    for d in reversed(cuerpo):
        suma += int(d) * mult
        mult = 2 if mult == 7 else mult + 1
    esperado = 11 - (suma % 11)
    dv_esperado = "0" if esperado == 11 else "K" if esperado == 10 else str(esperado)
    return dv == dv_esperado


def formatear_rut(rut: str) -> str:
    limpio = limpiar_rut(rut)
    if len(limpio) <= 1:
        return limpio
    cuerpo, dv = limpio[:-1], limpio[-1]
    return f"{int(cuerpo):,}".replace(",", ".") + f"-{dv}"


def clp(valor) -> str:
    return "$" + f"{int(valor):,}".replace(",", ".")
