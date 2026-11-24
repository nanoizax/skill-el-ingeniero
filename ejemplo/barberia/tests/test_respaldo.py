"""Respaldo y restauración de la base SQLite: copia segura, verificación y que nunca se pise un archivo sin permiso."""
import hashlib
import re
import sqlite3
from datetime import datetime, timedelta, timezone

import pytest
from ayudas import AHORA, a_las

from app.citas.dominio import ATENDIDA, Cita
from app.citas.repositorio_sqlite import RepositorioDeCitasSqlite
from app.cobros.dominio import Cobro
from app.cobros.repositorio_sqlite import RepositorioDeCobrosSqlite
from app.compartido.db import BaseDeDatos
from app.compartido.migraciones import aplicar_migraciones
from app.cuentas.dominio import Usuario
from app.cuentas.repositorio_sqlite import RepositorioDeUsuariosSqlite
from scripts import respaldo, restaurar


def crear_base(ruta, cobros=2):
    """Una base real en archivo con usuarios, citas y cobros ficticios."""
    base = BaseDeDatos(f"sqlite:///{ruta}")
    aplicar_migraciones(base)
    usuarios, citas, repo_cobros = RepositorioDeUsuariosSqlite(base), RepositorioDeCitasSqlite(base), \
        RepositorioDeCobrosSqlite(base)
    usuarios.guardar(Usuario("u1", "Ana", "ana@ejemplo.test", "cliente", "hash-ficticio"))  # pragma: allowlist secret
    usuarios.guardar(Usuario("b1", "Luis", "luis@ejemplo.test", "barbero", "hash-ficticio"))  # pragma: allowlist secret
    for i in range(cobros):
        inicio = (a_las(11 + i)).astimezone(timezone.utc)
        cita = Cita(f"c{i}", "b1", "u1", inicio, inicio + timedelta(minutes=30), ATENDIDA)
        citas.guardar(cita)
        repo_cobros.guardar(Cobro(f"k{i}", cita.id, "b1", inicio, 10000 + i, "efectivo", AHORA))
    return base


def volcar(ruta):
    """Todas las filas de todas las tablas, para comparar dos bases."""
    c = sqlite3.connect(ruta)
    try:
        tablas = [n for (n,) in c.execute("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name")]
        return {t: sorted(c.execute(f"SELECT * FROM {t}").fetchall()) for t in tablas}
    finally:
        c.close()


def borrar_base(ruta):
    for sufijo in ("", "-wal", "-shm"):
        ruta.with_name(ruta.name + sufijo).unlink(missing_ok=True)


def huella(ruta):
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def test_respaldo_y_restauracion_devuelven_los_mismos_datos(tmp_path):
    original = tmp_path / "barberia.db"
    crear_base(original)
    antes = volcar(original)
    assert antes["cobros"] and antes["citas"] and antes["usuarios"]

    copia = respaldo.respaldar(original, tmp_path / "respaldos")
    assert re.fullmatch(r"barberia-\d{8}-\d{6}\.db", copia.name) and copia.parent == tmp_path / "respaldos"
    assert volcar(copia) == antes

    borrar_base(original)  # se pierde la base original
    assert not original.exists()
    restaurar.restaurar(copia, original)
    assert volcar(original) == antes  # mismos datos, fila por fila
    assert restaurar.contar_filas_de(original)["cobros"] == 2


def test_el_respaldo_se_nombra_con_la_fecha_y_hora_de_la_zona_del_negocio(tmp_path):
    crear_base(tmp_path / "b.db")
    ahora = datetime(2026, 12, 1, 15, 4, 5, tzinfo=timezone.utc)  # 12:04:05 en Santiago (UTC-3)
    assert respaldo.respaldar(tmp_path / "b.db", tmp_path / "r", ahora=ahora).name == "barberia-20261201-120405.db"


def test_el_respaldo_incluye_lo_que_aun_esta_en_el_wal(tmp_path):
    original = tmp_path / "barberia.db"
    base = crear_base(original, cobros=1)
    with base.conexion() as c:  # esta conexión sigue abierta: los cambios viven en el archivo -wal
        c.execute("INSERT INTO usuarios (id, nombre, correo, rol, contrasena_hash) VALUES "
                  "('u9', 'Nueva', 'nueva@ejemplo.test', 'cliente', 'hash-ficticio')")  # pragma: allowlist secret
        copia = respaldo.respaldar(original, tmp_path / "r")
    fila = ("u9", "Nueva", "nueva@ejemplo.test", "cliente", "hash-ficticio")  # pragma: allowlist secret
    assert fila in volcar(copia)["usuarios"]


def test_la_copia_no_modifica_la_base_original(tmp_path):
    original = tmp_path / "barberia.db"
    crear_base(original)
    antes = volcar(original)
    respaldo.respaldar(original, tmp_path / "r")
    assert volcar(original) == antes


def test_el_respaldo_detecta_una_copia_con_filas_de_menos(tmp_path):
    original = tmp_path / "barberia.db"
    crear_base(original)
    copia = respaldo.respaldar(original, tmp_path / "r")
    esperado = restaurar.contar_filas_de(original)
    respaldo.verificar_copia(copia, esperado)  # la buena pasa
    c = sqlite3.connect(copia)
    c.execute("DELETE FROM cobros WHERE id = 'k0'")
    c.commit()
    c.close()
    with pytest.raises(respaldo.RespaldoInvalido, match="cobros"):
        respaldo.verificar_copia(copia, esperado)


def test_el_respaldo_detecta_una_copia_danada(tmp_path):
    original = tmp_path / "barberia.db"
    crear_base(original)
    copia = respaldo.respaldar(original, tmp_path / "r")
    esperado = restaurar.contar_filas_de(original)
    datos = bytearray(copia.read_bytes())
    for i in range(4096, min(len(datos), 4096 * 3)):  # se estropean las páginas siguientes a la primera
        datos[i] = 0xFF
    copia.write_bytes(bytes(datos))
    with pytest.raises(respaldo.RespaldoInvalido):
        respaldo.verificar_copia(copia, esperado)


def test_respaldar_algo_que_no_existe_falla_con_un_mensaje_claro(tmp_path):
    with pytest.raises(respaldo.RespaldoInvalido, match="No existe"):
        respaldo.respaldar(tmp_path / "no-hay.db", tmp_path / "r")
    assert not (tmp_path / "r").exists() or not list((tmp_path / "r").iterdir())


def test_no_se_pisa_un_respaldo_del_mismo_segundo(tmp_path):
    crear_base(tmp_path / "b.db")
    ahora = datetime(2026, 12, 1, 15, 4, 5, tzinfo=timezone.utc)
    primero = respaldo.respaldar(tmp_path / "b.db", tmp_path / "r", ahora=ahora)
    firma = huella(primero)
    with pytest.raises(respaldo.RespaldoInvalido, match="ya existe"):
        respaldo.respaldar(tmp_path / "b.db", tmp_path / "r", ahora=ahora)
    assert huella(primero) == firma
    assert [p.name for p in (tmp_path / "r").iterdir()] == [primero.name]  # sin restos de la copia parcial


def test_la_restauracion_no_pisa_un_archivo_existente(tmp_path, capsys):
    original = tmp_path / "barberia.db"
    crear_base(original)
    copia = respaldo.respaldar(original, tmp_path / "r")
    destino = tmp_path / "otra.db"
    destino.write_bytes(b"contenido importante que no se debe perder")
    firma = huella(destino)

    with pytest.raises(restaurar.DestinoYaExiste):
        restaurar.restaurar(copia, destino)
    assert huella(destino) == firma
    assert restaurar.main([str(copia), str(destino)]) == 1  # por la línea de comandos también se niega
    assert "--forzar" in capsys.readouterr().err
    assert huella(destino) == firma

    assert restaurar.main([str(copia), str(destino), "--forzar"]) == 0  # con permiso explícito sí
    assert volcar(destino) == volcar(original)


def test_forzar_limpia_los_archivos_wal_del_destino_anterior(tmp_path):
    original = tmp_path / "barberia.db"
    crear_base(original)
    copia = respaldo.respaldar(original, tmp_path / "r")
    destino = tmp_path / "vieja.db"
    crear_base(destino, cobros=1)
    destino.with_name("vieja.db-wal").write_bytes(b"restos del wal anterior")
    destino.with_name("vieja.db-shm").write_bytes(b"restos")
    restaurar.restaurar(copia, destino, forzar=True)
    assert not destino.with_name("vieja.db-wal").exists() and not destino.with_name("vieja.db-shm").exists()
    assert volcar(destino) == volcar(original)


def test_restaurar_un_archivo_que_no_es_una_base_no_toca_el_destino(tmp_path):
    falso = tmp_path / "falso.db"
    falso.write_bytes(b"esto no es una base de datos sqlite" * 100)
    with pytest.raises(restaurar.RestauracionInvalida):
        restaurar.restaurar(falso, tmp_path / "destino.db")
    assert not (tmp_path / "destino.db").exists()
    assert not list(tmp_path.glob("destino.db*"))  # ni archivos temporales
    with pytest.raises(restaurar.RestauracionInvalida, match="No existe"):
        restaurar.restaurar(tmp_path / "nada.db", tmp_path / "destino.db")


def test_el_script_de_respaldo_usa_las_variables_de_entorno(tmp_path, capsys):
    crear_base(tmp_path / "barberia.db")
    entorno = {"DATABASE_URL": f"sqlite:///{tmp_path / 'barberia.db'}", "RESPALDO_DESTINO": str(tmp_path / "r")}
    assert respaldo.main([], entorno) == 0
    assert "Respaldo listo" in capsys.readouterr().out
    assert len(list((tmp_path / "r").glob("barberia-*.db"))) == 1


@pytest.mark.parametrize("entorno", [{}, {"DATABASE_URL": "sqlite:///x.db"}, {"RESPALDO_DESTINO": "r"},
                                     {"DATABASE_URL": ":memory:", "RESPALDO_DESTINO": "r"}])
def test_el_script_de_respaldo_avisa_si_falta_configuracion(entorno, capsys):
    assert respaldo.main([], entorno) == 1
    assert capsys.readouterr().err.strip() != ""
