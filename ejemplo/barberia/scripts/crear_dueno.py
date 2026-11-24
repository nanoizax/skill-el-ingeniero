"""Crea la cuenta del dueño (la primera, porque solo el dueño puede crear personal).
Uso: python -m scripts.crear_dueno "Nombre Apellido" correo@ejemplo.cl
La contraseña se lee de DUENO_CONTRASENA o se pide por teclado; nunca se imprime."""  # pragma: allowlist secret
import argparse
import getpass
import os
import sys

from app.compartido.db import BaseDeDatos
from app.compartido.errores import ConfiguracionInvalida, ErrorDeNegocio
from app.compartido.migraciones import aplicar_migraciones
from app.cuentas.casos_de_uso import CrearDueno
from app.cuentas.repositorio_sqlite import RepositorioDeUsuariosSqlite


def crear_dueno(url, nombre, correo, contrasena):
    base = BaseDeDatos(url)
    aplicar_migraciones(base)
    return CrearDueno(RepositorioDeUsuariosSqlite(base)).ejecutar(nombre, correo, contrasena)


def main(argv=None, entorno=None, pedir=getpass.getpass):
    parser = argparse.ArgumentParser(description="Crea la cuenta del dueño de la barbería.")
    parser.add_argument("nombre")
    parser.add_argument("correo")
    argumentos = parser.parse_args(argv)
    entorno = os.environ if entorno is None else entorno
    url = entorno.get("DATABASE_URL")
    if not url:
        print("Falta la variable de entorno DATABASE_URL.", file=sys.stderr)
        return 1
    contrasena = entorno.get("DUENO_CONTRASENA") or pedir("Contraseña del dueño (mínimo 10 caracteres): ")
    try:
        dueno = crear_dueno(url, argumentos.nombre, argumentos.correo, contrasena)
    except (ErrorDeNegocio, ConfiguracionInvalida) as error:
        print(f"No se pudo crear al dueño: {getattr(error, 'mensaje', error)}", file=sys.stderr)
        return 1
    print(f"Dueño creado: {dueno.correo}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
