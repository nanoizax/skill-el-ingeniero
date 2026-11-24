"""El flujo completo sobre SQLite en archivo, y el script que crea al primer dueño."""
import sqlite3

from ayudas import CLAVE_DE_PRUEBA, CONTRASENA_DE_PRUEBA, Reloj, a_las
from fastapi.testclient import TestClient

from app.main import crear_app
from scripts import crear_dueno


def entrar(http, correo, contrasena=CONTRASENA_DE_PRUEBA):
    r = http.post("/sesion", json={"correo": correo, "contrasena": contrasena})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_flujo_principal_de_punta_a_punta(tmp_path):
    ruta = tmp_path / "barberia.db"
    url = f"sqlite:///{ruta}"
    reloj = Reloj()
    http = TestClient(crear_app(CLAVE_DE_PRUEBA, database_url=url, reloj=reloj), raise_server_exceptions=False)
    crear_dueno.crear_dueno(url, "Don Mario", "mario@ejemplo.test", CONTRASENA_DE_PRUEBA)

    # El dueño inicia sesión y da de alta a un barbero.
    dueno = entrar(http, "mario@ejemplo.test")
    r = http.post("/cuentas/personal", headers=dueno, json={
        "nombre": "Luis Barbero", "correo": "luis@ejemplo.test", "contrasena": CONTRASENA_DE_PRUEBA, "rol": "barbero"})
    assert r.status_code == 201
    barbero = entrar(http, "luis@ejemplo.test")
    barbero_id = http.get("/yo", headers=barbero).json()["id"]

    # Un cliente se registra, inicia sesión y agenda para mañana en la tarde.
    assert http.post("/cuentas/clientes", json={
        "nombre": "Ana Cliente", "correo": "ana@ejemplo.test", "contrasena": CONTRASENA_DE_PRUEBA}).status_code == 201
    cliente = entrar(http, "ana@ejemplo.test")
    cita = http.post("/citas", headers=cliente, json={
        "barbero_id": barbero_id, "inicio": "2026-12-01T15:00:00-03:00", "duracion_minutos": 30})
    assert cita.status_code == 201 and cita.json()["estado"] == "confirmada"
    cita_id = cita.json()["id"]

    # El barbero ve su agenda, atiende y cobra.
    agenda = http.get("/agenda", params={"fecha": "2026-12-01"}, headers=barbero).json()
    assert [c["id"] for c in agenda] == [cita_id]
    reloj.ahora = a_las(15, 1)  # ya pasó la hora de la cita
    assert http.post(f"/citas/{cita_id}/atender", headers=barbero).json()["estado"] == "atendida"
    cobro = http.post(f"/citas/{cita_id}/cobro", headers=barbero, json={"monto": 15000, "medio": "tarjeta"})
    assert cobro.status_code == 201 and cobro.json()["monto"] == 15000

    # El dueño cierra la caja; el cliente ve su cita atendida.
    cierre = http.get("/caja", params={"fecha": "2026-12-01"}, headers=dueno).json()
    assert cierre["total"] == 15000 and cierre["por_medio"]["tarjeta"] == 15000
    assert cierre["por_barbero"] == {barbero_id: 15000} and cierre["cantidad_de_cobros"] == 1
    assert [c["estado"] for c in http.get("/mis-citas", headers=cliente).json()] == ["atendida"]
    assert http.get("/caja", params={"fecha": "2026-12-01"}, headers=barbero).status_code == 403

    # Lo que quedó en el archivo SQLite: una cita, un cobro y contraseñas que no están en texto.
    c = sqlite3.connect(ruta)
    assert c.execute("SELECT count(*) FROM citas").fetchone() == (1,)
    assert c.execute("SELECT monto, medio FROM cobros").fetchone() == (15000, "tarjeta")
    hashes = [h for (h,) in c.execute("SELECT contrasena_hash FROM usuarios")]
    c.close()
    assert len(hashes) == 3 and all(h.startswith("scrypt$") and CONTRASENA_DE_PRUEBA not in h for h in hashes)


def test_crear_dueno_por_la_linea_de_comandos(tmp_path, capsys):
    url = f"sqlite:///{tmp_path / 'b.db'}"
    entorno = {"DATABASE_URL": url, "DUENO_CONTRASENA": CONTRASENA_DE_PRUEBA}  # pragma: allowlist secret
    assert crear_dueno.main(["Don Mario", "mario@ejemplo.test"], entorno) == 0
    http = TestClient(crear_app(CLAVE_DE_PRUEBA, database_url=entorno["DATABASE_URL"]))
    assert http.get("/yo", headers=entrar(http, "mario@ejemplo.test")).json()["rol"] == "dueno"
    assert CONTRASENA_DE_PRUEBA not in capsys.readouterr().out  # nunca se imprime la contraseña
    assert crear_dueno.main(["Otro", "mario@ejemplo.test"], entorno) == 1  # correo repetido
    assert "ya tiene una cuenta" in capsys.readouterr().err


def test_crear_dueno_pide_la_contrasena_si_no_viene_en_el_entorno(tmp_path):
    entorno = {"DATABASE_URL": f"sqlite:///{tmp_path / 'b.db'}"}
    clave_corta = "corta"  # pragma: allowlist secret
    assert crear_dueno.main(["Don Mario", "mario@ejemplo.test"], entorno, pedir=lambda _: clave_corta) == 1
    assert crear_dueno.main(["Don Mario", "mario@ejemplo.test"], entorno, pedir=lambda _: CONTRASENA_DE_PRUEBA) == 0
    assert crear_dueno.main(["Don Mario", "x@ejemplo.test"], {}, pedir=lambda _: CONTRASENA_DE_PRUEBA) == 1  # sin base
