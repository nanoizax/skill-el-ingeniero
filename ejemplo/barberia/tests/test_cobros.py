"""Cobros: solo sobre citas atendidas, monto entero positivo, medio válido y un solo cobro por cita."""
import pytest

from app.compartido.roles import BARBERO, CLIENTE, DUENO, RECEPCION

MEDIOS = ["efectivo", "tarjeta", "transferencia"]


@pytest.fixture
def escena(mundo):
    barbero, h_barbero = mundo.entrar(BARBERO, "Barbero Uno")
    cliente, h_cliente = mundo.entrar(CLIENTE, "Cliente Uno")
    return {"m": mundo, "barbero": barbero, "h_barbero": h_barbero, "cliente": cliente, "h_cliente": h_cliente}


def cita_atendida(escena, hora=15, atender=True):
    m = escena["m"]
    cita = m.agendar(escena["barbero"], escena["cliente"], hora=hora)
    if atender:
        assert m.atender(cita, escena["h_barbero"]).status_code == 200
    return cita["id"]


def cobrar(escena, cita_id, cabeceras=None, **cuerpo):
    cuerpo = {"monto": 10000, "medio": "efectivo", **cuerpo}
    cuerpo = {k: v for k, v in cuerpo.items() if v != "__falta__"}
    return escena["m"].http.post(f"/citas/{cita_id}/cobro", json=cuerpo, headers=cabeceras or escena["h_barbero"])


def test_el_barbero_cobra_una_cita_atendida_con_201(escena):
    r = cobrar(escena, cita_atendida(escena), monto=12000, medio="tarjeta")
    assert r.status_code == 201
    assert r.json()["monto"] == 12000 and r.json()["medio"] == "tarjeta" and isinstance(r.json()["monto"], int)


@pytest.mark.parametrize("medio", MEDIOS)
def test_se_acepta_cada_medio_de_pago(escena, medio):
    assert cobrar(escena, cita_atendida(escena), medio=medio).status_code == 201


def test_el_monto_minimo_es_un_peso(escena):
    assert cobrar(escena, cita_atendida(escena), monto=1).status_code == 201  # límite inferior


@pytest.mark.parametrize("rol", [RECEPCION, DUENO])
def test_recepcion_y_dueno_cobran_cualquier_cita(escena, rol):
    _, cabeceras = escena["m"].entrar(rol)
    assert cobrar(escena, cita_atendida(escena), cabeceras).status_code == 201


def test_no_se_cobra_dos_veces_la_misma_cita(escena):
    cita_id = cita_atendida(escena)
    assert cobrar(escena, cita_id).status_code == 201
    r = cobrar(escena, cita_id, monto=5000, medio="tarjeta")
    assert r.status_code == 409 and r.json()["error"] == "cita_ya_cobrada"


def test_no_se_cobra_una_cita_no_atendida(escena):
    confirmada = cita_atendida(escena, atender=False)
    r = cobrar(escena, confirmada)
    assert r.status_code == 409 and r.json()["error"] == "cita_no_atendida"
    escena["m"].http.post(f"/citas/{confirmada}/cancelar", headers=escena["h_barbero"])
    assert cobrar(escena, confirmada).status_code == 409  # cancelada tampoco se cobra
    assert escena["m"].servicios.cobros.de_la_cita(confirmada) is None


@pytest.mark.parametrize("monto", [0, -1, -10000, 100.5, 10000.0, 0.0, "10000", "", True, False, None, [], {}, 10**30])
def test_monto_cero_negativo_o_decimal_se_rechaza(escena, monto):
    cita_id = cita_atendida(escena)
    r = cobrar(escena, cita_id, monto=monto)
    assert r.status_code == 422 and r.json()["error"] == "monto_invalido"
    assert cobrar(escena, cita_id).status_code == 201  # no quedó cobrada por el intento fallido


def test_sin_monto_se_rechaza(escena):
    r = cobrar(escena, cita_atendida(escena), monto="__falta__")
    assert r.status_code == 422 and r.json()["error"] == "monto_invalido"


@pytest.mark.parametrize("medio", ["bitcoin", "", "EFECTIVO", "efectivo ", None, 5, True, [], "cheque"])
def test_medio_de_pago_invalido_se_rechaza(escena, medio):
    cita_id = cita_atendida(escena)
    r = cobrar(escena, cita_id, medio=medio)
    assert r.status_code == 422 and r.json()["error"] == "medio_invalido"
    assert cobrar(escena, cita_id).status_code == 201


def test_sin_medio_se_rechaza(escena):
    assert cobrar(escena, cita_atendida(escena), medio="__falta__").status_code == 422


def test_otro_barbero_y_el_cliente_no_cobran_y_responden_403(escena):
    cita_id = cita_atendida(escena)
    _, h_otro = escena["m"].entrar(BARBERO)
    assert cobrar(escena, cita_id, h_otro).status_code == 403
    assert cobrar(escena, cita_id, escena["h_cliente"]).status_code == 403
    assert cobrar(escena, cita_id).status_code == 201  # el cobro de verdad sigue disponible


def test_cobrar_sin_sesion_responde_401(escena):
    assert cobrar(escena, cita_atendida(escena), {"Authorization": "Bearer mal"}).status_code == 401


def test_cobrar_una_cita_que_no_existe_responde_404(escena):
    r = cobrar(escena, "no-existe")
    assert r.status_code == 404 and r.json()["error"] == "cita_no_encontrada"


def test_un_cuerpo_que_no_es_un_objeto_responde_422(escena):
    r = escena["m"].http.post(f"/citas/{cita_atendida(escena)}/cobro", json=[1, 2], headers=escena["h_barbero"])
    assert r.status_code == 422
