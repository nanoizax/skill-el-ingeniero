from ayudas import CLAVE_DE_PRUEBA
from fastapi.testclient import TestClient

from app.main import crear_app


def test_el_punto_de_salud_responde_ok_sin_pedir_sesion():
    r = TestClient(crear_app(CLAVE_DE_PRUEBA, en_memoria=True)).get("/health")
    assert r.status_code == 200
    assert r.json() == {"estado": "ok"}
