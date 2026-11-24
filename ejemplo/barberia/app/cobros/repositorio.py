"""El repositorio de cobros: la interfaz que usan los casos de uso y su adaptador en memoria (para las pruebas)."""
import threading
from typing import List, Optional, Protocol

from app.cobros.dominio import CitaYaCobrada, Cobro


class RepositorioDeCobros(Protocol):
    def guardar(self, cobro: Cobro) -> None:
        """Guarda el cobro; lanza CitaYaCobrada si la cita ya tenía uno."""

    def de_la_cita(self, cita_id: str) -> Optional[Cobro]: ...

    def en_rango(self, desde, hasta) -> List[Cobro]:
        """Cobros cuya cita empezó en [desde, hasta) (instantes en UTC)."""


class RepositorioDeCobrosEnMemoria:
    def __init__(self):
        self._por_cita = {}
        self._cerrojo = threading.Lock()

    def guardar(self, cobro):
        with self._cerrojo:
            if cobro.cita_id in self._por_cita:
                raise CitaYaCobrada("Esa cita ya fue cobrada.")
            self._por_cita[cobro.cita_id] = cobro

    def de_la_cita(self, cita_id):
        return self._por_cita.get(cita_id)

    def en_rango(self, desde, hasta):
        return [c for c in self._por_cita.values() if desde <= c.cita_inicio < hasta]
