"""La API de cuentas: registro, personal, sesión, /yo y los códigos 401 y 403."""
import pytest
from ayudas import CLAVE_DE_PRUEBA, CONTRASENA_DE_PRUEBA
from fastapi.testclient import TestClient

from app.compartido.errores import ConfiguracionInvalida
from app.compartido.roles import BARBERO, CLIENTE, DUENO, RECEPCION
from app.main import crear_app

REGISTRO = {"nombre": "Ana Pérez", "correo": "ana@ejemplo.test", "contrasena": CONTRASENA_DE_PRUEBA}


def registrar(mundo, **cambios):
    return mundo.http.post("/cuentas/clientes", json={**REGISTRO, **cambios})


def test_registrar_cliente_responde_201_sin_mostrar_la_contrasena(mundo):
    r = registrar(mundo)
    assert r.status_code == 201
    assert r.json()["rol"] == CLIENTE and r.json()["correo"] == "ana@ejemplo.test"
    assert "contrasena" not in r.text and "scrypt" not in r.text


def test_registrar_dos_veces_el_mismo_correo_responde_409(mundo):
    registrar(mundo)
    r = registrar(mundo, nombre="Otra")
    assert r.status_code == 409 and r.json()["error"] == "correo_ya_registrado"


def test_solicitud_con_datos_invalidos_se_rechaza(mundo):
    casos = [
        {"nombre": "Ana"},  # cuerpo incompleto
        {},  # cuerpo vacío
        {**REGISTRO, "contrasena": "corta123"},  # contraseña corta  # pragma: allowlist secret
        {**REGISTRO, "correo": "no-es-un-correo"},
        {**REGISTRO, "nombre": "   "},
    ]
    for cuerpo in casos:
        r = mundo.http.post("/cuentas/clientes", json=cuerpo)
        assert r.status_code == 422, cuerpo
        assert r.json()["error"] in {"datos_invalidos", "contrasena_debil"}
        assert CONTRASENA_DE_PRUEBA not in r.text
    assert mundo.servicios.usuarios.por_correo("ana@ejemplo.test") is None  # nada quedó guardado


def test_iniciar_sesion_y_ver_mis_datos(mundo):
    registrar(mundo)
    r = mundo.http.post("/sesion", json={"correo": "ana@ejemplo.test", "contrasena": CONTRASENA_DE_PRUEBA})
    assert r.status_code == 200 and r.json()["token"].count(".") == 2
    yo = mundo.http.get("/yo", headers={"Authorization": f"Bearer {r.json()['token']}"})
    assert yo.status_code == 200
    assert yo.json()["correo"] == "ana@ejemplo.test" and yo.json()["rol"] == CLIENTE
    assert "contrasena_hash" not in yo.text


def test_credenciales_malas_responden_401_con_el_mismo_mensaje(mundo):
    registrar(mundo)
    a = mundo.http.post("/sesion", json={"correo": "nadie@ejemplo.test", "contrasena": CONTRASENA_DE_PRUEBA})
    mala = {"correo": "ana@ejemplo.test", "contrasena": "contrasena-equivocada"}  # pragma: allowlist secret
    b = mundo.http.post("/sesion", json=mala)
    assert a.status_code == b.status_code == 401
    assert a.json() == b.json() and a.json()["mensaje"] == "Correo o contraseña incorrectos"


def test_el_sexto_intento_por_http_responde_429(mundo):
    registrar(mundo)
    malo = {"correo": "ana@ejemplo.test", "contrasena": "contrasena-equivocada"}  # pragma: allowlist secret
    assert [mundo.http.post("/sesion", json=malo).status_code for _ in range(6)] == [401] * 5 + [429]


@pytest.mark.parametrize("cabecera", [None, "", "Bearer", "Bearer ", "Basic abc", "Bearer basura", "token-suelto"])
def test_yo_sin_sesion_valida_responde_401(mundo, cabecera):
    cabeceras = {} if cabecera is None else {"Authorization": cabecera}
    r = mundo.http.get("/yo", headers=cabeceras)
    assert r.status_code == 401 and r.json()["error"] == "sesion_invalida"


def test_un_token_vencido_responde_401(mundo):
    _, cabeceras = mundo.entrar(CLIENTE)
    assert mundo.http.get("/yo", headers=cabeceras).status_code == 200
    mundo.reloj.avanzar(hours=8, seconds=1)
    assert mundo.http.get("/yo", headers=cabeceras).status_code == 401


def test_un_token_alterado_responde_401(mundo):
    _, cabeceras = mundo.entrar(CLIENTE)
    token = cabeceras["Authorization"].split(" ")[1]
    ultimo = "0" if token[-1] != "0" else "1"
    r = mundo.http.get("/yo", headers={"Authorization": f"Bearer {token[:-1]}{ultimo}"})
    assert r.status_code == 401


def crear_personal(mundo, cabeceras, rol=BARBERO, correo="luis@ejemplo.test"):
    cuerpo = {"nombre": "Luis", "correo": correo, "contrasena": CONTRASENA_DE_PRUEBA, "rol": rol}
    return mundo.http.post("/cuentas/personal", json=cuerpo, headers=cabeceras)


def test_el_dueno_crea_personal_con_201(mundo):
    _, cabeceras = mundo.entrar(DUENO)
    r = crear_personal(mundo, cabeceras, rol=RECEPCION)
    assert r.status_code == 201 and r.json()["rol"] == RECEPCION


@pytest.mark.parametrize("rol", [RECEPCION, BARBERO, CLIENTE])
def test_los_demas_roles_no_crean_personal_y_responden_403(mundo, rol):
    _, cabeceras = mundo.entrar(rol)
    r = crear_personal(mundo, cabeceras)
    assert r.status_code == 403 and r.json()["error"] == "no_autorizado"


def test_crear_personal_sin_sesion_responde_401(mundo):
    assert crear_personal(mundo, {}).status_code == 401


@pytest.mark.parametrize("rol", [DUENO, CLIENTE, "admin"])
def test_el_personal_con_rol_invalido_responde_422(mundo, rol):
    _, cabeceras = mundo.entrar(DUENO)
    assert crear_personal(mundo, cabeceras, rol=rol).status_code == 422


def test_crear_app_sin_clave_falla_con_un_mensaje_claro(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)  # pragma: allowlist secret
    with pytest.raises(ConfiguracionInvalida, match="SECRET_KEY"):  # pragma: allowlist secret
        crear_app(en_memoria=True)


def test_crear_app_toma_la_clave_de_la_variable_de_entorno(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", CLAVE_DE_PRUEBA)  # pragma: allowlist secret
    assert TestClient(crear_app(en_memoria=True)).get("/health").status_code == 200


def test_crear_app_sin_base_de_datos_falla_salvo_que_se_pida_memoria(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ConfiguracionInvalida, match="DATABASE_URL"):
        crear_app(CLAVE_DE_PRUEBA)
