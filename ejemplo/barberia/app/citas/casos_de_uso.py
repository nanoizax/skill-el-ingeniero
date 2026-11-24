"""Casos de uso de las citas: una acción por clase."""
import uuid
from datetime import timedelta, timezone

from app.citas.dominio import (
    MAXIMO_DE_CITAS_FUTURAS_DEL_CLIENTE,
    BarberoInexistente,
    Cita,
    CitaNoEncontrada,
    CitaNoModificable,
    ClienteInexistente,
    SinPermiso,
    hoy_en_la_zona,
    limites_del_dia,
    puede_operar,
    validar_duracion,
    validar_horario,
    validar_inicio,
)
from app.compartido.errores import DatosInvalidos
from app.compartido.fechas import parsear_fecha
from app.compartido.reloj import reloj_real as _reloj_real
from app.compartido.roles import BARBERO, CLIENTE, PERSONAL_DE_ATENCION
from app.compartido.validacion import id_valido


def _cita_del_actor(repositorio, actor, cita_id, incluye_clientes=True):
    cita = repositorio.obtener(id_valido(cita_id, "El identificador de la cita"))
    if cita is None:
        raise CitaNoEncontrada("No encontramos esa cita.")
    if not puede_operar(actor, cita, incluye_clientes):
        raise SinPermiso("No tienes permiso para esa cita.")
    return cita


def _cambiar_estado(repositorio, antes, despues):
    """Compare-and-set: si otra persona cambió la cita en el medio, esta operación pierde con un 409."""
    if not repositorio.cambiar_estado(antes.id, antes.estado, despues.estado):
        actual = repositorio.obtener(antes.id)
        raise CitaNoModificable(f"Esta cita está {actual.estado if actual else 'borrada'} y ya no se puede cambiar.")


class AgendarCita:
    def __init__(self, repositorio, reloj=_reloj_real):
        self._repositorio = repositorio
        self._reloj = reloj

    def ejecutar(self, barbero_id, cliente_id, inicio, duracion_minutos, limite_de_citas_futuras=None):
        validar_duracion(duracion_minutos)
        ahora = self._reloj()
        validar_inicio(inicio, ahora)
        fin = inicio + timedelta(minutes=duracion_minutos)
        validar_horario(inicio, fin)
        nueva = Cita(id=str(uuid.uuid4()), barbero_id=barbero_id, cliente_id=cliente_id,
                     inicio=inicio.astimezone(timezone.utc), fin=fin.astimezone(timezone.utc))
        # Cruce y tope de citas se revisan y se guardan en un solo paso atómico del repositorio.
        self._repositorio.guardar_si_esta_libre(nueva, limite_de_citas_futuras, ahora)
        return nueva


class AgendarCitaPorUsuario:
    """Quién agenda para quién: el cliente solo para sí mismo (con tope de citas por venir); recepción y dueño para
    cualquier cliente que exista; el barbero no agenda. El barbero debe existir y tener rol barbero."""

    def __init__(self, agendar, usuarios):
        self._agendar = agendar
        self._usuarios = usuarios

    def ejecutar(self, actor, barbero_id, cliente_id, inicio, duracion_minutos):
        limite = None
        if actor.rol == CLIENTE:
            cliente_id, limite = actor.id, MAXIMO_DE_CITAS_FUTURAS_DEL_CLIENTE  # se ignora el cliente_id enviado
        elif actor.rol in PERSONAL_DE_ATENCION:
            if cliente_id is None:
                raise DatosInvalidos("Indica para qué cliente es la cita.")
            id_valido(cliente_id, "El cliente")
        else:
            raise SinPermiso("Tu rol no puede agendar citas.")
        id_valido(barbero_id, "El barbero")
        if self._rol_de(barbero_id) != BARBERO:
            raise BarberoInexistente("No encontramos a ese barbero.")
        if actor.rol != CLIENTE and self._rol_de(cliente_id) != CLIENTE:
            raise ClienteInexistente("No encontramos a ese cliente.")
        return self._agendar.ejecutar(barbero_id, cliente_id, inicio, duracion_minutos, limite)

    def _rol_de(self, usuario_id):
        usuario = self._usuarios.por_id(usuario_id)
        return usuario.rol if usuario else None


class CancelarCita:
    def __init__(self, repositorio):
        self._repositorio = repositorio

    def ejecutar(self, actor, cita_id):
        cita = _cita_del_actor(self._repositorio, actor, cita_id)
        cancelada = cita.cancelar()
        _cambiar_estado(self._repositorio, cita, cancelada)
        return cancelada


class MarcarAtendida:
    """Solo el personal marca una cita como atendida (el cliente no), y solo desde la hora de inicio de la cita."""

    def __init__(self, repositorio, reloj=_reloj_real):
        self._repositorio = repositorio
        self._reloj = reloj

    def ejecutar(self, actor, cita_id):
        cita = _cita_del_actor(self._repositorio, actor, cita_id, incluye_clientes=False)
        atendida = cita.atender(self._reloj())
        _cambiar_estado(self._repositorio, cita, atendida)
        return atendida


class MoverCita:
    def __init__(self, repositorio, reloj=_reloj_real):
        self._repositorio = repositorio
        self._reloj = reloj

    def ejecutar(self, actor, cita_id, inicio):
        cita = _cita_del_actor(self._repositorio, actor, cita_id)
        validar_inicio(inicio, self._reloj())
        movida = cita.mover_a(inicio.astimezone(timezone.utc))
        validar_horario(movida.inicio, movida.fin)
        self._repositorio.guardar_si_esta_libre(movida)  # atómico; solo reescribe si la cita sigue confirmada
        return movida


class VerAgenda:
    """El barbero ve solo su agenda; recepción y dueño la de un barbero o la de todos; el cliente no la ve."""

    def __init__(self, repositorio, reloj=_reloj_real):
        self._repositorio = repositorio
        self._reloj = reloj

    def ejecutar(self, actor, fecha, barbero_id=None):
        if actor.rol == BARBERO:
            barbero_id = actor.id  # se ignora el barbero_id pedido
        elif actor.rol not in PERSONAL_DE_ATENCION:
            raise SinPermiso("Tu rol no puede ver la agenda.")
        elif barbero_id is not None:
            id_valido(barbero_id, "El barbero")
        desde, hasta = limites_del_dia(parsear_fecha(fecha, hoy_en_la_zona(self._reloj())))
        return self._repositorio.citas_en_rango(desde.astimezone(timezone.utc), hasta.astimezone(timezone.utc),
                                                barbero_id=barbero_id)


class VerMisCitas:
    def __init__(self, repositorio):
        self._repositorio = repositorio

    def ejecutar(self, actor):
        return self._repositorio.citas_en_rango(cliente_id=actor.id)
