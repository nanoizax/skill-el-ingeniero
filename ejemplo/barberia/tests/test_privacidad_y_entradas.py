"""Segunda revisión: restos del nombre en el archivo, direcciones IPv6 equivalentes y caracteres invisibles."""
import json
import sqlite3
from pathlib import Path

import pytest
from ayudas import CLAVE_DE_PRUEBA, CONTRASENA_DE_PRUEBA
from fastapi.testclient import TestClient

from app.compartido.db import BaseDeDatos
from app.compartido.errores import DatosInvalidos
from app.compartido.limites import clave_de_direccion
from app.compartido.roles import BARBERO, CLIENTE, DUENO, RECEPCION
from app.compartido.validacion import id_valido, texto_valido
from app.main import crear_app
from scripts import anonimizar_cliente

NOMBRE = "Zoraida Xochitlquetzal Ñandú-Quispe Ficticiamente Irrepetible"
CORREO = "zoraida.xochitlquetzal.irrepetible@ejemplo.test"
JSON = {"content-type": "application/json"}


def hacer_checkpoint(ruta):
    c = sqlite3.connect(ruta, isolation_level=None)
    try:
        c.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchall()
    finally:
        c.close()


def bytes_del_archivo(ruta):
    """Lo que hay en el .db y en el -wal (si existe), tal cual está en disco."""
    ruta = Path(ruta)
    wal = ruta.with_name(ruta.name + "-wal")
    return ruta.read_bytes(), (wal.read_bytes() if wal.exists() else b"")


# ---------- 1. restos del nombre en el archivo ----------

def crear_clienta(tmp_path):
    ruta = tmp_path / "barberia.db"
    url = f"sqlite:///{ruta}"
    app = crear_app(CLAVE_DE_PRUEBA, database_url=url)
    app.state.servicios.registrar_cliente.ejecutar(NOMBRE, CORREO, CONTRASENA_DE_PRUEBA)
    for i in range(30):  # otras cuentas, para que las páginas de la base tengan movimiento
        app.state.servicios.registrar_cliente.ejecutar(f"Otra Persona {i}", f"otra{i}@ejemplo.test", CONTRASENA_DE_PRUEBA)
    return ruta, url


def test_tras_anonimizar_el_nombre_y_el_correo_ya_no_estan_en_el_archivo(tmp_path, capsys):
    ruta, url = crear_clienta(tmp_path)
    hacer_checkpoint(ruta)
    antes = b"".join(bytes_del_archivo(ruta))
    assert NOMBRE.encode() in antes and CORREO.encode() in antes  # antes de anonimizar los datos sí estaban

    assert anonimizar_cliente.main([CORREO], {"DATABASE_URL": url}) == 0
    hacer_checkpoint(ruta)
    base, wal = bytes_del_archivo(ruta)
    for archivo, contenido in ((".db", base), ("-wal", wal)):
        for dato in (NOMBRE, CORREO, NOMBRE[:14], "xochitlquetzal", "Quispe", "irrepetible"):
            assert dato.encode() not in contenido, f"quedó {dato!r} en el archivo {archivo}"
    assert b"Cliente anonimizado" in base  # y la cuenta sigue ahí, ya sin datos personales
    assert "Cliente anonimizado" in capsys.readouterr().out


def test_la_conexion_borra_de_forma_segura(tmp_path):
    base = BaseDeDatos(f"sqlite:///{tmp_path / 'b.db'}")
    with base.conexion() as c:
        assert c.execute("PRAGMA secure_delete").fetchone() == (1,)
    memoria = BaseDeDatos(":memory:")
    with memoria.conexion() as c:
        assert c.execute("PRAGMA secure_delete").fetchone() == (1,)


def test_compactar_deja_claro_si_otra_conexion_esta_escribiendo(tmp_path):
    ruta, url = crear_clienta(tmp_path)
    ocupada = sqlite3.connect(ruta, isolation_level=None)
    ocupada.execute("BEGIN IMMEDIATE")  # otra conexión escribiendo: el VACUUM no puede correr
    try:
        with pytest.raises(anonimizar_cliente.CompactacionIncompleta, match="VACUUM"):
            anonimizar_cliente.compactar(url, espera=0.2)
    finally:
        ocupada.execute("ROLLBACK")
        ocupada.close()
    anonimizar_cliente.compactar(url, espera=0.2)  # liberada la base, sí puede


def test_si_no_se_puede_compactar_el_script_avisa_pero_la_cuenta_ya_quedo_anonimizada(tmp_path, monkeypatch, capsys):
    ruta, url = crear_clienta(tmp_path)

    def bloqueada(*args, **kwargs):
        raise anonimizar_cliente.CompactacionIncompleta("otra conexión está escribiendo; ejecuta VACUUM más tarde")
    monkeypatch.setattr(anonimizar_cliente, "compactar", bloqueada)
    assert anonimizar_cliente.main([CORREO], {"DATABASE_URL": url}) == 2  # código propio: anonimizó, falta compactar
    error = capsys.readouterr().err
    assert "VACUUM" in error and CORREO not in error and NOMBRE not in error
    app = crear_app(CLAVE_DE_PRUEBA, database_url=url)
    assert app.state.servicios.usuarios.por_correo(CORREO) is None  # la anonimización sí se hizo


def test_compactar_una_base_en_memoria_no_hace_nada():
    anonimizar_cliente.compactar(":memory:")


# ---------- 2. direcciones IPv6 equivalentes ----------

@pytest.mark.parametrize("a,b", [
    ("203.0.113.5", "::ffff:203.0.113.5"),
    ("203.0.113.5", "::FFFF:203.0.113.5"),
    ("203.0.113.5", "::ffff:cb00:7105"),
    ("2001:DB8:0:0:0:0:0:1", "2001:db8::1"),
    ("2001:0db8:0000:0000:0000:0000:0000:0001", "2001:db8::1"),
    ("fe80::1%eth0", "fe80::1"),
])
def test_las_direcciones_equivalentes_comparten_clave(a, b):
    assert clave_de_direccion(a) == clave_de_direccion(b)


def test_direcciones_distintas_no_comparten_clave_y_lo_raro_se_conserva():
    assert clave_de_direccion("203.0.113.5") != clave_de_direccion("203.0.113.6")
    assert clave_de_direccion("2001:db8::1") != clave_de_direccion("2001:db8::2")
    assert clave_de_direccion("testclient") == "testclient"  # no es una IP: se usa tal cual
    assert clave_de_direccion("") == "desconocida" and clave_de_direccion(None) == "desconocida"


def test_203_0_113_5_y_su_forma_ipv6_comparten_el_mismo_contador(mundo):
    como_ipv4 = TestClient(mundo.app, raise_server_exceptions=False, client=("203.0.113.5", 40000))
    como_ipv6 = TestClient(mundo.app, raise_server_exceptions=False, client=("::ffff:203.0.113.5", 40001))

    def registrar(http, n):
        cuerpo = {"nombre": "Ana", "correo": f"c{n}@ejemplo.test", "contrasena": CONTRASENA_DE_PRUEBA}
        return http.post("/cuentas/clientes", content=json.dumps(cuerpo), headers=JSON)
    estados = [registrar(como_ipv4 if n % 2 == 0 else como_ipv6, n).status_code for n in range(10)]
    assert estados == [201] * 10  # entre las dos escrituras suman 10
    assert registrar(como_ipv4, 10).status_code == 429
    assert registrar(como_ipv6, 11).status_code == 429  # la otra forma de la misma IP también está bloqueada
    assert registrar(mundo.otra_direccion, 12).status_code == 201  # otra dirección real no se afecta


# ---------- 3. caracteres invisibles de formato (categoría Cf) ----------

INVISIBLES = [chr(c) for c in (*range(0x202A, 0x202F), *range(0x2066, 0x206A), *range(0x200B, 0x2010))]
INVISIBLES += ["­", "﻿", "⁠"]  # guion blando, marca de orden de bytes, unión de palabras


def enviar(mundo, ruta, datos, cabeceras=None):
    return mundo.http.post(ruta, content=json.dumps(datos), headers={**JSON, **(cabeceras or {})})


@pytest.mark.parametrize("invisible", INVISIBLES, ids=lambda c: f"U+{ord(c):04X}")
def test_el_registro_rechaza_caracteres_invisibles_en_nombre_y_correo(mundo, invisible):
    base = {"nombre": "Ana Pérez", "correo": "ana@ejemplo.test", "contrasena": CONTRASENA_DE_PRUEBA}
    for campo, valor in (("nombre", "Ana" + invisible + "Pérez"), ("nombre", invisible + "Ana"),
                         ("correo", "an" + invisible + "a@ejemplo.test")):
        r = enviar(mundo, "/cuentas/clientes", {**base, campo: valor})
        assert r.status_code == 422 and r.json()["error"] == "datos_invalidos", (campo, f"U+{ord(invisible):04X}")
    assert mundo.servicios.usuarios.por_correo("ana@ejemplo.test") is None


@pytest.mark.parametrize("invisible", ["‮", "​", "⁦", "‏"])
def test_los_ids_rechazan_caracteres_invisibles(mundo, invisible):
    barbero = mundo.usuario(BARBERO)
    cliente, h_cliente = mundo.entrar(CLIENTE)
    _, h_recepcion = mundo.entrar(RECEPCION)
    cita = {"inicio": "2026-12-01T15:00:00-03:00", "duracion_minutos": 30}
    r = enviar(mundo, "/citas", {**cita, "barbero_id": barbero.id + invisible}, h_cliente)
    assert r.status_code == 422 and r.json()["error"] == "datos_invalidos"
    r = enviar(mundo, "/citas", {**cita, "barbero_id": barbero.id, "cliente_id": cliente.id + invisible}, h_recepcion)
    assert r.status_code == 422 and r.json()["error"] == "datos_invalidos"
    r = mundo.http.post(f"/citas/abc{invisible}/cancelar", headers=h_recepcion)
    assert r.status_code == 422 and r.json()["error"] == "datos_invalidos"


def test_el_inicio_de_sesion_rechaza_un_correo_con_caracteres_invisibles(mundo):
    r = enviar(mundo, "/sesion", {"correo": "ana‮@ejemplo.test", "contrasena": CONTRASENA_DE_PRUEBA})
    assert r.status_code == 422 and r.json()["error"] == "datos_invalidos"


def test_el_personal_tampoco_puede_tener_un_nombre_con_caracteres_invisibles(mundo):
    _, dueno = mundo.entrar(DUENO)
    r = enviar(mundo, "/cuentas/personal", {"nombre": "Luis‮", "correo": "luis@ejemplo.test",
                                            "contrasena": CONTRASENA_DE_PRUEBA, "rol": "barbero"}, dueno)
    assert r.status_code == 422 and r.json()["error"] == "datos_invalidos"


@pytest.mark.parametrize("invisible", INVISIBLES[:6])
def test_texto_valido_y_id_valido_rechazan_los_invisibles(invisible):
    with pytest.raises(DatosInvalidos):
        texto_valido("a" + invisible + "b", "El nombre", 50)
    with pytest.raises(DatosInvalidos):
        id_valido("id" + invisible)


def test_el_texto_normal_con_tildes_y_enes_sigue_valiendo():
    assert texto_valido("José Ñandú Pérez-Muñoz", "El nombre", 50) == "José Ñandú Pérez-Muñoz"


def test_la_contrasena_si_puede_llevar_emojis_con_union_de_ancho_cero(mundo):
    familia = "familia-\U0001F468‍\U0001F469‍\U0001F467-123"  # la unión U+200D es de categoría Cf
    cuerpo = {"nombre": "Ana", "correo": "ana@ejemplo.test", "contrasena": familia}  # pragma: allowlist secret
    assert enviar(mundo, "/cuentas/clientes", cuerpo).status_code == 201
    entrada = {"correo": "ana@ejemplo.test", "contrasena": familia}  # pragma: allowlist secret
    assert enviar(mundo, "/sesion", entrada).status_code == 200

