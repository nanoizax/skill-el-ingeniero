"""Reglas de los cobros. El dinero son siempre pesos enteros: nunca decimales."""
from dataclasses import dataclass
from datetime import datetime

from app.compartido.errores import ErrorDeNegocio

EFECTIVO, TARJETA, TRANSFERENCIA = "efectivo", "tarjeta", "transferencia"
MEDIOS = (EFECTIVO, TARJETA, TRANSFERENCIA)
MONTO_MAXIMO = 100_000_000  # tope de cordura: evita errores de tipeo con muchos ceros y desbordes en la base


class MontoInvalido(ErrorDeNegocio):
    codigo = "monto_invalido"


class MedioInvalido(ErrorDeNegocio):
    codigo = "medio_invalido"


class CitaNoAtendida(ErrorDeNegocio):
    codigo = "cita_no_atendida"
    tipo = "conflicto"


class CitaYaCobrada(ErrorDeNegocio):
    codigo = "cita_ya_cobrada"
    tipo = "conflicto"


@dataclass(frozen=True)
class Cobro:
    id: str
    cita_id: str
    barbero_id: str  # copia de la cita: el cierre de caja no necesita volver a consultarla
    cita_inicio: datetime  # en UTC; define a qué día de caja pertenece el cobro
    monto: int
    medio: str
    registrado_en: datetime


def validar_monto(monto):
    # type() y no isinstance: bool es un int en Python y True no puede ser un monto.
    if type(monto) is not int or not 0 < monto <= MONTO_MAXIMO:
        raise MontoInvalido(f"El monto debe ser un número entero de pesos, mayor que cero y hasta {MONTO_MAXIMO}.")
    return monto


def validar_medio(medio):
    if not isinstance(medio, str) or medio not in MEDIOS:
        raise MedioInvalido("El medio de pago debe ser efectivo, tarjeta o transferencia.")
    return medio


@dataclass(frozen=True)
class Cierre:
    fecha: str
    total: int
    cantidad_de_cobros: int
    por_medio: dict
    por_barbero: dict


def armar_cierre(fecha, cobros):
    """Suma en pesos enteros; el total siempre coincide con la suma por medio y con la suma por barbero."""
    por_medio = {medio: 0 for medio in MEDIOS}
    por_barbero = {}
    for cobro in cobros:
        por_medio[cobro.medio] += cobro.monto
        por_barbero[cobro.barbero_id] = por_barbero.get(cobro.barbero_id, 0) + cobro.monto
    return Cierre(fecha=fecha.isoformat(), total=sum(por_medio.values()), cantidad_de_cobros=len(cobros),
                  por_medio=por_medio, por_barbero=por_barbero)
