"""Cancelar, atender y mover a la vez: el cambio de estado es atómico y una cita cancelada no revive."""
import pytest
from ayudas import AHORA, a_las, lanzar_en_paralelo

from app.citas.casos_de_uso import AgendarCita, CancelarCita, MarcarAtendida, MoverCita
from app.citas.dominio import ATENDIDA, CANCELADA, CONFIRMADA, BarberoOcupado, Cita, CitaNoModificable, DemasiadasCitas
from app.citas.repositorio import RepositorioEnMemoria
from app.citas.repositorio_sqlite import RepositorioDeCitasSqlite
from app.compartido.db import BaseDeDatos
from app.compartido.migraciones import aplicar_migraciones
from app.compartido.roles import RECEPCION, Actor

ACTOR = Actor("recepcion-1", RECEPCION)


@pytest.fixture(params=["memoria", "sqlite-archivo"])
def citas(request, tmp_path):
    if request.param == "memoria":
        return RepositorioEnMemoria()
    base = BaseDeDatos(f"sqlite:///{tmp_path / 'carrera.db'}")
    aplicar_migraciones(base)
    return RepositorioDeCitasSqlite(base)


def crear(citas, hora=15, cliente="c1", barbero="b1"):
    return AgendarCita(citas, reloj=lambda: AHORA).ejecutar(barbero, cliente, a_las(hora), 30)


def test_cancelar_y_atender_la_misma_cita_a_la_vez_solo_una_gana(citas):
    cita = crear(citas)
    cancelar = CancelarCita(citas)
    atender = MarcarAtendida(citas, reloj=lambda: a_las(16))  # ya pasó la hora de la cita

    def accion(i):
        return (cancelar if i % 2 == 0 else atender).ejecutar(ACTOR, cita.id)

    resultados = lanzar_en_paralelo(20, accion)
    ganadoras = [r for r, error in resultados if error is None]
    errores = [error for _, error in resultados if error is not None]
    assert len(ganadoras) == 1, resultados
    assert len(errores) == 19 and all(isinstance(e, CitaNoModificable) for e in errores), errores
    assert citas.obtener(cita.id).estado == ganadoras[0].estado  # el estado final es el de la que ganó
    assert ganadoras[0].estado in {CANCELADA, ATENDIDA}


def test_mover_y_cancelar_a_la_vez_no_reactivan_una_cita_cancelada(citas):
    cita = crear(citas, hora=11)
    cancelar = CancelarCita(citas)
    mover = MoverCita(citas, reloj=lambda: AHORA)

    def accion(i):
        if i % 2 == 0:
            return cancelar.ejecutar(ACTOR, cita.id)
        return mover.ejecutar(ACTOR, cita.id, a_las(10 + i // 2))

    resultados = lanzar_en_paralelo(20, accion)
    canceladas = [r for r, error in resultados if error is None and r.estado == CANCELADA]
    assert len(canceladas) == 1  # una sola cancelación gana
    raros = [e for _, e in resultados if e is not None and not isinstance(e, (CitaNoModificable, BarberoOcupado))]
    assert raros == []
    assert citas.obtener(cita.id).estado == CANCELADA  # ningún movimiento tardío la dejó confirmada otra vez


def test_cambiar_estado_solo_cambia_si_sigue_en_el_estado_esperado(citas):
    cita = crear(citas)
    assert citas.cambiar_estado(cita.id, CONFIRMADA, CANCELADA) is True
    assert citas.cambiar_estado(cita.id, CONFIRMADA, ATENDIDA) is False  # ya no estaba confirmada
    assert citas.cambiar_estado("no-existe", CONFIRMADA, CANCELADA) is False
    assert citas.obtener(cita.id).estado == CANCELADA


def test_guardar_si_esta_libre_no_reescribe_una_cita_que_ya_no_esta_confirmada(citas):
    cita = crear(citas)
    citas.cambiar_estado(cita.id, CONFIRMADA, CANCELADA)
    reactivada = Cita(cita.id, cita.barbero_id, cita.cliente_id, cita.inicio, cita.fin, CONFIRMADA)
    with pytest.raises(CitaNoModificable):
        citas.guardar_si_esta_libre(reactivada)
    assert citas.obtener(cita.id).estado == CANCELADA


def test_el_limite_de_citas_por_cliente_aguanta_solicitudes_simultaneas(citas):
    agendar = AgendarCita(citas, reloj=lambda: AHORA)
    resultados = lanzar_en_paralelo(10, lambda i: agendar.ejecutar("b1", "mismo-cliente", a_las(10 + i), 30,
                                                                  limite_de_citas_futuras=3))
    assert sum(1 for _, error in resultados if error is None) == 3, resultados
    assert all(isinstance(e, DemasiadasCitas) for _, e in resultados if e is not None)
    assert len(citas.citas_en_rango(cliente_id="mismo-cliente")) == 3
