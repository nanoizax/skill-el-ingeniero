"""Punto de entrada de la aplicación. Se arranca con: uvicorn app.main:crear_app --factory"""
import os

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as ErrorHttp

from app.citas.api import router as router_de_citas
from app.cobros.api import router as router_de_cobros
from app.compartido.api import (
    respuesta_de_datos_invalidos,
    respuesta_de_error_de_negocio,
    respuesta_de_error_http,
    respuesta_de_error_interno,
)
from app.compartido.errores import ConfiguracionInvalida, ErrorDeNegocio
from app.composicion import construir_servicios
from app.cuentas.api import router as router_de_cuentas

LARGO_MINIMO_DE_CLAVE = 32


def crear_app(secret_key=None, database_url=None, en_memoria=False, reloj=None, docs_activas=None):
    """Arma la aplicación. Las pruebas pasan la clave como argumento y piden memoria o una base explícita."""
    clave = secret_key or os.environ.get("SECRET_KEY")
    if not clave:
        raise ConfiguracionInvalida("Falta la variable de entorno SECRET_KEY: es la clave con que se firman las sesiones.")
    if len(clave) < LARGO_MINIMO_DE_CLAVE:
        raise ConfiguracionInvalida(f"SECRET_KEY debe tener al menos {LARGO_MINIMO_DE_CLAVE} caracteres; "
                                    "usa una clave larga y al azar.")
    if docs_activas is None:
        docs_activas = os.environ.get("DOCS_ACTIVAS") == "si"  # apagadas por defecto: no se publica el mapa de la API
    app = FastAPI(title="Barbería Don Mario", docs_url="/docs" if docs_activas else None,
                  redoc_url="/redoc" if docs_activas else None,
                  openapi_url="/openapi.json" if docs_activas else None)
    app.state.servicios = construir_servicios(clave, database_url, en_memoria, reloj)
    app.include_router(router_de_cuentas)
    app.include_router(router_de_citas)
    app.include_router(router_de_cobros)
    app.add_exception_handler(ErrorDeNegocio, respuesta_de_error_de_negocio)
    app.add_exception_handler(ErrorHttp, respuesta_de_error_http)
    app.add_exception_handler(RequestValidationError, respuesta_de_datos_invalidos)
    app.add_exception_handler(Exception, respuesta_de_error_interno)

    @app.get("/health")
    def salud():
        return {"estado": "ok"}

    return app
