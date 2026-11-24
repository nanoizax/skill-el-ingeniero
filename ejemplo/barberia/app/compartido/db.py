"""Conexión a SQLite con el módulo estándar: modo WAL, claves foráneas activas y transacciones inmediatas."""
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone

from app.compartido.errores import ConfiguracionInvalida

MEMORIA = ":memory:"
FORMATO_UTC = "%Y-%m-%dT%H:%M:%S.%f"  # ancho fijo: el orden del texto es el orden del tiempo
_PREFIJO = "sqlite:///"


def ruta_desde_url(url):
    """'sqlite:///ruta' (o 'sqlite:////ruta/absoluta'), una ruta suelta o ':memory:'."""
    texto = (url or "").strip()
    if texto.startswith(_PREFIJO):
        texto = texto[len(_PREFIJO):]
    elif "://" in texto:
        raise ConfiguracionInvalida("DATABASE_URL debe ser sqlite:///ruta, una ruta de archivo o :memory:.")
    if not texto:
        raise ConfiguracionInvalida("DATABASE_URL está vacía: indica dónde está la base (sqlite:///barberia.db).")
    return texto


def a_texto_utc(momento):
    if momento.tzinfo is None:
        raise ValueError("Una hora sin zona horaria no se puede guardar.")
    return momento.astimezone(timezone.utc).strftime(FORMATO_UTC)


def desde_texto_utc(texto):
    return datetime.strptime(texto, FORMATO_UTC).replace(tzinfo=timezone.utc)


class BaseDeDatos:
    """En archivo abre una conexión por operación (varios hilos escriben sin pisarse gracias a la espera por
    bloqueo); en memoria comparte una sola conexión protegida por un cerrojo."""

    def __init__(self, url):
        self.ruta = ruta_desde_url(url)
        self._en_memoria = self.ruta == MEMORIA
        self._cerrojo = threading.RLock()
        self._compartida = self._abrir() if self._en_memoria else None

    def _abrir(self):
        # isolation_level=None: las transacciones se manejan a mano (BEGIN IMMEDIATE) y no a escondidas.
        conexion = sqlite3.connect(self.ruta, timeout=30, isolation_level=None, check_same_thread=False)
        conexion.execute("PRAGMA foreign_keys = ON")
        conexion.execute("PRAGMA journal_mode = WAL")
        # Lo borrado se sobrescribe con ceros: así un dato anonimizado no queda legible en las páginas libres.
        conexion.execute("PRAGMA secure_delete = ON")
        return conexion

    @contextmanager
    def conexion(self):
        if self._en_memoria:
            with self._cerrojo:
                yield self._compartida
            return
        conexion = self._abrir()
        try:
            yield conexion
        finally:
            conexion.close()

    @contextmanager
    def transaccion(self):
        """BEGIN IMMEDIATE toma el derecho de escribir desde el principio: lo que se revisa dentro sigue siendo
        cierto hasta el COMMIT. Si algo falla (o se lanza un error de negocio) se deshace todo."""
        with self.conexion() as conexion:
            conexion.execute("BEGIN IMMEDIATE")
            try:
                yield conexion
                conexion.execute("COMMIT")
            except BaseException:
                if conexion.in_transaction:
                    conexion.execute("ROLLBACK")
                raise
