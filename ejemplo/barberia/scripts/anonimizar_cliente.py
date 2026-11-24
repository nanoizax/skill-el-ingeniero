"""Borrado a pedido de un cliente: anonimiza sus datos personales y conserva sus citas y cobros sin nombre.
Uso: python -m scripts.anonimizar_cliente correo@ejemplo.cl
Reemplaza el nombre por "Cliente anonimizado", el correo por anon-<id>@anonimo.invalid y deja la contraseña
inutilizable. Al final compacta el archivo (VACUUM) para que no queden restos del nombre dentro de la base.
No se puede deshacer; los respaldos hechos antes de anonimizar conservan el dato: bórralos o rehazlos."""
import argparse
import os
import sqlite3
import sys

from app.compartido.db import MEMORIA, BaseDeDatos, ruta_desde_url
from app.compartido.errores import ConfiguracionInvalida, ErrorDeNegocio
from app.compartido.migraciones import aplicar_migraciones
from app.cuentas.casos_de_uso import AnonimizarCliente
from app.cuentas.repositorio_sqlite import RepositorioDeUsuariosSqlite

ESPERA_POR_DEFECTO = 5.0  # segundos que se espera si otra conexión está escribiendo


class CompactacionIncompleta(Exception):
    """La cuenta ya quedó anonimizada, pero no se pudo compactar el archivo."""


def compactar(url, espera=ESPERA_POR_DEFECTO):
    """VACUUM fuera de transacción, con una conexión propia (la aplicación puede seguir en marcha), y luego un
    checkpoint que vacía el archivo -wal. Si otra conexión está escribiendo, lo dice con claridad."""
    ruta = ruta_desde_url(url)
    if ruta == MEMORIA:
        return
    conexion = sqlite3.connect(ruta, timeout=espera, isolation_level=None)
    try:
        conexion.execute("PRAGMA secure_delete = ON")
        conexion.execute("VACUUM")
        ocupado = conexion.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()[0]
    except sqlite3.OperationalError as error:
        raise CompactacionIncompleta(
            f"No se pudo compactar la base porque otra conexión la está usando ({error}). Los datos ya quedaron "
            "anonimizados, pero pueden quedar restos del nombre dentro del archivo. Cuando no haya nadie escribiendo "
            "(con la aplicación detenida), ejecuta VACUUM sobre la base.") from None
    finally:
        conexion.close()
    if ocupado:
        raise CompactacionIncompleta(
            "La base se compactó, pero otra conexión impidió vaciar el archivo -wal, que aún puede tener restos del "
            "nombre. Cuando no haya nadie usando la base, ejecuta PRAGMA wal_checkpoint(TRUNCATE).")


def anonimizar(url, correo, compactar_al_final=True):
    """Anonimiza y devuelve al usuario. Si no se pudo compactar, lanza CompactacionIncompleta con `.usuario`."""
    base = BaseDeDatos(url)
    aplicar_migraciones(base)
    usuario = AnonimizarCliente(RepositorioDeUsuariosSqlite(base)).ejecutar(correo)
    if compactar_al_final:
        try:
            compactar(url)
        except CompactacionIncompleta as error:
            error.usuario = usuario
            raise
    return usuario


def main(argv=None, entorno=None):
    parser = argparse.ArgumentParser(description="Anonimiza a un cliente de la barbería.")
    parser.add_argument("correo", help="el correo actual del cliente")
    argumentos = parser.parse_args(argv)
    entorno = os.environ if entorno is None else entorno
    url = entorno.get("DATABASE_URL")
    if not url:
        print("Falta la variable de entorno DATABASE_URL.", file=sys.stderr)
        return 1
    try:
        usuario = anonimizar(url, argumentos.correo, compactar_al_final=False)
    except (ErrorDeNegocio, ConfiguracionInvalida) as error:
        print(f"No se pudo anonimizar: {getattr(error, 'mensaje', error)}", file=sys.stderr)
        return 1
    print(f"Cliente anonimizado: {usuario.id}")  # solo el id: nunca se imprimen los datos que se borraron
    try:
        compactar(url)
    except CompactacionIncompleta as error:
        print(f"Atención: {error}", file=sys.stderr)
        return 2  # la cuenta quedó anonimizada, pero falta compactar el archivo
    print("Archivo compactado. Recuerda que los respaldos hechos antes de anonimizar conservan el dato.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
