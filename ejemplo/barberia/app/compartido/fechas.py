"""Lectura estricta de fechas AAAA-MM-DD (date.fromisoformat solo acepta además otros formatos)."""
import re
from datetime import date, timedelta

from app.compartido.errores import DatosInvalidos

_FORMATO = re.compile(r"\d{4}-\d{2}-\d{2}")
FECHA_MINIMA = date(2000, 1, 1)
DIAS_HACIA_ADELANTE = 1826  # cinco años


def parsear_fecha(texto, hoy=None):
    """Una fecha real entre el 2000-01-01 y (si se indica `hoy`) cinco años después de hoy."""
    if not isinstance(texto, str) or not _FORMATO.fullmatch(texto):
        raise DatosInvalidos("La fecha debe tener el formato AAAA-MM-DD, por ejemplo 2026-12-01.")
    try:
        fecha = date.fromisoformat(texto)
    except ValueError:
        raise DatosInvalidos("Esa fecha no existe en el calendario.") from None
    if fecha < FECHA_MINIMA or (hoy is not None and fecha > hoy + timedelta(days=DIAS_HACIA_ADELANTE)):
        raise DatosInvalidos("La fecha está fuera del rango permitido (desde el 2000 hasta dentro de cinco años).")
    return fecha
