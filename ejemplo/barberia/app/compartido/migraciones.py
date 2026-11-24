"""Ejecutor de migraciones SQL: aplica en orden las que faltan y lo anota en schema_version."""
import re
import sqlite3
from pathlib import Path

from app.compartido.errores import ConfiguracionInvalida

CARPETA = Path(__file__).resolve().parents[2] / "migrations"
_NOMBRE = re.compile(r"^(\d+)_.+\.sql$")


def _listar(carpeta):
    encontradas = {}
    for archivo in sorted(Path(carpeta).glob("*.sql")):
        coincide = _NOMBRE.match(archivo.name)
        if not coincide:
            continue
        version = int(coincide.group(1))
        if version in encontradas:
            raise ConfiguracionInvalida(f"Dos migraciones usan el número {version}: {encontradas[version].name} "
                                        f"y {archivo.name}.")
        encontradas[version] = archivo
    return sorted(encontradas.items())


def aplicar_migraciones(base, carpeta=None, hasta=None):
    """Aplica las migraciones pendientes (hasta la versión `hasta`, si se indica) y devuelve sus números.
    Es idempotente: una segunda llamada no hace nada. Cada migración es todo o nada."""
    aplicadas = []
    with base.conexion() as c:
        c.execute("CREATE TABLE IF NOT EXISTS schema_version ("
                  "version INTEGER PRIMARY KEY, nombre TEXT NOT NULL, aplicada_en TEXT NOT NULL)")
        for version, archivo in _listar(carpeta or CARPETA):
            if hasta is not None and version > hasta:
                break
            if c.execute("SELECT 1 FROM schema_version WHERE version = ?", (version,)).fetchone():
                continue
            nombre = archivo.name.replace("'", "''")
            guion = (f"BEGIN IMMEDIATE;\n{archivo.read_text(encoding='utf-8')}\n"
                     f"INSERT INTO schema_version (version, nombre, aplicada_en) "
                     f"VALUES ({version}, '{nombre}', strftime('%Y-%m-%dT%H:%M:%SZ', 'now'));\nCOMMIT;")
            try:
                c.executescript(guion)
            except sqlite3.Error:
                if c.in_transaction:
                    c.execute("ROLLBACK")
                if c.execute("SELECT 1 FROM schema_version WHERE version = ?", (version,)).fetchone():
                    continue  # otro proceso la aplicó justo antes
                raise
            aplicadas.append(version)
    return aplicadas
