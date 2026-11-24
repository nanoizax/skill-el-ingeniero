"""Cierre de caja: totales en pesos enteros, por medio y por barbero, en el día de la zona del negocio."""
from datetime import datetime, timedelta, timezone

import pytest
from ayudas import a_las

from app.citas.dominio import ATENDIDA, ZONA, Cita
from app.cobros.dominio import Cobro
from app.compartido.roles import BARBERO, CLIENTE, DUENO, RECEPCION

FECHA = "2026-12-01"


@pytest.fixture
def local(mundo):
    b1, h1 = mundo.entrar(BARBERO, "Barbero Uno")
    b2, h2 = mundo.entrar(BARBERO, "Barbero Dos")
    cliente, _ = mundo.entrar(CLIENTE)
    _, dueno = mundo.entrar(DUENO)
    return {"m": mundo, "b1": b1, "h1": h1, "b2": b2, "h2": h2, "cliente": cliente, "dueno": dueno}


def cobrar(local, barbero, cabeceras, monto, medio, hora, dia=1):
    m = local["m"]
    cita = m.agendar(barbero, local["cliente"], hora=hora, dia=dia)
    assert m.atender(cita, cabeceras).status_code == 200
    r = m.http.post(f"/citas/{cita['id']}/cobro", json={"monto": monto, "medio": medio}, headers=cabeceras)
    assert r.status_code == 201, r.text
    return cita["id"]


def caja(local, cabeceras=None, fecha=FECHA):
    return local["m"].http.get("/caja", params={"fecha": fecha}, headers=cabeceras or local["dueno"])


def test_el_cierre_suma_enteros_y_cuadra(local):
    cobrar(local, local["b1"], local["h1"], 10000, "efectivo", 11)
    cobrar(local, local["b1"], local["h1"], 12000, "tarjeta", 12)
    cobrar(local, local["b2"], local["h2"], 8000, "efectivo", 13)
    r = caja(local)
    assert r.status_code == 200
    cierre = r.json()
    assert cierre["total"] == 10000 + 12000 + 8000 == 30000
    assert cierre["cantidad_de_cobros"] == 3 and cierre["fecha"] == FECHA
    assert cierre["por_medio"] == {"efectivo": 18000, "tarjeta": 12000, "transferencia": 0}
    assert cierre["por_barbero"] == {local["b1"].id: 22000, local["b2"].id: 8000}
    assert sum(cierre["por_medio"].values()) == cierre["total"] == sum(cierre["por_barbero"].values())
    valores = [cierre["total"], *cierre["por_medio"].values(), *cierre["por_barbero"].values()]
    assert all(type(v) is int for v in valores)  # nunca decimales


def test_dia_sin_cobros_da_cero(local):
    cierre = caja(local, fecha="2026-12-03").json()
    assert cierre == {"fecha": "2026-12-03", "total": 0, "cantidad_de_cobros": 0,
                      "por_medio": {"efectivo": 0, "tarjeta": 0, "transferencia": 0}, "por_barbero": {}}


def test_solo_cuenta_el_dia_pedido(local):
    cobrar(local, local["b1"], local["h1"], 10000, "efectivo", 11, dia=1)
    inicio = a_las(11, dia=2).astimezone(timezone.utc)  # el día 2 se carga directo: todavía no llega
    local["m"].servicios.citas.guardar(Cita("d2", local["b1"].id, local["cliente"].id, inicio,
                                            inicio + timedelta(minutes=30), estado=ATENDIDA))
    local["m"].servicios.cobros.guardar(Cobro("k-d2", "d2", local["b1"].id, inicio, 7000, "transferencia", inicio))
    assert caja(local, fecha="2026-12-01").json()["total"] == 10000
    assert caja(local, fecha="2026-12-02").json()["por_medio"]["transferencia"] == 7000


def test_un_cobro_no_se_cuenta_dos_veces_aunque_se_intente_cobrar_otra_vez(local):
    cita_id = cobrar(local, local["b1"], local["h1"], 10000, "efectivo", 11)
    local["m"].http.post(f"/citas/{cita_id}/cobro", json={"monto": 10000, "medio": "efectivo"}, headers=local["h1"])
    assert caja(local).json()["total"] == 10000


def test_el_dia_de_caja_se_define_en_la_zona_del_negocio_no_en_utc(local):
    m = local["m"]

    def cobro_directo(id_, inicio_local, monto):  # se guarda directo: el horario normal no deja citas de noche
        inicio = inicio_local.astimezone(timezone.utc)
        m.servicios.citas.guardar(Cita(id_, local["b1"].id, local["cliente"].id, inicio,
                                       inicio + timedelta(minutes=30), estado=ATENDIDA))
        m.servicios.cobros.guardar(Cobro("c-" + id_, id_, local["b1"].id, inicio, monto, "efectivo", inicio))

    cobro_directo("noche", datetime(2026, 12, 1, 23, 30, tzinfo=ZONA), 5000)  # 02:30 UTC del día 2
    cobro_directo("madrugada", datetime(2026, 12, 2, 0, 15, tzinfo=ZONA), 3000)
    assert caja(local, fecha="2026-12-01").json()["total"] == 5000
    assert caja(local, fecha="2026-12-02").json()["total"] == 3000


@pytest.mark.parametrize("rol", [RECEPCION, BARBERO, CLIENTE])
def test_solo_el_dueno_ve_el_cierre(local, rol):
    _, cabeceras = local["m"].entrar(rol)
    r = caja(local, cabeceras)
    assert r.status_code == 403 and r.json()["error"] == "no_autorizado"
    assert caja(local, cabeceras, fecha="basura").status_code == 403  # primero el permiso


def test_el_cierre_exige_sesion(local):
    assert local["m"].http.get("/caja", params={"fecha": FECHA}).status_code == 401


@pytest.mark.parametrize("fecha", ["2026-13-01", "2026-02-30", "hola", "", "20261201", "2026-12-1"])
def test_el_cierre_rechaza_fechas_invalidas(local, fecha):
    r = caja(local, fecha=fecha)
    assert r.status_code == 422 and r.json()["error"] == "datos_invalidos"


def test_el_cierre_exige_la_fecha(local):
    assert local["m"].http.get("/caja", headers=local["dueno"]).status_code == 422
