"""La API de citas: sesión obligatoria, quién agenda para quién, códigos de respuesta y que no se filtre nada interno."""
import pytest

from app.compartido.roles import BARBERO, CLIENTE, DUENO, RECEPCION


def cuerpo(barbero, hora="2026-12-01T15:00:00-03:00", duracion=30, cliente=None):
    datos = {"barbero_id": barbero.id, "inicio": hora, "duracion_minutos": duracion}
    if cliente is not None:
        datos["cliente_id"] = cliente.id if hasattr(cliente, "id") else cliente
    return datos


@pytest.fixture
def barbero(mundo):
    return mundo.usuario(BARBERO, "Barbero Uno")


def test_agendar_sin_sesion_responde_401(mundo, barbero):
    r = mundo.http.post("/citas", json=cuerpo(barbero))
    assert r.status_code == 401 and r.json()["error"] == "sesion_invalida"


def test_el_cliente_agenda_solo_para_si_mismo_y_se_ignora_el_cliente_id_enviado(mundo, barbero):
    cliente, cabeceras = mundo.entrar(CLIENTE)
    otro = mundo.usuario(CLIENTE)
    r = mundo.http.post("/citas", json=cuerpo(barbero, cliente=otro), headers=cabeceras)
    assert r.status_code == 201
    assert r.json()["cliente_id"] == cliente.id and r.json()["estado"] == "confirmada"
    r2 = mundo.http.post("/citas", json=cuerpo(barbero, "2026-12-01T16:00:00-03:00"), headers=cabeceras)
    assert r2.json()["cliente_id"] == cliente.id


def test_recepcion_y_dueno_agendan_para_cualquier_cliente(mundo, barbero):
    cliente = mundo.usuario(CLIENTE)
    horas = {RECEPCION: "2026-12-01T15:00:00-03:00", DUENO: "2026-12-01T16:00:00-03:00"}
    for rol, hora in horas.items():
        _, cabeceras = mundo.entrar(rol)
        r = mundo.http.post("/citas", json=cuerpo(barbero, hora, cliente=cliente), headers=cabeceras)
        assert r.status_code == 201 and r.json()["cliente_id"] == cliente.id


def test_recepcion_debe_indicar_para_que_cliente_agenda(mundo, barbero):
    _, cabeceras = mundo.entrar(RECEPCION)
    r = mundo.http.post("/citas", json=cuerpo(barbero), headers=cabeceras)
    assert r.status_code == 422 and r.json()["error"] == "datos_invalidos"


def test_el_barbero_no_agenda_y_responde_403(mundo, barbero):
    _, cabeceras = mundo.entrar(BARBERO)
    r = mundo.http.post("/citas", json=cuerpo(barbero), headers=cabeceras)
    assert r.status_code == 403 and r.json()["error"] == "no_autorizado"


def test_la_respuesta_muestra_la_hora_en_la_zona_del_negocio(mundo, barbero):
    _, cabeceras = mundo.entrar(CLIENTE)
    r = mundo.http.post("/citas", json=cuerpo(barbero, "2026-12-01T18:00:00+00:00"), headers=cabeceras)  # 15:00 local
    assert r.json()["inicio"] == "2026-12-01T15:00:00-03:00"
    assert r.json()["fin"] == "2026-12-01T15:30:00-03:00"


def test_hora_ocupada_responde_409_con_un_mensaje_claro(mundo, barbero):
    _, cabeceras = mundo.entrar(CLIENTE)
    mundo.http.post("/citas", json=cuerpo(barbero), headers=cabeceras)
    r = mundo.http.post("/citas", json=cuerpo(barbero), headers=cabeceras)
    assert r.status_code == 409
    assert r.json()["error"] == "barbero_ocupado"


def test_fuera_de_horario_responde_422(mundo, barbero):
    _, cabeceras = mundo.entrar(CLIENTE)
    r = mundo.http.post("/citas", json=cuerpo(barbero, "2026-12-06T15:00:00-03:00"), headers=cabeceras)  # domingo
    assert r.status_code == 422
    assert r.json()["error"] == "fuera_de_horario"


def test_un_cuerpo_incompleto_responde_422_sin_agendar(mundo):
    _, cabeceras = mundo.entrar(CLIENTE)
    r = mundo.http.post("/citas", json={"barbero_id": "ana"}, headers=cabeceras)
    assert r.status_code == 422 and r.json()["error"] == "datos_invalidos"


def test_un_error_inesperado_no_muestra_detalles_internos(mundo, barbero):
    class Roto:
        def ejecutar(self, *args, **kwargs):
            raise RuntimeError("contraseña interna de la base")
    mundo.servicios.agendar_cita = Roto()
    _, cabeceras = mundo.entrar(CLIENTE)
    r = mundo.http.post("/citas", json=cuerpo(barbero), headers=cabeceras)
    assert r.status_code == 500
    assert "contraseña" not in r.text and "RuntimeError" not in r.text
    assert r.json()["error"] == "error_interno"
