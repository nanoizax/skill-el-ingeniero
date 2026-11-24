"""El repositorio de citas: la interfaz que usan los casos de uso y su adaptador en memoria (para las pruebas)."""
import threading
from typing import List, Optional, Protocol

from app.citas.dominio import (
    CONFIRMADA,
    ESTADOS_QUE_OCUPAN_LA_HORA,
    BarberoOcupado,
    Cita,
    CitaNoModificable,
    DemasiadasCitas,
)


class RepositorioDeCitas(Protocol):
    def obtener(self, cita_id: str) -> Optional[Cita]: ...

    def guardar(self, cita: Cita) -> None:
        """Inserta o actualiza sin ninguna revisión (datos de apoyo y pruebas)."""

    def guardar_si_esta_libre(self, cita: Cita, limite_de_citas_futuras=None, ahora=None) -> None:
        """Atómico. Una cita que ya existe solo se reescribe (mover) si sigue confirmada, y se ignora a sí misma al
        revisar el cruce con el barbero (BarberoOcupado). Si es nueva y se indica un límite, el cliente no puede
        quedar con más citas confirmadas posteriores a `ahora` (DemasiadasCitas). Si falla, no guarda nada."""

    def cambiar_estado(self, cita_id: str, desde: str, hasta: str) -> bool:
        """Compare-and-set: pasa de `desde` a `hasta` solo si todavía está en `desde`. Devuelve si cambió."""

    def citas_en_rango(self, desde=None, hasta=None, barbero_id=None, cliente_id=None) -> List[Cita]:
        """Citas confirmadas o atendidas con inicio en [desde, hasta), ordenadas por hora. None = sin límite."""


def mensaje_de_cita_cerrada(estado):
    return f"Esta cita está {estado} y ya no se puede cambiar."


def mensaje_de_limite(limite):
    return f"Ya tienes {limite} citas confirmadas por venir. Cancela una o espera a que pase para agendar otra."


class RepositorioEnMemoria:
    def __init__(self):
        self._citas = {}
        self._cerrojo = threading.Lock()

    def obtener(self, cita_id):
        return self._citas.get(cita_id)

    def guardar(self, cita):
        with self._cerrojo:
            self._citas[cita.id] = cita

    def guardar_si_esta_libre(self, cita, limite_de_citas_futuras=None, ahora=None):
        with self._cerrojo:  # la revisión y el guardado ocurren sin que otro hilo se meta en medio
            existente = self._citas.get(cita.id)
            if existente is not None and existente.estado != CONFIRMADA:
                raise CitaNoModificable(mensaje_de_cita_cerrada(existente.estado))
            if any(cita.se_cruza_con(c) for c in self._citas.values()
                   if c.barbero_id == cita.barbero_id and c.id != cita.id and c.estado in ESTADOS_QUE_OCUPAN_LA_HORA):
                raise BarberoOcupado("El barbero ya tiene una cita en ese horario.")
            if existente is None and limite_de_citas_futuras is not None:
                futuras = sum(1 for c in self._citas.values()
                              if c.cliente_id == cita.cliente_id and c.estado == CONFIRMADA and c.inicio > ahora)
                if futuras >= limite_de_citas_futuras:
                    raise DemasiadasCitas(mensaje_de_limite(limite_de_citas_futuras))
            self._citas[cita.id] = cita

    def cambiar_estado(self, cita_id, desde, hasta):
        with self._cerrojo:
            existente = self._citas.get(cita_id)
            if existente is None or existente.estado != desde:
                return False
            self._citas[cita_id] = Cita(existente.id, existente.barbero_id, existente.cliente_id, existente.inicio,
                                        existente.fin, hasta)
            return True

    def citas_en_rango(self, desde=None, hasta=None, barbero_id=None, cliente_id=None):
        coinciden = [c for c in self._citas.values()
                     if c.estado in ESTADOS_QUE_OCUPAN_LA_HORA
                     and (desde is None or c.inicio >= desde) and (hasta is None or c.inicio < hasta)
                     and (barbero_id is None or c.barbero_id == barbero_id)
                     and (cliente_id is None or c.cliente_id == cliente_id)]
        return sorted(coinciden, key=lambda c: (c.inicio, c.id))
