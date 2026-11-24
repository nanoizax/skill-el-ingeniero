"""Adaptador SQLite del repositorio de cobros."""
import sqlite3

from app.cobros.dominio import CitaYaCobrada, Cobro
from app.compartido.db import a_texto_utc, desde_texto_utc

_COLUMNAS = "id, cita_id, barbero_id, cita_inicio, monto, medio, registrado_en"


def _a_cobro(fila):
    return Cobro(id=fila[0], cita_id=fila[1], barbero_id=fila[2], cita_inicio=desde_texto_utc(fila[3]),
                 monto=fila[4], medio=fila[5], registrado_en=desde_texto_utc(fila[6]))


class RepositorioDeCobrosSqlite:
    def __init__(self, base):
        self._base = base

    def guardar(self, cobro):
        try:
            with self._base.conexion() as c:
                c.execute(f"INSERT INTO cobros ({_COLUMNAS}) VALUES (?, ?, ?, ?, ?, ?, ?)",
                          (cobro.id, cobro.cita_id, cobro.barbero_id, a_texto_utc(cobro.cita_inicio), cobro.monto,
                           cobro.medio, a_texto_utc(cobro.registrado_en)))
        except sqlite3.IntegrityError as error:
            if "cobros.cita_id" in str(error):  # la restricción UNIQUE: la cita ya tenía su cobro
                raise CitaYaCobrada("Esa cita ya fue cobrada.") from None
            raise

    def de_la_cita(self, cita_id):
        with self._base.conexion() as c:
            fila = c.execute(f"SELECT {_COLUMNAS} FROM cobros WHERE cita_id = ?", (cita_id,)).fetchone()
        return _a_cobro(fila) if fila else None

    def en_rango(self, desde, hasta):
        with self._base.conexion() as c:
            filas = c.execute(f"SELECT {_COLUMNAS} FROM cobros WHERE cita_inicio >= ? AND cita_inicio < ? "
                              "ORDER BY cita_inicio, id", (a_texto_utc(desde), a_texto_utc(hasta))).fetchall()
        return [_a_cobro(f) for f in filas]
