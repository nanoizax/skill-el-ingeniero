"""La agenda del día y las citas de cada cliente: quién ve qué, en qué orden y con qué zona horaria."""
from datetime import datetime, timedelta, timezone

import pytest

from app.citas.dominio import ZONA, Cita
from app.compartido.roles import BARBERO, CLIENTE, DUENO, RECEPCION

FECHA = "2026-12-01"


def agenda(mundo, cabeceras, fecha=FECHA, **extra):
    return mundo.http.get("/agenda", params={"fecha": fecha, **extra}, headers=cabeceras)


def horas(respuesta):
    return [c["inicio"][11:16] for c in respuesta.json()]


@pytest.fixture
def local(mundo):
    """Dos barberos con citas fuera de orden, dos clientes y una cita cancelada que no debe verse."""
    b1, h1 = mundo.entrar(BARBERO, "Barbero Uno")
    b2, h2 = mundo.entrar(BARBERO, "Barbero Dos")
    c1, hc1 = mundo.entrar(CLIENTE, "Cliente Uno")
    c2, hc2 = mundo.entrar(CLIENTE, "Cliente Dos")
    mundo.agendar(b1, c1, hora=17)
    mundo.agendar(b1, c2, hora=11)
    mundo.agendar(b2, c1, hora=14)
    cancelada = mundo.agendar(b1, c1, hora=12)
    mundo.http.post(f"/citas/{cancelada['id']}/cancelar", headers=hc1)
    return {"m": mundo, "b1": b1, "h1": h1, "b2": b2, "h2": h2, "c1": c1, "hc1": hc1, "c2": c2, "hc2": hc2}


def test_un_barbero_no_ve_las_citas_de_otro(local):
    m = local["m"]
    r = agenda(m, local["h1"], barbero_id=local["b2"].id)  # intenta mirar la agenda del otro: se ignora
    assert r.status_code == 200
    assert {c["barbero_id"] for c in r.json()} == {local["b1"].id}
    assert horas(r) == ["11:00", "17:00"]
    assert horas(agenda(m, local["h2"])) == ["14:00"]


def test_la_agenda_sale_ordenada_por_hora(local):
    m = local["m"]
    _, recepcion = m.entrar(RECEPCION)
    assert horas(agenda(m, recepcion)) == ["11:00", "14:00", "17:00"]  # todos los barberos, mezclados y en orden
    assert horas(agenda(m, recepcion, barbero_id=local["b1"].id)) == ["11:00", "17:00"]
    _, dueno = m.entrar(DUENO)
    assert horas(agenda(m, dueno, barbero_id=local["b2"].id)) == ["14:00"]


def test_las_citas_canceladas_no_aparecen_pero_las_atendidas_si(local):
    m = local["m"]
    primera = agenda(m, local["h1"]).json()[0]
    assert m.atender(primera, local["h1"]).status_code == 200
    r = agenda(m, local["h1"])
    assert [c["estado"] for c in r.json()] == ["atendida", "confirmada"]


def test_un_dia_sin_citas_devuelve_lista_vacia(local):
    r = agenda(local["m"], local["h1"], fecha="2026-12-03")
    assert r.status_code == 200 and r.json() == []


def test_el_cliente_no_ve_la_agenda_y_recibe_403(local):
    r = agenda(local["m"], local["hc1"])
    assert r.status_code == 403 and r.json()["error"] == "no_autorizado"
    assert agenda(local["m"], local["hc1"], fecha="basura").status_code == 403  # primero el permiso


def test_la_agenda_exige_sesion(mundo):
    assert mundo.http.get("/agenda", params={"fecha": FECHA}).status_code == 401
    assert mundo.http.get("/mis-citas").status_code == 401


def test_una_hora_se_guarda_en_utc_y_se_muestra_en_zona_del_negocio(mundo):
    barbero, h_barbero = mundo.entrar(BARBERO)
    cliente, h_cliente = mundo.entrar(CLIENTE)
    _, recepcion = mundo.entrar(RECEPCION)
    # Verano en Santiago (UTC-3): 19:30 locales son las 22:30 UTC.
    creada = mundo.http.post("/citas", headers=recepcion, json={
        "barbero_id": barbero.id, "cliente_id": cliente.id, "inicio": "2026-12-01T22:30:00+00:00",
        "duracion_minutos": 30}).json()
    guardada = mundo.servicios.citas.obtener(creada["id"])
    assert guardada.inicio.utcoffset() == timedelta(0)
    assert (guardada.inicio.hour, guardada.inicio.minute) == (22, 30)
    assert agenda(mundo, h_barbero).json()[0]["inicio"] == "2026-12-01T19:30:00-03:00"
    # Invierno (UTC-4): 15:00 locales son las 19:00 UTC; el 5 de julio de 2027 es lunes.
    invierno = mundo.http.post("/citas", headers=recepcion, json={
        "barbero_id": barbero.id, "cliente_id": cliente.id, "inicio": "2027-07-05T15:00:00-04:00",
        "duracion_minutos": 30}).json()
    assert mundo.servicios.citas.obtener(invierno["id"]).inicio.hour == 19
    assert agenda(mundo, h_barbero, fecha="2027-07-05").json()[0]["inicio"] == "2027-07-05T15:00:00-04:00"


def test_el_dia_se_calcula_en_la_zona_del_negocio_no_en_utc(mundo):
    barbero, h_barbero = mundo.entrar(BARBERO)
    cliente, _ = mundo.entrar(CLIENTE)

    def guardar(id_, inicio_local):  # se guarda directo: el horario normal no deja citas de noche
        inicio = inicio_local.astimezone(timezone.utc)
        mundo.servicios.citas.guardar(Cita(id_, barbero.id, cliente.id, inicio, inicio + timedelta(minutes=30)))

    guardar("tarde", datetime(2026, 12, 1, 23, 30, tzinfo=ZONA))  # 02:30 UTC del día 2: sigue siendo día 1 en Santiago
    guardar("medianoche", datetime(2026, 12, 2, 0, 0, tzinfo=ZONA))  # límite: ya es el día 2
    guardar("antes", datetime(2026, 12, 1, 0, 0, tzinfo=ZONA))  # límite: primer minuto del día 1
    dia1 = [c["id"] for c in agenda(mundo, h_barbero, fecha="2026-12-01").json()]
    dia2 = [c["id"] for c in agenda(mundo, h_barbero, fecha="2026-12-02").json()]
    assert dia1 == ["antes", "tarde"] and dia2 == ["medianoche"]


def test_un_cliente_solo_ve_sus_propias_citas(local):
    m = local["m"]
    r1 = m.http.get("/mis-citas", headers=local["hc1"])
    r2 = m.http.get("/mis-citas", headers=local["hc2"])
    assert r1.status_code == 200
    assert {c["cliente_id"] for c in r1.json()} == {local["c1"].id}
    assert horas(r1) == ["14:00", "17:00"]  # ordenadas y sin la cancelada
    assert [c["cliente_id"] for c in r2.json()] == [local["c2"].id] and horas(r2) == ["11:00"]


def test_un_cliente_sin_citas_ve_una_lista_vacia(mundo):
    _, cabeceras = mundo.entrar(CLIENTE)
    assert mundo.http.get("/mis-citas", headers=cabeceras).json() == []


@pytest.mark.parametrize("fecha", ["2026-13-01", "2026-02-30", "hola", "", "20261201", "2026-12-1", "2026-W48-2",
                                   "2026-12-01T10:00", " 2026-12-01"])
@pytest.mark.parametrize("rol", [BARBERO, RECEPCION, DUENO])
def test_fecha_invalida_se_rechaza(mundo, rol, fecha):
    _, cabeceras = mundo.entrar(rol)
    r = agenda(mundo, cabeceras, fecha=fecha)
    assert r.status_code == 422 and r.json()["error"] == "datos_invalidos"


def test_agenda_sin_fecha_se_rechaza(mundo):
    _, cabeceras = mundo.entrar(RECEPCION)
    assert mundo.http.get("/agenda", headers=cabeceras).status_code == 422
