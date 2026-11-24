"""Conexión SQLite y migraciones: base vacía, base con datos, idempotencia y errores a medias."""
import sqlite3

import pytest
from ayudas import AHORA

from app.compartido.db import BaseDeDatos, a_texto_utc, desde_texto_utc, ruta_desde_url
from app.compartido.errores import ConfiguracionInvalida
from app.compartido.migraciones import aplicar_migraciones

INICIO = "2026-12-01T18:00:00.000000"
FIN = "2026-12-01T18:30:00.000000"


def poblar(c):
    c.execute("INSERT INTO usuarios (id, nombre, correo, rol, contrasena_hash) VALUES "
              "('u1', 'Ana', 'ana@ejemplo.test', 'cliente', 'hash-ficticio')")  # pragma: allowlist secret
    c.execute("INSERT INTO citas (id, barbero_id, cliente_id, inicio, fin, estado) VALUES "
              f"('c1', 'b1', 'u1', '{INICIO}', '{FIN}', 'atendida')")
    c.execute("INSERT INTO cobros (id, cita_id, barbero_id, cita_inicio, monto, medio, registrado_en) VALUES "
              f"('k1', 'c1', 'b1', '{INICIO}', 10000, 'efectivo', '{FIN}')")


def instantanea(c):
    tablas = [n for (n,) in c.execute("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name")]
    contenido = {t: sorted(c.execute(f"SELECT * FROM {t}").fetchall()) for t in tablas}
    esquema = sorted(c.execute("SELECT type, name, sql FROM sqlite_master").fetchall())
    return contenido, esquema


@pytest.fixture
def base(tmp_path):
    return BaseDeDatos(f"sqlite:///{tmp_path / 'prueba.db'}")


def test_migraciones_en_una_base_vacia(base):
    assert aplicar_migraciones(base) == [1, 2]
    with base.conexion() as c:
        nombres = {n for (n,) in c.execute("SELECT name FROM sqlite_master")}
        assert {"usuarios", "citas", "cobros", "schema_version", "idx_citas_barbero_inicio"} <= nombres
        assert [v for (v,) in c.execute("SELECT version FROM schema_version ORDER BY version")] == [1, 2]
        assert c.execute("PRAGMA foreign_keys").fetchone() == (1,)
        assert c.execute("PRAGMA journal_mode").fetchone() == ("wal",)
        indice = [fila[2] for fila in c.execute("PRAGMA index_info(idx_citas_barbero_inicio)")]
        assert indice == ["barbero_id", "inicio"]


def test_las_restricciones_de_la_base_se_cumplen(base):
    aplicar_migraciones(base)
    with base.conexion() as c:
        poblar(c)
        with pytest.raises(sqlite3.IntegrityError):  # correo único, sin importar mayúsculas
            c.execute("INSERT INTO usuarios (id, nombre, correo, rol, contrasena_hash) VALUES "
                      "('u2', 'Otra', 'ANA@ejemplo.test', 'cliente', 'x')")
        with pytest.raises(sqlite3.IntegrityError):  # un solo cobro por cita
            c.execute("INSERT INTO cobros (id, cita_id, barbero_id, cita_inicio, monto, medio, registrado_en) VALUES "
                      f"('k2', 'c1', 'b1', '{INICIO}', 5000, 'tarjeta', '{FIN}')")
        for monto in (0, -5):  # monto mayor que cero
            with pytest.raises(sqlite3.IntegrityError):
                c.execute("INSERT INTO citas (id, barbero_id, cliente_id, inicio, fin, estado) VALUES "
                          f"('c2', 'b1', 'u1', '{INICIO}', '{FIN}', 'atendida')")
                c.execute("INSERT INTO cobros (id, cita_id, barbero_id, cita_inicio, monto, medio, registrado_en) VALUES "
                          f"('k3', 'c2', 'b1', '{INICIO}', {monto}, 'efectivo', '{FIN}')")
            c.execute("DELETE FROM citas WHERE id = 'c2'")
        with pytest.raises(sqlite3.IntegrityError):  # clave foránea: no hay cita 'fantasma'
            c.execute("INSERT INTO cobros (id, cita_id, barbero_id, cita_inicio, monto, medio, registrado_en) VALUES "
                      f"('k4', 'fantasma', 'b1', '{INICIO}', 100, 'efectivo', '{FIN}')")
        with pytest.raises(sqlite3.IntegrityError):  # una cita no puede terminar antes de empezar
            c.execute("INSERT INTO citas (id, barbero_id, cliente_id, inicio, fin, estado) VALUES "
                      f"('c3', 'b1', 'u1', '{FIN}', '{INICIO}', 'confirmada')")


def test_migraciones_con_datos_existentes(base):
    assert aplicar_migraciones(base, hasta=1) == [1]
    with base.conexion() as c:
        poblar(c)
        antes = instantanea(c)[0]
        assert "idx_citas_barbero_inicio" not in {n for (n,) in c.execute("SELECT name FROM sqlite_master")}
    assert aplicar_migraciones(base) == [2]  # solo falta la 002
    with base.conexion() as c:
        contenido, _ = instantanea(c)
        assert {t: filas for t, filas in contenido.items() if t != "schema_version"} == \
            {t: filas for t, filas in antes.items() if t != "schema_version"}  # los datos siguen intactos
        assert c.execute("SELECT count(*) FROM citas").fetchone() == (1,)
        assert c.execute("SELECT monto FROM cobros").fetchone() == (10000,)
        assert c.execute("SELECT count(*) FROM sqlite_master WHERE name = 'idx_citas_barbero_inicio'").fetchone() == (1,)


def test_migraciones_aplicadas_dos_veces_no_cambian_nada(base):
    aplicar_migraciones(base)
    with base.conexion() as c:
        poblar(c)
        antes = instantanea(c)
    assert aplicar_migraciones(base) == []
    with base.conexion() as c:
        assert instantanea(c) == antes  # mismos datos, mismo esquema y mismas filas en schema_version


def test_una_migracion_con_error_se_deshace_completa_y_no_se_registra(base, tmp_path):
    carpeta = tmp_path / "migraciones"
    carpeta.mkdir()
    (carpeta / "001_ok.sql").write_text("CREATE TABLE uno (id INTEGER);", encoding="utf-8")
    (carpeta / "002_mala.sql").write_text("CREATE TABLE dos (id INTEGER); CREATE TABLE uno (id INTEGER);",
                                          encoding="utf-8")
    with pytest.raises(sqlite3.Error):
        aplicar_migraciones(base, carpeta=carpeta)
    with base.conexion() as c:
        nombres = {n for (n,) in c.execute("SELECT name FROM sqlite_master")}
        assert "uno" in nombres and "dos" not in nombres  # la 002 no dejó nada a medias
        assert [v for (v,) in c.execute("SELECT version FROM schema_version")] == [1]


def test_dos_migraciones_con_el_mismo_numero_se_rechazan(base, tmp_path):
    (tmp_path / "001_a.sql").write_text("SELECT 1;", encoding="utf-8")
    (tmp_path / "001_b.sql").write_text("SELECT 1;", encoding="utf-8")
    with pytest.raises(ConfiguracionInvalida):
        aplicar_migraciones(base, carpeta=tmp_path)


@pytest.mark.parametrize("url,ruta", [
    ("sqlite:///barberia.db", "barberia.db"),
    ("sqlite:////var/datos/barberia.db", "/var/datos/barberia.db"),
    ("sqlite:///C:/datos/barberia.db", "C:/datos/barberia.db"),
    ("datos/barberia.db", "datos/barberia.db"),
    (r"C:\datos\barberia.db", r"C:\datos\barberia.db"),
    (":memory:", ":memory:"),
    ("sqlite:///:memory:", ":memory:"),
])
def test_la_ruta_sale_de_la_url(url, ruta):
    assert ruta_desde_url(url) == ruta


@pytest.mark.parametrize("url", ["", "   ", None, "sqlite:///", "postgresql://u@h/db"])
def test_una_url_invalida_se_rechaza(url):
    with pytest.raises(ConfiguracionInvalida):
        ruta_desde_url(url)


def test_las_horas_se_guardan_como_texto_utc_y_vuelven_iguales():
    texto = a_texto_utc(AHORA)  # 09:00 en Santiago (UTC-3) = 12:00 UTC
    assert texto == "2026-12-01T12:00:00.000000"
    assert desde_texto_utc(texto) == AHORA and desde_texto_utc(texto).utcoffset().total_seconds() == 0
    with pytest.raises(ValueError):
        a_texto_utc(AHORA.replace(tzinfo=None))  # una hora sin zona no se guarda
