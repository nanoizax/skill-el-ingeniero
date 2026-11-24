"""Rutas HTTP de los cobros y del cierre de caja."""
from dataclasses import asdict
from typing import Annotated, Any, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.compartido.api import servicios
from app.compartido.roles import Actor
from app.cuentas.api import actor_actual

router = APIRouter()


class SolicitudDeCobro(BaseModel):
    # Se reciben sin tipo para que el dominio decida (rechaza decimales, texto y booleanos con un mensaje claro).
    monto: Any = None
    medio: Any = None


def cobro_a_json(cobro):
    return {"id": cobro.id, "cita_id": cobro.cita_id, "monto": cobro.monto, "medio": cobro.medio}


@router.post("/citas/{cita_id}/cobro", status_code=201)
def registrar_cobro(cita_id: str, solicitud: SolicitudDeCobro, actor: Annotated[Actor, Depends(actor_actual)],
                    s=Depends(servicios)):
    return cobro_a_json(s.registrar_cobro.ejecutar(actor, cita_id, solicitud.monto, solicitud.medio))


@router.get("/caja")
def cierre_de_caja(actor: Annotated[Actor, Depends(actor_actual)], fecha: Annotated[Optional[str], Query()] = None,
                   s=Depends(servicios)):
    return asdict(s.cierre_de_caja.ejecutar(actor, fecha))
