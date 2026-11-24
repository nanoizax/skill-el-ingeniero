"""Rutas HTTP de las cuentas y la dependencia que identifica a quien hace cada solicitud."""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel

from app.compartido.api import direccion_del_cliente, servicios
from app.compartido.roles import Actor
from app.cuentas.dominio import SesionInvalida, Usuario

router = APIRouter()


class SolicitudDeRegistro(BaseModel):
    nombre: str
    correo: str
    contrasena: str


class SolicitudDePersonal(SolicitudDeRegistro):
    rol: str


class SolicitudDeSesion(BaseModel):
    correo: str
    contrasena: str


def _token_del_encabezado(autorizacion: Optional[str]):
    esquema, _, token = (autorizacion or "").partition(" ")
    if esquema.lower() != "bearer" or not token.strip():
        raise SesionInvalida()
    return token.strip()


def usuario_actual(autorizacion: Annotated[Optional[str], Header(alias="Authorization")] = None,
                   s=Depends(servicios)) -> Usuario:
    return s.usuario_de_sesion.ejecutar(_token_del_encabezado(autorizacion))


def actor_actual(usuario: Annotated[Usuario, Depends(usuario_actual)]) -> Actor:
    return Actor(id=usuario.id, rol=usuario.rol)


def _usuario_a_json(usuario: Usuario):
    return {"id": usuario.id, "nombre": usuario.nombre, "correo": usuario.correo, "rol": usuario.rol}


@router.post("/cuentas/clientes", status_code=201)
def registrar_cliente(solicitud: SolicitudDeRegistro, request: Request, s=Depends(servicios)):
    usuario = s.registrar_cliente.ejecutar(solicitud.nombre, solicitud.correo, solicitud.contrasena,
                                           direccion_del_cliente(request))
    return _usuario_a_json(usuario)


@router.post("/cuentas/personal", status_code=201)
def crear_personal(solicitud: SolicitudDePersonal, actor: Annotated[Actor, Depends(actor_actual)], s=Depends(servicios)):
    usuario = s.crear_personal.ejecutar(actor, solicitud.nombre, solicitud.correo, solicitud.contrasena, solicitud.rol)
    return _usuario_a_json(usuario)


@router.post("/sesion")
def iniciar_sesion(solicitud: SolicitudDeSesion, request: Request, s=Depends(servicios)):
    sesion = s.iniciar_sesion.ejecutar(solicitud.correo, solicitud.contrasena, direccion_del_cliente(request))
    return {"token": sesion.token, "tipo": "Bearer", "expira_en": sesion.expira_en.isoformat()}


@router.get("/yo")
def quien_soy(usuario: Annotated[Usuario, Depends(usuario_actual)]):
    return _usuario_a_json(usuario)
