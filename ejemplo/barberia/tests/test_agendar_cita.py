"""Caso de uso 1: agendar una cita. Reglas: hora libre, sin solapar al mismo barbero, a futuro y dentro del horario."""
from datetime import datetime, timedelta

import pytest

from app.citas.casos_de_uso import AgendarCita
from app.citas.dominio import ZONA, BarberoOcupado, CitaEnElPasado, DuracionInvalida, FueraDeHorario
from app.citas.repositorio import RepositorioEnMemoria

AHORA = datetime(2026, 12, 1, 9, 0, tzinfo=ZONA)  # martes por la mañana


def a_las(hora, minuto=0, dia=1):
    return datetime(2026, 12, dia, hora, minuto, tzinfo=ZONA)


@pytest.fixture
def agendar():
    return AgendarCita(RepositorioEnMemoria(), reloj=lambda: AHORA)


def test_agenda_en_una_hora_libre(agendar):
    cita = agendar.ejecutar("ana", "cliente-1", a_las(15), 30)
    assert cita.estado == "confirmada"
    assert cita.fin - cita.inicio == timedelta(minutes=30)


def test_rechaza_si_el_barbero_ya_tiene_una_cita_que_se_cruza(agendar):
    agendar.ejecutar("ana", "cliente-1", a_las(15), 30)
    with pytest.raises(BarberoOcupado):
        agendar.ejecutar("ana", "cliente-2", a_las(15, 15), 30)


def test_permite_una_cita_que_empieza_justo_cuando_termina_otra(agendar):
    agendar.ejecutar("ana", "cliente-1", a_las(15), 30)
    cita = agendar.ejecutar("ana", "cliente-2", a_las(15, 30), 30)  # límite: el fin de una no choca con el inicio de la otra
    assert cita.inicio == a_las(15, 30)


def test_otro_barbero_puede_tener_la_misma_hora(agendar):
    agendar.ejecutar("ana", "cliente-1", a_las(15), 30)
    assert agendar.ejecutar("luis", "cliente-2", a_las(15), 30).barbero_id == "luis"


def test_rechaza_una_hora_que_ya_paso(agendar):
    with pytest.raises(CitaEnElPasado):
        agendar.ejecutar("ana", "cliente-1", a_las(8, 30), 30)


def test_rechaza_antes_de_la_apertura(agendar):
    with pytest.raises(FueraDeHorario):
        agendar.ejecutar("ana", "cliente-1", a_las(9, 30, dia=2), 30)


def test_rechaza_si_la_cita_termina_despues_del_cierre(agendar):
    with pytest.raises(FueraDeHorario):
        agendar.ejecutar("ana", "cliente-1", a_las(19, 45), 30)  # termina a las 20:15


def test_permite_una_cita_que_termina_justo_al_cierre(agendar):
    assert agendar.ejecutar("ana", "cliente-1", a_las(19, 30), 30).fin == a_las(20)


def test_rechaza_el_domingo(agendar):
    with pytest.raises(FueraDeHorario):
        agendar.ejecutar("ana", "cliente-1", a_las(15, dia=6), 30)  # 6 de diciembre de 2026 es domingo


@pytest.mark.parametrize("duracion", [0, -15])
def test_rechaza_duraciones_invalidas(agendar, duracion):
    with pytest.raises(DuracionInvalida):
        agendar.ejecutar("ana", "cliente-1", a_las(15), duracion)


def test_una_hora_sin_zona_horaria_se_rechaza_en_vez_de_adivinar(agendar):
    with pytest.raises(DuracionInvalida):
        agendar.ejecutar("ana", "cliente-1", datetime(2026, 12, 1, 15, 0), 30)
