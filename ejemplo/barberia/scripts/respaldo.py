"""Copia segura de la base SQLite. Uso: python -m scripts.respaldo (lee DATABASE_URL y RESPALDO_DESTINO)."""
import argparse
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

from app.citas.dominio import ZONA
from app.compartido.db import MEMORIA, ruta_desde_url
from app.compartido.errores import ConfiguracionInvalida


class RespaldoInvalido(Exception):
    pass


def contar_filas(conexion):
    """Cantidad de filas de cada tabla de la base."""
    tablas = [n for (n,) in conexion.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    return {t: conexion.execute('SELECT count(*) FROM "{}"'.format(t.replace('"', '""'))).fetchone()[0]
            for t in tablas}


def verificar_copia(ruta_copia, cuentas_esperadas):
    """La copia debe pasar PRAGMA integrity_check y tener las mismas filas por tabla que el origen."""
    try:
        conexion = sqlite3.connect(Path(ruta_copia).resolve().as_uri() + "?mode=ro", uri=True)
        try:
            integridad = [f[0] for f in conexion.execute("PRAGMA integrity_check")]
            if integridad != ["ok"]:
                raise RespaldoInvalido(f"La copia está dañada: {'; '.join(integridad[:3])}")
            cuentas = contar_filas(conexion)
        finally:
            conexion.close()
    except sqlite3.DatabaseError as error:
        raise RespaldoInvalido(f"La copia no se pudo leer: {error}") from None
    if cuentas != cuentas_esperadas:
        faltan = [t for t in cuentas_esperadas if cuentas.get(t) != cuentas_esperadas[t]]
        raise RespaldoInvalido(f"La copia no coincide con el original en las tablas: {', '.join(faltan)}.")


def respaldar(ruta_base, carpeta_destino, ahora=None):
    """Copia con la API de respaldo de sqlite3 (segura aunque la base esté en uso) a
    <carpeta>/barberia-AAAAMMDD-HHMMSS.db. Devuelve la ruta de la copia ya verificada."""
    origen_ruta = Path(ruta_base)
    if not origen_ruta.is_file():
        raise RespaldoInvalido(f"No existe la base de datos en {origen_ruta}.")
    momento = (ahora or datetime.now(timezone.utc)).astimezone(ZONA)
    carpeta = Path(carpeta_destino)
    destino = carpeta / f"barberia-{momento:%Y%m%d-%H%M%S}.db"
    if destino.exists():
        raise RespaldoInvalido(f"El respaldo {destino.name} ya existe; espera un segundo e intenta de nuevo.")
    carpeta.mkdir(parents=True, exist_ok=True)
    parcial = destino.with_name(destino.name + ".parcial")
    parcial.unlink(missing_ok=True)
    origen = sqlite3.connect(origen_ruta, timeout=30, isolation_level=None)
    try:
        origen.execute("BEGIN")
        origen.execute("SELECT count(*) FROM sqlite_master").fetchone()  # fija la foto: copia y conteo ven lo mismo
        copia = sqlite3.connect(parcial)
        try:
            origen.backup(copia)
            copia.execute("PRAGMA journal_mode = DELETE")  # un solo archivo, sin -wal ni -shm
        finally:
            copia.close()
        esperado = contar_filas(origen)
        origen.execute("COMMIT")
        verificar_copia(parcial, esperado)
        os.replace(parcial, destino)
    except BaseException:
        parcial.unlink(missing_ok=True)
        raise
    finally:
        origen.close()
    return destino


def main(argv=None, entorno=None):
    argparse.ArgumentParser(description="Respalda la base de datos de la barbería.").parse_args(argv)
    entorno = os.environ if entorno is None else entorno
    url, destino = entorno.get("DATABASE_URL"), entorno.get("RESPALDO_DESTINO")
    if not url or not destino:
        print("Faltan las variables de entorno DATABASE_URL y RESPALDO_DESTINO.", file=sys.stderr)
        return 1
    try:
        ruta = ruta_desde_url(url)
        if ruta == MEMORIA:
            raise RespaldoInvalido("Una base en memoria no se puede respaldar.")
        copia = respaldar(ruta, destino)
    except (RespaldoInvalido, ConfiguracionInvalida, sqlite3.Error, OSError) as error:
        print(f"No se pudo respaldar: {error}", file=sys.stderr)
        return 1
    print(f"Respaldo listo: {copia}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
