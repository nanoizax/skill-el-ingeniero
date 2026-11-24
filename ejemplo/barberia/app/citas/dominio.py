"""Reglas de las citas. Esta capa no conoce la API ni la base de datos."""
import os
from dataclasses import dataclass, replace
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.compartido.errores import DatosInvalidos, ErrorDeNegocio
from app.compartido.roles import BARBERO, CLIENTE, PERSONAL_DE_ATENCION

ZONA = ZoneInfo(os.environ.get("ZONA_HORARIA") or "America/Santiago")
APERTURA = time(10, 0)
CIERRE = time(20, 0)
DIAS_ABIERTOS = {0, 1, 2, 3, 4, 5}  # lunes a sábado
CONFIRMADA, CANCELADA, ATENDIDA = "confirmada", "cancelada", "atendida"
ESTADOS_QUE_OCUPAN_LA_HORA = (CONFIRMADA, ATENDIDA)  # una cita cancelada libera la hora
DURACION_MINIMA, DURACION_MAXIMA = 1, 480  # minutos
DIAS_MAXIMOS_HACIA_ADELANTE = 365
MAXIMO_DE_CITAS_FUTURAS_DEL_CLIENTE = 3


class CitaEnElPasado(ErrorDeNegocio):
    codigo = "cita_en_el_pasado"


class FueraDeHorario(ErrorDeNegocio):
    codigo = "fuera_de_horario"


class BarberoOcupado(ErrorDeNegocio):
    codigo = "barbero_ocupado"
    tipo = "conflicto"


class SinPermiso(ErrorDeNegocio):
    codigo = "no_autorizado"
    tipo = "prohibido"


class CitaNoEncontrada(ErrorDeNegocio):
    codigo = "cita_no_encontrada"
    tipo = "no_encontrado"


class CitaNoModificable(ErrorDeNegocio):
    codigo = "cita_no_modificable"
    tipo = "conflicto"


class CitaFutura(ErrorDeNegocio):
    codigo = "cita_futura"
    tipo = "conflicto"


class DemasiadasCitas(ErrorDeNegocio):
    codigo = "demasiadas_citas"
    tipo = "conflicto"


class BarberoInexistente(ErrorDeNegocio):
    codigo = "barbero_inexistente"


class ClienteInexistente(ErrorDeNegocio):
    codigo = "cliente_inexistente"


class DuracionInvalida(DatosInvalidos):
    pass


@dataclass(frozen=True)
class Cita:
    id: str
    barbero_id: str
    cliente_id: str
    inicio: datetime
    fin: datetime
    estado: str = CONFIRMADA

    def se_cruza_con(self, otra):
        """Dos citas se cruzan si cada una empieza antes de que termine la otra (terminar justo al inicio no cruza)."""
        return self.inicio < otra.fin and otra.inicio < self.fin

    def _exigir_confirmada(self):
        if self.estado != CONFIRMADA:
            raise CitaNoModificable(f"Esta cita está {self.estado} y ya no se puede cambiar.")

    def cancelar(self):
        self._exigir_confirmada()
        return replace(self, estado=CANCELADA)

    def atender(self, ahora):
        """Solo se atiende una cita cuya hora de inicio ya llegó; si no, la caja del día quedaría distorsionada."""
        self._exigir_confirmada()
        if self.inicio > ahora:
            raise CitaFutura("Esa cita todavía no empieza: se puede marcar como atendida desde su hora de inicio.")
        return replace(self, estado=ATENDIDA)

    def mover_a(self, inicio):
        """La misma cita en otra hora, con la misma duración."""
        self._exigir_confirmada()
        return replace(self, inicio=inicio, fin=inicio + (self.fin - self.inicio))


def puede_operar(actor, cita, incluye_clientes=True):
    """Recepción y dueño operan cualquier cita; el barbero, las de su agenda; el cliente, las suyas."""
    if actor.rol in PERSONAL_DE_ATENCION:
        return True
    if actor.rol == BARBERO:
        return cita.barbero_id == actor.id
    return incluye_clientes and actor.rol == CLIENTE and cita.cliente_id == actor.id


def validar_horario(inicio, fin):
    local_inicio, local_fin = inicio.astimezone(ZONA), fin.astimezone(ZONA)
    mismo_dia = local_inicio.date() == local_fin.date()
    if local_inicio.weekday() not in DIAS_ABIERTOS or not mismo_dia:
        raise FueraDeHorario("La barbería atiende de lunes a sábado.")
    if local_inicio.time() < APERTURA or local_fin.time() > CIERRE:
        raise FueraDeHorario("La barbería atiende de 10:00 a 20:00.")


def validar_duracion(duracion_minutos):
    # type() y no isinstance: True es un int en Python y no es una duración.
    if type(duracion_minutos) is not int or not DURACION_MINIMA <= duracion_minutos <= DURACION_MAXIMA:
        raise DuracionInvalida(
            f"La duración debe ser un número entero de minutos, entre {DURACION_MINIMA} y {DURACION_MAXIMA}.")


def validar_inicio(inicio, ahora):
    """Con zona horaria, a futuro y como mucho un año adelante. Se revisa antes de convertir o sumar horas,
    para que las fechas extremas den un error claro y no un desborde."""
    if not isinstance(inicio, datetime) or inicio.tzinfo is None:
        raise DuracionInvalida("La hora de la cita debe indicar su zona horaria.")
    try:
        if inicio <= ahora:
            raise CitaEnElPasado("No se puede agendar una hora que ya pasó.")
        if inicio > ahora + timedelta(days=DIAS_MAXIMOS_HACIA_ADELANTE):
            raise DatosInvalidos("Solo se puede agendar con hasta un año de anticipación.")
    except OverflowError:
        raise DatosInvalidos("La hora de la cita no es válida.") from None


def hoy_en_la_zona(ahora):
    return ahora.astimezone(ZONA).date()


def limites_del_dia(fecha):
    """Inicio y fin (sin incluir) del día de calendario en la zona del negocio."""
    desde = datetime.combine(fecha, time.min, tzinfo=ZONA)
    return desde, datetime.combine(fecha + timedelta(days=1), time.min, tzinfo=ZONA)
