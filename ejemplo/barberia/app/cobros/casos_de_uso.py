"""Casos de uso de los cobros: una acción por clase."""
import uuid
from datetime import timezone

from app.citas.dominio import ATENDIDA, CitaNoEncontrada, SinPermiso, hoy_en_la_zona, limites_del_dia, puede_operar
from app.cobros.dominio import CitaNoAtendida, CitaYaCobrada, Cobro, armar_cierre, validar_medio, validar_monto
from app.compartido.fechas import parsear_fecha
from app.compartido.reloj import reloj_real
from app.compartido.roles import DUENO


class RegistrarCobro:
    """Lo registran recepción, dueño y el barbero de esa cita, y solo sobre una cita atendida."""

    def __init__(self, cobros, citas, reloj=reloj_real):
        self._cobros = cobros
        self._citas = citas
        self._reloj = reloj

    def ejecutar(self, actor, cita_id, monto, medio):
        cita = self._citas.obtener(cita_id)
        if cita is None:
            raise CitaNoEncontrada("No encontramos esa cita.")
        if not puede_operar(actor, cita, incluye_clientes=False):
            raise SinPermiso("No tienes permiso para cobrar esa cita.")
        validar_monto(monto)
        validar_medio(medio)
        if cita.estado != ATENDIDA:
            raise CitaNoAtendida("Solo se puede cobrar una cita que ya fue atendida.")
        if self._cobros.de_la_cita(cita.id):
            raise CitaYaCobrada("Esa cita ya fue cobrada.")
        cobro = Cobro(id=str(uuid.uuid4()), cita_id=cita.id, barbero_id=cita.barbero_id, cita_inicio=cita.inicio,
                      monto=monto, medio=medio, registrado_en=self._reloj())
        self._cobros.guardar(cobro)  # si dos cobros llegan a la vez, el repositorio deja pasar solo uno
        return cobro


class CierreDeCaja:
    """Solo el dueño. El día se define en la zona del negocio por la hora de la cita atendida y cobrada."""

    def __init__(self, cobros, reloj=reloj_real):
        self._cobros = cobros
        self._reloj = reloj

    def ejecutar(self, actor, fecha):
        if actor.rol != DUENO:
            raise SinPermiso("Solo el dueño puede ver el cierre de caja.")
        dia = parsear_fecha(fecha, hoy_en_la_zona(self._reloj()))
        desde, hasta = limites_del_dia(dia)
        return armar_cierre(dia, self._cobros.en_rango(desde.astimezone(timezone.utc), hasta.astimezone(timezone.utc)))
