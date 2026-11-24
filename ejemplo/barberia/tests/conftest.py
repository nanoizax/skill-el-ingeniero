"""Fixtures comunes: la aplicación armada (en memoria y con SQLite) y usuarios de prueba ya con sesión."""
import itertools
from datetime import datetime, timedelta

import pytest
from ayudas import CLAVE_DE_PRUEBA, CONTRASENA_DE_PRUEBA, Reloj
from fastapi.testclient import TestClient

from app.cuentas.dominio import Usuario
from app.cuentas.seguridad import hashear_contrasena
from app.main import crear_app

_hash_de_prueba = []
_numeros = itertools.count(1)


def hash_de_prueba():
    # scrypt es lento a propósito: se calcula una sola vez y se reutiliza en todos los usuarios de prueba.
    if not _hash_de_prueba:
        _hash_de_prueba.append(hashear_contrasena(CONTRASENA_DE_PRUEBA))
    return _hash_de_prueba[0]


class Mundo:
    """Una aplicación lista para probar por HTTP, con atajos para crear usuarios con sesión iniciada."""

    def __init__(self, app, reloj):
        self.app = app
        self.reloj = reloj
        self.http = TestClient(app, raise_server_exceptions=False)
        self.otra_direccion = TestClient(app, raise_server_exceptions=False, client=("203.0.113.9", 50000))
        self.servicios = app.state.servicios

    def usuario(self, rol, nombre=None):
        n = next(_numeros)
        usuario = Usuario(id=f"{rol}-{n}", nombre=nombre or f"{rol} {n}", correo=f"{rol}{n}@ejemplo.test",
                          rol=rol, contrasena_hash=hash_de_prueba())
        self.servicios.usuarios.guardar(usuario)
        return usuario

    def cabeceras(self, usuario):
        return {"Authorization": f"Bearer {self.servicios.emisor.emitir(usuario.id).token}"}

    def entrar(self, rol, nombre=None):
        usuario = self.usuario(rol, nombre)
        return usuario, self.cabeceras(usuario)

    def atender(self, cita, cabeceras):
        """Marca la cita como atendida con el reloj puesto un minuto después de su inicio; luego lo devuelve."""
        antes = self.reloj.ahora
        self.reloj.ahora = datetime.fromisoformat(cita["inicio"]) + timedelta(minutes=1)
        try:
            return self.http.post(f"/citas/{cita['id']}/atender", headers=cabeceras)
        finally:
            self.reloj.ahora = antes

    def agendar(self, barbero, cliente, hora=15, minuto=0, dia=1, duracion=30):
        """Agenda por HTTP como recepción y devuelve el JSON de la cita (falla si no se pudo agendar)."""
        if not hasattr(self, "_recepcion"):
            self._recepcion = self.entrar("recepcion")[1]
        inicio = f"2026-12-{dia:02d}T{hora:02d}:{minuto:02d}:00-03:00"
        cuerpo = {"barbero_id": barbero.id, "cliente_id": cliente.id, "inicio": inicio, "duracion_minutos": duracion}
        r = self.http.post("/citas", json=cuerpo, headers=self._recepcion)
        assert r.status_code == 201, r.text
        return r.json()


@pytest.fixture(params=["memoria", "sqlite"])
def mundo(request):
    reloj = Reloj()
    if request.param == "memoria":
        app = crear_app(CLAVE_DE_PRUEBA, en_memoria=True, reloj=reloj)
    else:
        app = crear_app(CLAVE_DE_PRUEBA, database_url=":memory:", reloj=reloj)
    return Mundo(app, reloj)
