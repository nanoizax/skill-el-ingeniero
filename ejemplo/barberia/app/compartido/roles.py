"""Roles del sistema y la persona que realiza una acción (id y rol)."""
from dataclasses import dataclass

DUENO = "dueno"
RECEPCION = "recepcion"
BARBERO = "barbero"
CLIENTE = "cliente"
ROLES = (DUENO, RECEPCION, BARBERO, CLIENTE)
PERSONAL_DE_ATENCION = (DUENO, RECEPCION)  # pueden operar sobre las citas de cualquiera


@dataclass(frozen=True)
class Actor:
    id: str
    rol: str
