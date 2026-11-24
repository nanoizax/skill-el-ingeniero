"""Borrado a pedido: anonimizar a un cliente conserva citas y cobros pero sin datos personales."""
import sqlite3

import pytest
from ayudas import CLAVE_DE_PRUEBA, CONTRASENA_DE_PRUEBA, Reloj, a_las
from fastapi.testclient import TestClient

from app.compartido.errores import DatosInvalidos
from app.compartido.roles import BARBERO, CLIENTE
from app.cuentas.casos_de_uso import AnonimizarCliente, RegistrarCliente
from app.cuentas.dominio import UsuarioNoEncontrado
from app.cuentas.repositorio import RepositorioDeUsuariosEnMemoria
from app.cuentas.seguridad import hashear_contrasena, verificar_contrasena
from app.main import crear_app
from scripts import anonimizar_cliente

NOMBRE = "Ana Pérez Ficticia"
CORREO = "ana.ficticia@ejemplo.test"


def volcar_texto(ruta):
    """Todo el texto de todas las celdas de la base, para buscar datos personales."""
    c = sqlite3.connect(ruta)
    try:
        tablas = [n for (n,) in c.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]
        return [str(celda) for t in tablas for fila in c.execute(f"SELECT * FROM {t}") for celda in fila]
    finally:
        c.close()


@pytest.fixture
def escena(tmp_path):
    """Una base en archivo con un cliente que tuvo una cita atendida y cobrada."""
    ruta = tmp_path / "barberia.db"
    url = f"sqlite:///{ruta}"
    reloj = Reloj()
    app = crear_app(CLAVE_DE_PRUEBA, database_url=url, reloj=reloj)
    http = TestClient(app, raise_server_exceptions=False)
    servicios = app.state.servicios
    r = http.post("/cuentas/clientes", json={"nombre": NOMBRE, "correo": CORREO, "contrasena": CONTRASENA_DE_PRUEBA})
    cliente_id = r.json()["id"]
    sesion = http.post("/sesion", json={"correo": CORREO, "contrasena": CONTRASENA_DE_PRUEBA}).json()["token"]
    from app.cuentas.dominio import Usuario
    barbero = Usuario("barbero-1", "Luis Barbero", "luis@ejemplo.test", BARBERO, hashear_contrasena(CONTRASENA_DE_PRUEBA))
    servicios.usuarios.guardar(barbero)
    cabeceras_barbero = {"Authorization": f"Bearer {servicios.emisor.emitir(barbero.id).token}"}
    cita = http.post("/citas", headers={"Authorization": f"Bearer {sesion}"}, json={
        "barbero_id": barbero.id, "inicio": "2026-12-01T15:00:00-03:00", "duracion_minutos": 30}).json()
    reloj.ahora = a_las(15, 1)
    assert http.post(f"/citas/{cita['id']}/atender", headers=cabeceras_barbero).status_code == 200
    assert http.post(f"/citas/{cita['id']}/cobro", headers=cabeceras_barbero,
                     json={"monto": 12000, "medio": "efectivo"}).status_code == 201
    return {"ruta": ruta, "url": url, "http": http, "cliente_id": cliente_id, "token": sesion, "cita": cita,
            "servicios": servicios}


def contar(ruta, tabla):
    c = sqlite3.connect(ruta)
    try:
        return c.execute(f"SELECT count(*) FROM {tabla}").fetchone()[0]
    finally:
        c.close()


def test_anonimizar_quita_los_datos_personales_y_conserva_citas_y_cobros(escena):
    assert NOMBRE in " ".join(volcar_texto(escena["ruta"]))  # antes los datos sí estaban
    usuario = anonimizar_cliente.anonimizar(escena["url"], CORREO)
    assert usuario.nombre == "Cliente anonimizado"
    assert usuario.correo == f"anon-{escena['cliente_id']}@anonimo.invalid"
    celdas = " | ".join(volcar_texto(escena["ruta"]))
    assert NOMBRE not in celdas and CORREO not in celdas and "Pérez" not in celdas  # ni rastro en ninguna tabla
    assert contar(escena["ruta"], "citas") == 1 and contar(escena["ruta"], "cobros") == 1
    c = sqlite3.connect(escena["ruta"])
    assert c.execute("SELECT cliente_id FROM citas").fetchone() == (escena["cliente_id"],)
    assert c.execute("SELECT monto FROM cobros").fetchone() == (12000,)
    c.close()


def test_la_cuenta_anonimizada_queda_inutilizable(escena):
    anonimizar_cliente.anonimizar(escena["url"], CORREO)
    http = escena["http"]
    correo_anonimo = f"anon-{escena['cliente_id']}@anonimo.invalid"
    for correo, clave in ((CORREO, CONTRASENA_DE_PRUEBA), (correo_anonimo, CONTRASENA_DE_PRUEBA),
                          (correo_anonimo, ""), (correo_anonimo, "!anonimizado")):  # pragma: allowlist secret
        assert http.post("/sesion", json={"correo": correo, "contrasena": clave}).status_code in {401, 422}
    hash_guardado = escena["servicios"].usuarios.por_id(escena["cliente_id"]).contrasena_hash
    assert not verificar_contrasena(CONTRASENA_DE_PRUEBA, hash_guardado) and not verificar_contrasena("", hash_guardado)
    assert not verificar_contrasena(hash_guardado, hash_guardado)
    # la sesión que ya estaba abierta tampoco sirve
    assert http.get("/yo", headers={"Authorization": f"Bearer {escena['token']}"}).status_code == 401


def test_el_correo_original_queda_libre_para_registrarse_de_nuevo(escena):
    anonimizar_cliente.anonimizar(escena["url"], CORREO)
    r = escena["http"].post("/cuentas/clientes", json={
        "nombre": "Otra Persona", "correo": CORREO, "contrasena": CONTRASENA_DE_PRUEBA})
    assert r.status_code == 201 and r.json()["id"] != escena["cliente_id"]


def test_anonimizar_dos_veces_o_un_correo_que_no_existe_falla(escena):
    anonimizar_cliente.anonimizar(escena["url"], CORREO)
    with pytest.raises(UsuarioNoEncontrado):
        anonimizar_cliente.anonimizar(escena["url"], CORREO)
    with pytest.raises(UsuarioNoEncontrado):
        anonimizar_cliente.anonimizar(escena["url"], "nadie@ejemplo.test")


def test_solo_se_anonimizan_clientes_no_personal(escena):
    with pytest.raises(DatosInvalidos):
        anonimizar_cliente.anonimizar(escena["url"], "luis@ejemplo.test")
    assert escena["servicios"].usuarios.por_correo("luis@ejemplo.test").nombre == "Luis Barbero"


def test_el_script_por_la_linea_de_comandos(escena, capsys):
    entorno = {"DATABASE_URL": escena["url"]}
    assert anonimizar_cliente.main([CORREO], entorno) == 0
    salida = capsys.readouterr().out
    assert escena["cliente_id"] in salida and CORREO not in salida and NOMBRE not in salida
    assert anonimizar_cliente.main([CORREO], entorno) == 1  # ya no existe
    assert "No se pudo anonimizar" in capsys.readouterr().err
    assert anonimizar_cliente.main(["luis@ejemplo.test"], entorno) == 1  # personal: se niega
    assert anonimizar_cliente.main([CORREO], {}) == 1  # sin base configurada


def test_el_caso_de_uso_con_repositorio_en_memoria():
    usuarios = RepositorioDeUsuariosEnMemoria()
    ana = RegistrarCliente(usuarios).ejecutar(NOMBRE, CORREO, CONTRASENA_DE_PRUEBA)
    anonimo = AnonimizarCliente(usuarios).ejecutar(CORREO)
    assert anonimo.id == ana.id and anonimo.rol == CLIENTE and anonimo.nombre == "Cliente anonimizado"
    assert usuarios.por_correo(CORREO) is None and usuarios.por_id(ana.id).correo.endswith("@anonimo.invalid")
