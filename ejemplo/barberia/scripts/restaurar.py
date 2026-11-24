"""Restaura un respaldo. Uso: python -m scripts.restaurar <archivo> <destino> [--forzar]
Detén la aplicación antes de restaurar sobre la base en uso."""
import argparse
import os
import sqlite3
import sys
from pathlib import Path

from scripts.respaldo import RespaldoInvalido, contar_filas, verificar_copia


class RestauracionInvalida(Exception):
    pass


class DestinoYaExiste(RestauracionInvalida):
    pass


def _abrir_solo_lectura(ruta):
    return sqlite3.connect(Path(ruta).resolve().as_uri() + "?mode=ro", uri=True)


def contar_filas_de(ruta):
    conexion = _abrir_solo_lectura(ruta)
    try:
        return contar_filas(conexion)
    finally:
        conexion.close()


def _archivos_auxiliares(destino):
    return [destino.with_name(destino.name + sufijo) for sufijo in ("-wal", "-shm")]


def restaurar(archivo, destino, forzar=False):
    """Copia el respaldo al destino. No pisa un destino que ya existe salvo con forzar=True."""
    archivo, destino = Path(archivo), Path(destino)
    if not archivo.is_file():
        raise RestauracionInvalida(f"No existe el archivo de respaldo {archivo}.")
    if destino.exists() and not forzar:
        raise DestinoYaExiste(f"{destino} ya existe. Usa --forzar si de verdad quieres reemplazarlo.")
    try:
        esperado = contar_filas_de(archivo)
        verificar_copia(archivo, esperado)  # no se restaura algo dañado
    except (sqlite3.DatabaseError, RespaldoInvalido) as error:
        raise RestauracionInvalida(f"El archivo no es un respaldo sano: {error}") from None
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporal = destino.with_name(destino.name + ".restaurando")
    temporal.unlink(missing_ok=True)
    try:
        origen = _abrir_solo_lectura(archivo)
        copia = sqlite3.connect(temporal)
        try:
            origen.backup(copia)
            copia.execute("PRAGMA journal_mode = DELETE")
        finally:
            copia.close()
            origen.close()
        verificar_copia(temporal, esperado)
        for auxiliar in _archivos_auxiliares(destino):
            auxiliar.unlink(missing_ok=True)  # un -wal viejo no debe aplicarse sobre la base restaurada
        os.replace(temporal, destino)
    except BaseException:
        temporal.unlink(missing_ok=True)
        raise
    return destino


def main(argv=None):
    parser = argparse.ArgumentParser(description="Restaura un respaldo de la base de datos de la barbería.")
    parser.add_argument("archivo", help="el respaldo (barberia-AAAAMMDD-HHMMSS.db)")
    parser.add_argument("destino", help="dónde dejar la base restaurada")
    parser.add_argument("--forzar", action="store_true", help="reemplazar el destino si ya existe")
    argumentos = parser.parse_args(argv)
    try:
        destino = restaurar(argumentos.archivo, argumentos.destino, argumentos.forzar)
    except (RestauracionInvalida, sqlite3.Error, OSError) as error:
        print(f"No se pudo restaurar: {error}", file=sys.stderr)
        return 1
    print(f"Restauración lista: {destino}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
