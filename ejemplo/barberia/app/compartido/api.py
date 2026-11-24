"""Piezas comunes de la capa HTTP: acceso a los servicios y traducción de errores a respuestas JSON."""
import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as ErrorHttp

from app.compartido.errores import ErrorDeNegocio
from app.compartido.limites import clave_de_direccion

registro = logging.getLogger("barberia")

ESTADO_POR_TIPO = {
    "invalido": 422,
    "no_autenticado": 401,
    "prohibido": 403,
    "no_encontrado": 404,
    "conflicto": 409,
    "limite": 429,
}


def servicios(request: Request):
    return request.app.state.servicios


def direccion_del_cliente(request: Request):
    """La dirección de la conexión. No se lee X-Forwarded-For: cualquiera puede escribir esa cabecera."""
    return clave_de_direccion(request.client.host if request.client else None)


def respuesta_de_error_http(_, error: ErrorHttp):
    if error.status_code == 404:
        contenido = {"error": "no_encontrado", "mensaje": "No encontramos lo que buscas."}
    elif error.status_code == 405:
        contenido = {"error": "metodo_no_permitido", "mensaje": "Esa ruta no acepta este método."}
    else:
        contenido = {"error": "error_http", "mensaje": "No pudimos atender la solicitud."}
    return JSONResponse(status_code=error.status_code, content=contenido, headers=error.headers)


def respuesta_de_error_de_negocio(_, error: ErrorDeNegocio):
    estado = ESTADO_POR_TIPO.get(error.tipo, 422)
    cabeceras = {"WWW-Authenticate": "Bearer"} if estado == 401 else None
    contenido = {"error": error.codigo, "mensaje": error.mensaje}
    return JSONResponse(status_code=estado, content=contenido, headers=cabeceras)


def respuesta_de_datos_invalidos(_, error: RequestValidationError):
    # Solo se nombran los campos; nunca se devuelve lo que la persona escribió (podría ser una contraseña).
    campos = sorted({".".join(str(parte) for parte in e["loc"][1:]) or "cuerpo" for e in error.errors()})
    contenido = {"error": "datos_invalidos", "mensaje": "Revisa los datos enviados.", "campos": campos}
    return JSONResponse(status_code=422, content=contenido)


def respuesta_de_error_interno(_, error):
    # El detalle real queda en los registros del servidor; a la persona solo se le dice que algo falló.
    registro.error("Error inesperado", exc_info=error)
    contenido = {"error": "error_interno", "mensaje": "Ocurrió un error. Intenta de nuevo."}
    return JSONResponse(status_code=500, content=contenido)
