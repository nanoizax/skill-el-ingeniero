"""Los repositorios en memoria y SQLite se comportan igual; y la reserva atómica aguanta carreras entre hilos."""
import threading
from datetime import timedelta, timezone

import pytest
from ayudas import AHORA, CLAVE_DE_PRUEBA, a_las

from app.citas.casos_de_uso import AgendarCita, MoverCita
from app.citas.dominio import ATENDIDA, CANCELADA, BarberoOcupado, Cita
from app.citas.repositorio import RepositorioEnMemoria
from app.citas.repositorio_sqlite import RepositorioDeCitasSqlite
from app.cobros.dominio import CitaYaCobrada, Cobro
from app.cobros.repositorio import RepositorioDeCobrosEnMemoria
from app.cobros.repositorio_sqlite import RepositorioDeCobrosSqlite
from app.compartido.db import BaseDeDatos
from app.compartido.migraciones import aplicar_migraciones
from app.compartido.roles import RECEPCION, Actor
from app.cuentas.dominio import CorreoYaRegistrado, Usuario
from app.cuentas.repositorio import RepositorioDeUsuariosEnMemoria
from app.cuentas.repositorio_sqlite import RepositorioDeUsuariosSqlite
from app.main import crear_app


def utc(dt):
    return dt.astimezone(timezone.utc)


def cita(id_, hora, minuto=0, barbero="b1", estado="confirmada", duracion=30):
    inicio = a_las(hora, minuto)
    return Cita(id_, barbero, "cliente-1", utc(inicio), utc(inicio + timedelta(minutes=duracion)), estado)


@pytest.fixture(params=["memoria", "sqlite"])
def repos(request):
    if request.param == "memoria":
        return RepositorioDeUsuariosEnMemoria(), RepositorioEnMemoria(), RepositorioDeCobrosEnMemoria()
    base = BaseDeDatos(":memory:")
    aplicar_migraciones(base)
    return RepositorioDeUsuariosSqlite(base), RepositorioDeCitasSqlite(base), RepositorioDeCobrosSqlite(base)


# ---------- citas ----------

def test_guardar_si_esta_libre_guarda_y_devuelve_lo_mismo(repos):
    _, citas, _ = repos
    citas.guardar_si_esta_libre(cita("c1", 15))
    assert citas.obtener("c1") == cita("c1", 15)
    assert citas.obtener("nada") is None


def test_guardar_si_esta_libre_rechaza_el_cruce_y_no_guarda(repos):
    _, citas, _ = repos
    citas.guardar_si_esta_libre(cita("c1", 15))
    with pytest.raises(BarberoOcupado):
        citas.guardar_si_esta_libre(cita("c2", 15, 15))
    assert citas.obtener("c2") is None


def test_pegadas_y_de_otro_barbero_no_cruzan(repos):
    _, citas, _ = repos
    citas.guardar_si_esta_libre(cita("c1", 15))
    citas.guardar_si_esta_libre(cita("c2", 15, 30))  # empieza justo cuando termina la otra
    citas.guardar_si_esta_libre(cita("c3", 14, 30))  # termina justo cuando empieza la otra
    citas.guardar_si_esta_libre(cita("c4", 15, barbero="b2"))
    assert all(citas.obtener(i) for i in ("c1", "c2", "c3", "c4"))


def test_guardar_si_esta_libre_ignora_la_propia_cita_al_moverla(repos):
    _, citas, _ = repos
    citas.guardar_si_esta_libre(cita("c1", 15))
    citas.guardar_si_esta_libre(cita("c1", 15, 15))  # se cruza solo consigo misma: es un movimiento
    assert citas.obtener("c1") == cita("c1", 15, 15)


def test_cancelada_libera_y_atendida_ocupa(repos):
    _, citas, _ = repos
    citas.guardar_si_esta_libre(cita("c1", 15))
    citas.guardar(cita("c1", 15, estado=CANCELADA))
    citas.guardar_si_esta_libre(cita("c2", 15))  # la hora quedó libre
    citas.guardar(cita("c2", 15, estado=ATENDIDA))
    with pytest.raises(BarberoOcupado):
        citas.guardar_si_esta_libre(cita("c3", 15))


def test_citas_en_rango_filtra_ordena_y_excluye_canceladas(repos):
    _, citas, _ = repos
    for c in (cita("tarde", 17), cita("manana", 11), cita("otro", 12, barbero="b2"),
              cita("cancelada", 13, estado=CANCELADA)):
        citas.guardar(c)
    todas = citas.citas_en_rango(utc(a_las(0)), utc(a_las(0, dia=2)))
    assert [c.id for c in todas] == ["manana", "otro", "tarde"]
    assert [c.id for c in citas.citas_en_rango(barbero_id="b1")] == ["manana", "tarde"]
    assert [c.id for c in citas.citas_en_rango(cliente_id="cliente-1")] == ["manana", "otro", "tarde"]
    assert citas.citas_en_rango(cliente_id="nadie") == []
    limite = utc(a_las(12))  # el límite inferior entra y el superior no
    assert [c.id for c in citas.citas_en_rango(limite, utc(a_las(17)))] == ["otro"]


def test_sqlite_guarda_las_horas_en_utc_como_texto(tmp_path):
    base = BaseDeDatos(f"sqlite:///{tmp_path / 'b.db'}")
    aplicar_migraciones(base)
    RepositorioDeCitasSqlite(base).guardar_si_esta_libre(
        Cita("c1", "b1", "u1", a_las(19, 30), a_las(20)))  # 19:30 en Santiago (UTC-3)
    with base.conexion() as c:
        assert c.execute("SELECT inicio, fin FROM citas").fetchone() == ("2026-12-01T22:30:00.000000",
                                                                         "2026-12-01T23:00:00.000000")


# ---------- cobros ----------

def un_cobro(id_="k1", cita_id="c1", monto=10000):
    return Cobro(id_, cita_id, "b1", utc(a_las(15)), monto, "efectivo", AHORA)


def test_un_cobro_por_cita_tambien_en_el_repositorio(repos):
    _, citas, cobros = repos
    citas.guardar(cita("c1", 15, estado=ATENDIDA))
    cobros.guardar(un_cobro())
    with pytest.raises(CitaYaCobrada):
        cobros.guardar(un_cobro("k2"))
    assert cobros.de_la_cita("c1").monto == 10000 and cobros.de_la_cita("otra") is None


def test_cobros_en_rango_usa_la_hora_de_la_cita(repos):
    _, citas, cobros = repos
    citas.guardar(cita("c1", 15, estado=ATENDIDA))
    cobros.guardar(un_cobro())
    assert [c.id for c in cobros.en_rango(utc(a_las(0)), utc(a_las(0, dia=2)))] == ["k1"]
    assert cobros.en_rango(utc(a_las(0, dia=2)), utc(a_las(0, dia=3))) == []
    assert cobros.en_rango(utc(a_las(15)), utc(a_las(16)))[0].registrado_en == AHORA  # inicio incluido


# ---------- usuarios ----------

def test_usuarios_guardar_buscar_y_correo_unico(repos):
    usuarios, _, _ = repos
    ana = Usuario("u1", "Ana", "ana@ejemplo.test", "cliente", "hash")
    usuarios.guardar(ana)
    assert usuarios.por_id("u1") == ana and usuarios.por_correo("ANA@ejemplo.test") == ana
    assert usuarios.por_id("x") is None and usuarios.por_correo("x@ejemplo.test") is None
    with pytest.raises(CorreoYaRegistrado):
        usuarios.guardar(Usuario("u2", "Otra", "ana@ejemplo.test", "cliente", "hash"))
    assert usuarios.por_id("u2") is None


# ---------- carreras entre hilos ----------

def correr_a_la_vez(hilos, accion):
    """Lanza `hilos` hilos que arrancan juntos; devuelve cuántos ganaron, cuántos chocaron y los errores raros."""
    barrera = threading.Barrier(hilos)
    resultados = []

    def tarea(i):
        barrera.wait()
        try:
            accion(i)
            resultados.append("ok")
        except BarberoOcupado:
            resultados.append("ocupado")
        except Exception as error:  # cualquier otro fallo es un bug: se reporta
            resultados.append(error)

    lanzados = [threading.Thread(target=tarea, args=(i,)) for i in range(hilos)]
    for h in lanzados:
        h.start()
    for h in lanzados:
        h.join(timeout=60)
    return resultados


@pytest.fixture(params=["memoria", "sqlite-archivo"])
def citas_compartidas(request, tmp_path):
    if request.param == "memoria":
        return RepositorioEnMemoria()
    base = BaseDeDatos(f"sqlite:///{tmp_path / 'carrera.db'}")
    aplicar_migraciones(base)
    return RepositorioDeCitasSqlite(base)


def test_dos_hilos_no_pueden_agendar_la_misma_hora(citas_compartidas):
    agendar = AgendarCita(citas_compartidas, reloj=lambda: AHORA)
    resultados = correr_a_la_vez(10, lambda i: agendar.ejecutar("b1", f"cliente-{i}", a_las(15), 30))
    assert resultados.count("ok") == 1 and resultados.count("ocupado") == 9, resultados
    assert len(citas_compartidas.citas_en_rango(barbero_id="b1")) == 1  # y en la base quedó una sola


def test_diez_hilos_moviendo_citas_a_la_misma_hora_solo_dejan_pasar_una(citas_compartidas):
    agendar = AgendarCita(citas_compartidas, reloj=lambda: AHORA)
    ids = [agendar.ejecutar("b1", f"cliente-{i}", a_las(10 + i), 30).id for i in range(8)]
    mover = MoverCita(citas_compartidas, reloj=lambda: AHORA)
    actor = Actor("recepcion-1", RECEPCION)
    resultados = correr_a_la_vez(8, lambda i: mover.ejecutar(actor, ids[i], a_las(19, 0)))
    assert resultados.count("ok") == 1 and resultados.count("ocupado") == 7, resultados
    a_las_19 = [c for c in citas_compartidas.citas_en_rango(barbero_id="b1") if c.inicio == utc(a_las(19))]
    assert len(a_las_19) == 1


def test_los_datos_sobreviven_a_reiniciar_la_aplicacion(tmp_path):
    url = f"sqlite:///{tmp_path / 'reinicio.db'}"
    primera = crear_app(CLAVE_DE_PRUEBA, database_url=url)
    primera.state.servicios.registrar_cliente.ejecutar("Ana", "ana@ejemplo.test", "contrasena-ficticia-123")
    segunda = crear_app(CLAVE_DE_PRUEBA, database_url=url)  # "reinicio": nueva aplicación, misma base
    assert segunda.state.servicios.usuarios.por_correo("ana@ejemplo.test").nombre == "Ana"


def test_crear_app_toma_la_base_de_la_variable_de_entorno(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'entorno.db'}")
    app = crear_app(CLAVE_DE_PRUEBA)
    app.state.servicios.registrar_cliente.ejecutar("Ana", "ana@ejemplo.test", "contrasena-ficticia-123")
    assert (tmp_path / "entorno.db").exists()
