"""Cancelar, mover y marcar como atendida una cita: quién puede, en qué estado y qué pasa con la hora."""
from datetime import datetime, timedelta

import pytest

from app.compartido.roles import BARBERO, CLIENTE, DUENO, RECEPCION

OTRA_HORA = "2026-12-01T17:00:00-03:00"


@pytest.fixture
def escena(mundo):
    """Un barbero con una cita a las 15:00 de su cliente, más otro cliente y otro barbero."""
    barbero, h_barbero = mundo.entrar(BARBERO, "Barbero Uno")
    cliente, h_cliente = mundo.entrar(CLIENTE, "Cliente Uno")
    cita = mundo.agendar(barbero, cliente)
    return {"m": mundo, "barbero": barbero, "h_barbero": h_barbero, "cliente": cliente, "h_cliente": h_cliente,
            "cita": cita, "url": f"/citas/{cita['id']}"}


def accion(escena, nombre, cabeceras, cuerpo=None):
    return escena["m"].http.post(f"{escena['url']}/{nombre}", json=cuerpo, headers=cabeceras)


def atender(escena, cabeceras):
    """Atiende la cita de la escena con el reloj ya pasada su hora de inicio."""
    return escena["m"].atender(escena["cita"], cabeceras)


def cuerpo_en_la_hora_de_la_cita(escena):
    return {"barbero_id": escena["barbero"].id, "inicio": escena["cita"]["inicio"], "duracion_minutos": 30}


# ---------- cancelar ----------

def test_el_cliente_cancela_su_propia_cita(escena):
    r = accion(escena, "cancelar", escena["h_cliente"])
    assert r.status_code == 200 and r.json()["estado"] == "cancelada"


def test_un_cliente_no_puede_cancelar_la_cita_de_otro(escena):
    _, h_otro = escena["m"].entrar(CLIENTE)
    r = accion(escena, "cancelar", h_otro)
    assert r.status_code == 403 and r.json()["error"] == "no_autorizado"
    assert atender(escena, escena["h_barbero"]).json()["estado"] == "atendida"  # seguía confirmada


def test_un_barbero_no_cancela_citas_de_otro_barbero(escena):
    _, h_otro_barbero = escena["m"].entrar(BARBERO)
    assert accion(escena, "cancelar", h_otro_barbero).status_code == 403


def test_el_barbero_cancela_las_citas_de_su_agenda(escena):
    assert accion(escena, "cancelar", escena["h_barbero"]).status_code == 200


@pytest.mark.parametrize("rol", [RECEPCION, DUENO])
def test_recepcion_y_dueno_cancelan_cualquier_cita(escena, rol):
    _, cabeceras = escena["m"].entrar(rol)
    assert accion(escena, "cancelar", cabeceras).json()["estado"] == "cancelada"


def test_cancelar_libera_la_hora(escena):
    m = escena["m"]
    otro, h_otro = m.entrar(CLIENTE)
    cuerpo = cuerpo_en_la_hora_de_la_cita(escena)
    assert m.http.post("/citas", json=cuerpo, headers=h_otro).status_code == 409  # ocupada
    accion(escena, "cancelar", escena["h_cliente"])
    r = m.http.post("/citas", json=cuerpo, headers=h_otro)
    assert r.status_code == 201 and r.json()["cliente_id"] == otro.id


def test_no_se_cancela_dos_veces_ni_una_cita_atendida(escena):
    assert accion(escena, "cancelar", escena["h_cliente"]).status_code == 200
    segunda = accion(escena, "cancelar", escena["h_cliente"])
    assert segunda.status_code == 409 and segunda.json()["error"] == "cita_no_modificable"
    otro, h_otro = escena["m"].entrar(CLIENTE)
    otra = escena["m"].agendar(escena["barbero"], otro, hora=12)
    escena["m"].atender(otra, escena["h_barbero"])
    assert escena["m"].http.post(f"/citas/{otra['id']}/cancelar", headers=h_otro).status_code == 409


def test_cancelar_una_cita_que_no_existe_responde_404(mundo):
    _, cabeceras = mundo.entrar(RECEPCION)
    r = mundo.http.post("/citas/no-existe/cancelar", headers=cabeceras)
    assert r.status_code == 404 and r.json()["error"] == "cita_no_encontrada"


def test_las_acciones_sobre_citas_exigen_sesion(escena):
    for nombre in ("cancelar", "mover", "atender"):
        assert accion(escena, nombre, {}, {"inicio": OTRA_HORA}).status_code == 401


# ---------- mover ----------

def test_mover_cambia_la_hora_conserva_la_duracion_y_libera_la_anterior(escena):
    m = escena["m"]
    r = accion(escena, "mover", escena["h_cliente"], {"inicio": OTRA_HORA})
    assert r.status_code == 200
    assert r.json()["inicio"] == OTRA_HORA and r.json()["fin"] == "2026-12-01T17:30:00-03:00"
    assert r.json()["id"] == escena["cita"]["id"] and r.json()["estado"] == "confirmada"
    _, h_otro = m.entrar(CLIENTE)
    assert m.http.post("/citas", json=cuerpo_en_la_hora_de_la_cita(escena), headers=h_otro).status_code == 201


def test_no_se_mueve_a_una_hora_ocupada(escena):
    m = escena["m"]
    otro, _ = m.entrar(CLIENTE)
    m.agendar(escena["barbero"], otro, hora=17)
    r = accion(escena, "mover", escena["h_cliente"], {"inicio": "2026-12-01T17:15:00-03:00"})
    assert r.status_code == 409 and r.json()["error"] == "barbero_ocupado"
    # la cita no se movió: sigue en su hora original y una hora libre sí se acepta
    assert accion(escena, "mover", escena["h_cliente"], {"inicio": "2026-12-01T18:00:00-03:00"}).status_code == 200


def test_mover_ignora_la_propia_cita_al_revisar_el_cruce(escena):
    r = accion(escena, "mover", escena["h_cliente"], {"inicio": "2026-12-01T15:15:00-03:00"})  # se cruza solo con ella
    assert r.status_code == 200 and r.json()["inicio"] == "2026-12-01T15:15:00-03:00"


def test_no_se_mueve_una_cita_atendida(escena):
    atender(escena, escena["h_barbero"])
    r = accion(escena, "mover", escena["h_cliente"], {"inicio": OTRA_HORA})
    assert r.status_code == 409 and r.json()["error"] == "cita_no_modificable"


def test_no_se_mueve_una_cita_cancelada(escena):
    accion(escena, "cancelar", escena["h_cliente"])
    assert accion(escena, "mover", escena["h_cliente"], {"inicio": OTRA_HORA}).status_code == 409


@pytest.mark.parametrize("destino,error", [
    ("2026-12-01T08:00:00-03:00", "cita_en_el_pasado"),  # antes de "ahora" (09:00)
    ("2026-12-02T09:30:00-03:00", "fuera_de_horario"),  # antes de abrir
    ("2026-12-02T19:45:00-03:00", "fuera_de_horario"),  # termina después del cierre
    ("2026-12-06T12:00:00-03:00", "fuera_de_horario"),  # domingo
    ("2026-12-02T12:00:00", "datos_invalidos"),  # sin zona horaria
])
def test_mover_aplica_las_mismas_reglas_que_agendar(escena, destino, error):
    r = accion(escena, "mover", escena["h_cliente"], {"inicio": destino})
    assert r.status_code == 422 and r.json()["error"] == error


def test_mover_exige_el_campo_inicio(escena):
    assert accion(escena, "mover", escena["h_cliente"], {}).status_code == 422


def test_mover_la_cita_de_otro_responde_403_y_la_cita_no_se_mueve(escena):
    _, h_otro = escena["m"].entrar(CLIENTE)
    assert accion(escena, "mover", h_otro, {"inicio": OTRA_HORA}).status_code == 403
    assert accion(escena, "mover", escena["h_barbero"], {"inicio": OTRA_HORA}).status_code == 200  # el suyo sí


def test_mover_una_cita_que_no_existe_responde_404(mundo):
    _, cabeceras = mundo.entrar(RECEPCION)
    assert mundo.http.post("/citas/no-existe/mover", json={"inicio": OTRA_HORA}, headers=cabeceras).status_code == 404


# ---------- atender ----------

def test_el_barbero_de_la_cita_la_marca_atendida(escena):
    r = atender(escena, escena["h_barbero"])
    assert r.status_code == 200 and r.json()["estado"] == "atendida"


@pytest.mark.parametrize("rol", [RECEPCION, DUENO])
def test_recepcion_y_dueno_marcan_cualquier_cita_como_atendida(escena, rol):
    _, cabeceras = escena["m"].entrar(rol)
    assert atender(escena, cabeceras).json()["estado"] == "atendida"


def test_otro_barbero_no_marca_la_cita_como_atendida(escena):
    _, h_otro = escena["m"].entrar(BARBERO)
    assert atender(escena, h_otro).status_code == 403


def test_el_cliente_no_se_marca_a_si_mismo_como_atendido(escena):
    assert atender(escena, escena["h_cliente"]).status_code == 403


def test_no_se_atiende_dos_veces_ni_una_cita_cancelada(escena):
    assert atender(escena, escena["h_barbero"]).status_code == 200
    assert atender(escena, escena["h_barbero"]).status_code == 409
    otro, h_otro = escena["m"].entrar(CLIENTE)
    otra = escena["m"].agendar(escena["barbero"], otro, hora=12)
    escena["m"].http.post(f"/citas/{otra['id']}/cancelar", headers=h_otro)
    assert escena["m"].atender(otra, escena["h_barbero"]).status_code == 409


def test_una_cita_atendida_sigue_ocupando_la_hora(escena):
    atender(escena, escena["h_barbero"])
    _, h_otro = escena["m"].entrar(CLIENTE)
    assert escena["m"].http.post("/citas", json=cuerpo_en_la_hora_de_la_cita(escena), headers=h_otro).status_code == 409


def test_no_se_atiende_una_cita_que_todavia_no_empieza(escena):
    r = accion(escena, "atender", escena["h_barbero"])  # son las 09:00 y la cita es a las 15:00
    assert r.status_code == 409 and r.json()["error"] == "cita_futura"
    assert atender(escena, escena["h_barbero"]).status_code == 200  # a la hora sí


def test_la_cita_se_puede_atender_justo_a_su_hora_de_inicio_y_no_un_segundo_antes(escena):
    m, inicio = escena["m"], datetime.fromisoformat(escena["cita"]["inicio"])
    m.reloj.ahora = inicio - timedelta(seconds=1)
    assert accion(escena, "atender", escena["h_barbero"]).status_code == 409
    m.reloj.ahora = inicio  # límite: ya es la hora
    assert accion(escena, "atender", escena["h_barbero"]).status_code == 200


def test_una_cita_futura_cancelada_se_informa_como_no_modificable_antes_que_futura(escena):
    accion(escena, "cancelar", escena["h_cliente"])
    r = accion(escena, "atender", escena["h_barbero"])
    assert r.status_code == 409 and r.json()["error"] == "cita_no_modificable"
