"""Rutas HTTP de las citas. Toda la lógica vive en los casos de uso; aquí solo se traduce lo que entra y sale."""
from datetime import datetime
from typing import Annotated, Any, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.citas.dominio import ZONA
from app.compartido.api import servicios
from app.compartido.roles import Actor
from app.cuentas.api import actor_actual

router = APIRouter()


class SolicitudDeCita(BaseModel):
    barbero_id: str
    cliente_id: Optional[str] = None  # solo lo usan recepción y dueño; al cliente se le ignora
    inicio: datetime
    duracion_minutos: Any = None  # sin tipo: el dominio rechaza decimales, texto y booleanos con un mensaje claro


def cita_a_json(cita):
    """Las horas se guardan en UTC y se muestran en la zona del negocio."""
    return {"id": cita.id, "barbero_id": cita.barbero_id, "cliente_id": cita.cliente_id,
            "inicio": cita.inicio.astimezone(ZONA).isoformat(), "fin": cita.fin.astimezone(ZONA).isoformat(),
            "estado": cita.estado}


@router.post("/citas", status_code=201)
def agendar(solicitud: SolicitudDeCita, actor: Annotated[Actor, Depends(actor_actual)], s=Depends(servicios)):
    cita = s.agendar_cita.ejecutar(actor, solicitud.barbero_id, solicitud.cliente_id, solicitud.inicio,
                                   solicitud.duracion_minutos)
    return cita_a_json(cita)


class SolicitudDeMovimiento(BaseModel):
    inicio: datetime


@router.post("/citas/{cita_id}/cancelar")
def cancelar(cita_id: str, actor: Annotated[Actor, Depends(actor_actual)], s=Depends(servicios)):
    return cita_a_json(s.cancelar_cita.ejecutar(actor, cita_id))


@router.post("/citas/{cita_id}/mover")
def mover(cita_id: str, solicitud: SolicitudDeMovimiento, actor: Annotated[Actor, Depends(actor_actual)],
          s=Depends(servicios)):
    return cita_a_json(s.mover_cita.ejecutar(actor, cita_id, solicitud.inicio))


@router.post("/citas/{cita_id}/atender")
def atender(cita_id: str, actor: Annotated[Actor, Depends(actor_actual)], s=Depends(servicios)):
    return cita_a_json(s.marcar_atendida.ejecutar(actor, cita_id))


@router.get("/agenda")
def ver_agenda(actor: Annotated[Actor, Depends(actor_actual)], fecha: Annotated[Optional[str], Query()] = None,
               barbero_id: Annotated[Optional[str], Query()] = None, s=Depends(servicios)):
    return [cita_a_json(c) for c in s.ver_agenda.ejecutar(actor, fecha, barbero_id)]


@router.get("/mis-citas")
def ver_mis_citas(actor: Annotated[Actor, Depends(actor_actual)], s=Depends(servicios)):
    return [cita_a_json(c) for c in s.ver_mis_citas.ejecutar(actor)]
