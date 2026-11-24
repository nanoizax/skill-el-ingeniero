"""Configuración al arrancar: clave larga, documentación apagada por defecto y errores con el mismo formato."""
import pytest
from ayudas import CLAVE_DE_PRUEBA
from fastapi.testclient import TestClient

from app.compartido.errores import ConfiguracionInvalida
from app.main import crear_app

RUTAS_DE_DOCUMENTACION = ["/docs", "/redoc", "/openapi.json"]


def cliente(monkeypatch, docs=None):
    if docs is None:
        monkeypatch.delenv("DOCS_ACTIVAS", raising=False)
    else:
        monkeypatch.setenv("DOCS_ACTIVAS", docs)
    return TestClient(crear_app(CLAVE_DE_PRUEBA, en_memoria=True), raise_server_exceptions=False)


def test_una_clave_de_menos_de_32_caracteres_impide_arrancar():
    corta = "k" * 31  # pragma: allowlist secret
    with pytest.raises(ConfiguracionInvalida, match="32 caracteres"):
        crear_app(corta, en_memoria=True)
    assert crear_app("k" * 32, en_memoria=True)  # límite: 32 sí sirve  # pragma: allowlist secret


def test_la_clave_corta_tambien_se_rechaza_si_viene_del_entorno(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "corta")  # pragma: allowlist secret
    with pytest.raises(ConfiguracionInvalida, match="SECRET_KEY"):  # pragma: allowlist secret
        crear_app(en_memoria=True)


@pytest.mark.parametrize("ruta", RUTAS_DE_DOCUMENTACION)
def test_la_documentacion_esta_apagada_por_defecto(monkeypatch, ruta):
    r = cliente(monkeypatch).get(ruta)
    assert r.status_code == 404 and r.json()["error"] == "no_encontrado"


@pytest.mark.parametrize("valor", ["no", "SI ", "true", "1", ""])
def test_solo_el_valor_si_activa_la_documentacion(monkeypatch, valor):
    assert cliente(monkeypatch, valor).get("/openapi.json").status_code == 404


@pytest.mark.parametrize("ruta", RUTAS_DE_DOCUMENTACION)
def test_docs_activas_si_enciende_la_documentacion(monkeypatch, ruta):
    assert cliente(monkeypatch, "si").get(ruta).status_code == 200


def test_una_ruta_inexistente_responde_404_con_el_formato_de_error(monkeypatch):
    r = cliente(monkeypatch).get("/no-existe")
    assert r.status_code == 404
    assert r.json() == {"error": "no_encontrado", "mensaje": "No encontramos lo que buscas."}


def test_un_metodo_no_permitido_responde_405_con_el_formato_de_error(monkeypatch):
    http = cliente(monkeypatch)
    for metodo, ruta in (("get", "/sesion"), ("post", "/yo"), ("delete", "/health")):
        r = getattr(http, metodo)(ruta)
        assert r.status_code == 405 and r.json()["error"] == "metodo_no_permitido" and "mensaje" in r.json()
        assert r.headers["allow"]
