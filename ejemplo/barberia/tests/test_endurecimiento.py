"""Hallazgos de la revisión: ids que existen, límites de abuso y entradas extremas que antes daban 500."""
import json
from datetime import date, timedelta

import pytest
from ayudas import CONTRASENA_DE_PRUEBA, a_las

from app.citas.casos_de_uso import AgendarCita
from app.citas.repositorio import RepositorioEnMemoria
from app.compartido.errores import DatosInvalidos
from app.compartido.roles import BARBERO, CLIENTE, DUENO, RECEPCION

REGISTRO = {"nombre": "Ana Pérez", "correo": "ana@ejemplo.test", "contrasena": CONTRASENA_DE_PRUEBA}
JSON = {"content-type": "application/json"}


def enviar(mundo, ruta, datos, cabeceras=None, http=None):
    """Envía el JSON tal cual (con ensure_ascii, así los caracteres sueltos viajan escapados como \\ud800)."""
    return (http or mundo.http).post(ruta, content=json.dumps(datos), headers={**JSON, **(cabeceras or {})})


def cita_de(barbero_id, hora="2026-12-01T15:00:00-03:00", duracion=30, **extra):
    return {"barbero_id": barbero_id, "inicio": hora, "duracion_minutos": duracion, **extra}


@pytest.fixture
def local(mundo):
    barbero = mundo.usuario(BARBERO, "Barbero Uno")
    cliente, h_cliente = mundo.entrar(CLIENTE, "Cliente Uno")
    _, h_recepcion = mundo.entrar(RECEPCION)
    _, h_dueno = mundo.entrar(DUENO)
    return {"m": mundo, "barbero": barbero, "cliente": cliente, "hc": h_cliente, "hr": h_recepcion, "hd": h_dueno}


# ---------- 1. barbero y cliente tienen que existir ----------

def test_agendar_con_un_barbero_que_no_existe_se_rechaza(local):
    m = local["m"]
    for barbero_id in ("no-existe", local["cliente"].id):  # un fantasma y el id de un cliente
        r = enviar(m, "/citas", cita_de(barbero_id), local["hc"])
        assert r.status_code == 422 and r.json()["error"] == "barbero_inexistente", barbero_id
    assert m.servicios.citas.citas_en_rango() == []  # nada quedó guardado


@pytest.mark.parametrize("barbero_id", ["", "x" * 65, "x" * 3_000_000, "ab\u0000cd", "a\nb"])  # pragma: allowlist secret
def test_un_id_de_barbero_vacio_largo_o_con_control_se_rechaza(local, barbero_id):
    r = enviar(local["m"], "/citas", cita_de(barbero_id), local["hc"])
    assert r.status_code == 422 and r.json()["error"] == "datos_invalidos"


def test_un_id_de_64_caracteres_es_valido_en_formato_pero_no_existe(local):
    r = enviar(local["m"], "/citas", cita_de("x" * 64), local["hc"])
    assert r.status_code == 422 and r.json()["error"] == "barbero_inexistente"  # límite: 64 pasa el formato


def test_el_cliente_que_indica_recepcion_tambien_tiene_que_existir(local):
    m = local["m"]
    otro_barbero = m.usuario(BARBERO)
    for cliente_id in ("fantasma", otro_barbero.id, local["barbero"].id):  # inexistente o con otro rol
        r = enviar(m, "/citas", cita_de(local["barbero"].id, cliente_id=cliente_id), local["hr"])
        assert r.status_code == 422 and r.json()["error"] == "cliente_inexistente", cliente_id
    for cliente_id in ("", "y" * 65, "a\u0000b"):
        r = enviar(m, "/citas", cita_de(local["barbero"].id, cliente_id=cliente_id), local["hd"])
        assert r.status_code == 422 and r.json()["error"] == "datos_invalidos", cliente_id
    ok = enviar(m, "/citas", cita_de(local["barbero"].id, cliente_id=local["cliente"].id), local["hr"])
    assert ok.status_code == 201
    assert m.servicios.citas.citas_en_rango()[0].cliente_id == local["cliente"].id


def test_un_id_con_control_en_la_ruta_se_rechaza_y_uno_largo_tambien(local):
    for cita_id in ("a%00b", "z" * 65):
        r = local["m"].http.post(f"/citas/{cita_id}/cancelar", headers=local["hr"])
        assert r.status_code == 422 and r.json()["error"] == "datos_invalidos", cita_id


# ---------- 2a. máximo 3 citas confirmadas a futuro por cliente ----------

def agendar_como(local, cabeceras, hora, **extra):
    return enviar(local["m"], "/citas", cita_de(local["barbero"].id, f"2026-12-01T{hora}:00-03:00", **extra), cabeceras)


def test_un_cliente_no_puede_tener_mas_de_3_citas_confirmadas_a_futuro(local):
    for hora in ("11:00", "12:00", "13:00"):
        assert agendar_como(local, local["hc"], hora).status_code == 201
    r = agendar_como(local, local["hc"], "14:00")
    assert r.status_code == 409 and r.json()["error"] == "demasiadas_citas"
    assert len(local["m"].servicios.citas.citas_en_rango(cliente_id=local["cliente"].id)) == 3


def test_cancelar_o_atender_una_cita_devuelve_el_cupo(local):
    m = local["m"]
    ids = [agendar_como(local, local["hc"], h).json() for h in ("11:00", "12:00", "13:00")]
    m.http.post(f"/citas/{ids[0]['id']}/cancelar", headers=local["hc"])
    assert agendar_como(local, local["hc"], "14:00").status_code == 201  # cancelada: ya no cuenta
    assert agendar_como(local, local["hc"], "15:00").status_code == 409
    assert m.atender(ids[1], local["hr"]).status_code == 200  # atendida: ya no es "por venir"
    assert agendar_como(local, local["hc"], "15:00").status_code == 201


def test_recepcion_y_dueno_no_sufren_el_limite_de_citas(local):
    for i, hora in enumerate(("11:00", "12:00", "13:00", "14:00", "15:00")):
        cabeceras = local["hr"] if i % 2 == 0 else local["hd"]
        assert agendar_como(local, cabeceras, hora, cliente_id=local["cliente"].id).status_code == 201


def test_el_limite_de_citas_es_por_cliente(local):
    otro, h_otro = local["m"].entrar(CLIENTE)
    for hora in ("11:00", "12:00", "13:00"):
        agendar_como(local, local["hc"], hora)
    assert agendar_como(local, h_otro, "14:00").status_code == 201


# ---------- 2b. límite por dirección ----------

def registrar(mundo, n, http=None, cabeceras=None):
    cuerpo = {**REGISTRO, "correo": f"cliente{n}@ejemplo.test"}
    return enviar(mundo, "/cuentas/clientes", cuerpo, cabeceras, http)


def test_el_registro_se_limita_a_10_por_hora_por_direccion(mundo):
    assert [registrar(mundo, n).status_code for n in range(10)] == [201] * 10
    r = registrar(mundo, 10)
    assert r.status_code == 429 and r.json()["error"] == "demasiadas_solicitudes"
    assert mundo.servicios.usuarios.por_correo("cliente10@ejemplo.test") is None
    assert registrar(mundo, 11, http=mundo.otra_direccion).status_code == 201  # otra dirección no se afecta
    mundo.reloj.avanzar(minutes=59, seconds=59)
    assert registrar(mundo, 12).status_code == 429  # límite: todavía dentro de la hora
    mundo.reloj.avanzar(seconds=1)
    assert registrar(mundo, 12).status_code == 201


def test_la_direccion_sale_de_la_conexion_y_no_de_x_forwarded_for(mundo):
    for n in range(10):
        registrar(mundo, n)
    for suplantada in ("198.51.100.7", "203.0.113.50, 10.0.0.1"):
        r = registrar(mundo, 99, cabeceras={"X-Forwarded-For": suplantada})
        assert r.status_code == 429  # cambiar la cabecera no ayuda a esquivar el límite
    r = registrar(mundo, 100, http=mundo.otra_direccion, cabeceras={"X-Forwarded-For": "198.51.100.7"})
    assert r.status_code == 201  # ni tampoco castiga a otra dirección real


def test_el_inicio_de_sesion_se_limita_a_30_intentos_por_15_minutos_por_direccion(mundo):
    def intentar(n, http=None):
        datos = {"correo": f"nadie{n}@ejemplo.test", "contrasena": "contrasena-mala-123"}  # pragma: allowlist secret
        return enviar(mundo, "/sesion", datos, http=http)
    assert [intentar(n).status_code for n in range(30)] == [401] * 30  # correos distintos: no salta el bloqueo por correo
    r = intentar(30)
    assert r.status_code == 429 and r.json()["error"] == "demasiadas_solicitudes"
    assert intentar(31, http=mundo.otra_direccion).status_code == 401
    mundo.reloj.avanzar(minutes=15)
    assert intentar(32).status_code == 401  # pasada la ventana vuelve a atender


def test_el_bloqueo_por_correo_sigue_funcionando_con_el_limite_por_direccion(mundo):
    registrar(mundo, 1)
    malo = {"correo": "cliente1@ejemplo.test", "contrasena": "contrasena-mala-123"}  # pragma: allowlist secret
    estados = [enviar(mundo, "/sesion", malo).status_code for _ in range(6)]
    assert estados == [401] * 5 + [429]
    assert enviar(mundo, "/sesion", malo).json()["error"] == "demasiados_intentos"


# ---------- 3. entradas extremas: 422 y nunca 500 ----------

@pytest.mark.parametrize("duracion", [10**12, 0, -1, 481, True, False, 30.5, 30.0, "30", None, [], {}])
def test_la_duracion_debe_ser_un_entero_entre_1_y_480(local, duracion):
    r = enviar(local["m"], "/citas", cita_de(local["barbero"].id, duracion=duracion), local["hc"])
    assert r.status_code == 422 and r.json()["error"] == "datos_invalidos", duracion


def test_la_duracion_en_los_limites_se_acepta(local):
    assert agendar_como(local, local["hc"], "10:00", duracion=480).status_code == 201  # 10:00 a 18:00
    assert agendar_como(local, local["hc"], "18:00", duracion=1).status_code == 201


@pytest.mark.parametrize("hora", ["9999-12-31T23:59:59-03:00", "9999-12-31T23:59:59+14:00", "2028-01-01T12:00:00-03:00"])
def test_un_inicio_demasiado_lejano_se_rechaza(local, hora):
    r = enviar(local["m"], "/citas", cita_de(local["barbero"].id, hora), local["hc"])
    assert r.status_code == 422 and r.json()["error"] == "datos_invalidos"


@pytest.mark.parametrize("hora", ["0001-01-01T00:00:00+05:00", "0001-01-01T00:00:00-14:00", "1900-01-01T10:00:00-03:00"])
def test_un_inicio_antiquisimo_se_rechaza_sin_error_500(local, hora):
    assert enviar(local["m"], "/citas", cita_de(local["barbero"].id, hora), local["hc"]).status_code == 422


def test_mover_tambien_rechaza_horas_extremas(local):
    cita = agendar_como(local, local["hc"], "11:00").json()
    for hora in ("9999-12-31T23:59:59-03:00", "0001-01-01T00:00:00+05:00"):
        r = enviar(local["m"], f"/citas/{cita['id']}/mover", {"inicio": hora}, local["hc"])
        assert r.status_code == 422, hora


def test_el_inicio_puede_ser_como_maximo_365_dias_despues_de_ahora():
    agendar = AgendarCita(RepositorioEnMemoria(), reloj=lambda: a_las(15))
    limite = a_las(15) + timedelta(days=365)  # miércoles 1-dic-2027 a las 15:00
    assert agendar.ejecutar("b1", "c1", limite, 30).inicio == limite  # límite: se acepta
    with pytest.raises(DatosInvalidos):
        agendar.ejecutar("b1", "c2", limite + timedelta(minutes=1), 30)


@pytest.mark.parametrize("ruta", ["/agenda", "/caja"])
def test_las_fechas_de_agenda_y_caja_van_de_2000_a_hoy_mas_5_anos(local, ruta):
    m, tope = local["m"], date(2026, 12, 1) + timedelta(days=1826)  # 2031-12-01
    for fecha in ("9999-12-31", "1999-12-31", "0001-01-01", "0000-01-01", (tope + timedelta(days=1)).isoformat()):
        r = m.http.get(ruta, params={"fecha": fecha}, headers=local["hd"])
        assert r.status_code == 422 and r.json()["error"] == "datos_invalidos", fecha
    for fecha in ("2000-01-01", tope.isoformat()):  # los dos límites exactos se aceptan
        assert m.http.get(ruta, params={"fecha": fecha}, headers=local["hd"]).status_code == 200, fecha


CARACTERES_MALOS = ["\u0000", "\n", "\t", "\x07", "\x7f"]


@pytest.mark.parametrize("malo", CARACTERES_MALOS)
@pytest.mark.parametrize("campo", ["nombre", "correo", "contrasena"])
def test_el_registro_rechaza_nul_y_caracteres_de_control(mundo, campo, malo):
    cuerpo = {**REGISTRO}
    cuerpo[campo] = cuerpo[campo].replace("a", "a" + malo, 1) if campo != "contrasena" else cuerpo[campo] + malo
    r = enviar(mundo, "/cuentas/clientes", cuerpo)
    assert r.status_code == 422 and r.json()["error"] in {"datos_invalidos", "contrasena_debil"}


@pytest.mark.parametrize("campo", ["nombre", "correo", "contrasena"])
def test_el_registro_rechaza_caracteres_sueltos_que_no_se_pueden_codificar(mundo, campo):
    cuerpo = {**REGISTRO}
    cuerpo[campo] = "ana\ud800" + cuerpo[campo] if campo == "nombre" else cuerpo[campo].replace("a", "a\udc80", 1)
    r = enviar(mundo, "/cuentas/clientes", cuerpo)
    assert r.status_code == 422 and r.json()["error"] == "datos_invalidos"
    assert mundo.servicios.usuarios.por_correo("ana@ejemplo.test") is None


def test_el_inicio_de_sesion_rechaza_entradas_extremas_con_422(mundo):
    for correo, clave in (("a\ud800@ejemplo.test", "x"), ("a\u0000@ejemplo.test", "x"), ("a@ejemplo.test", "\udc80"),
                          ("a@ejemplo.test", "x\u0000y"), ("a@ejemplo.test", "x" * 3_000_000),  # pragma: allowlist secret
                          ("a" * 300 + "@ejemplo.test", "x")):
        r = enviar(mundo, "/sesion", {"correo": correo, "contrasena": clave})
        assert r.status_code == 422 and r.json()["error"] == "datos_invalidos"


@pytest.mark.parametrize("campo,largo,acepta", [("nombre", 120, True), ("nombre", 121, False)])
def test_largo_maximo_del_nombre(mundo, campo, largo, acepta):
    r = enviar(mundo, "/cuentas/clientes", {**REGISTRO, "nombre": "N" * largo})
    assert (r.status_code == 201) is acepta
    if not acepta:
        assert r.json()["error"] == "datos_invalidos"


def test_largo_maximo_del_correo(mundo):
    valido = "c" * (254 - len("@ejemplo.test")) + "@ejemplo.test"
    assert len(valido) == 254
    assert enviar(mundo, "/cuentas/clientes", {**REGISTRO, "correo": valido}).status_code == 201
    r = enviar(mundo, "/cuentas/clientes", {**REGISTRO, "correo": "c" + valido})
    assert r.status_code == 422 and r.json()["error"] == "datos_invalidos"


def test_largo_maximo_de_la_contrasena(mundo):
    largo_maximo = {**REGISTRO, "contrasena": "p" * 200}  # pragma: allowlist secret
    assert enviar(mundo, "/cuentas/clientes", largo_maximo).status_code == 201
    otra = {**REGISTRO, "correo": "otra@ejemplo.test"}
    r = enviar(mundo, "/cuentas/clientes", {**otra, "contrasena": "p" * 201})  # pragma: allowlist secret
    assert r.status_code == 422 and r.json()["error"] == "datos_invalidos"
    r = enviar(mundo, "/cuentas/clientes", {**otra, "contrasena": "p" * 9})  # pragma: allowlist secret
    assert r.json()["error"] == "contrasena_debil"  # la regla de mínimo 10 sigue igual

