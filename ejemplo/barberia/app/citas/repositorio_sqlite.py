"""Adaptador SQLite del repositorio de citas. Las horas se guardan como texto en UTC."""
from app.citas.dominio import ATENDIDA, CONFIRMADA, BarberoOcupado, Cita, CitaNoModificable, DemasiadasCitas
from app.citas.repositorio import mensaje_de_cita_cerrada, mensaje_de_limite
from app.compartido.db import a_texto_utc, desde_texto_utc

_COLUMNAS = "id, barbero_id, cliente_id, inicio, fin, estado"
_OCUPAN = (CONFIRMADA, ATENDIDA)


def _a_cita(fila):
    return Cita(id=fila[0], barbero_id=fila[1], cliente_id=fila[2], inicio=desde_texto_utc(fila[3]),
                fin=desde_texto_utc(fila[4]), estado=fila[5])


def _guardar(conexion, cita):
    conexion.execute(
        f"INSERT INTO citas ({_COLUMNAS}) VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT (id) DO UPDATE SET "
        "barbero_id = excluded.barbero_id, cliente_id = excluded.cliente_id, inicio = excluded.inicio, "
        "fin = excluded.fin, estado = excluded.estado",
        (cita.id, cita.barbero_id, cita.cliente_id, a_texto_utc(cita.inicio), a_texto_utc(cita.fin), cita.estado))


class RepositorioDeCitasSqlite:
    def __init__(self, base):
        self._base = base

    def obtener(self, cita_id):
        with self._base.conexion() as c:
            fila = c.execute(f"SELECT {_COLUMNAS} FROM citas WHERE id = ?", (cita_id,)).fetchone()
        return _a_cita(fila) if fila else None

    def guardar(self, cita):
        with self._base.conexion() as c:
            _guardar(c, cita)

    def guardar_si_esta_libre(self, cita, limite_de_citas_futuras=None, ahora=None):
        """Revisa y guarda dentro de una sola transacción BEGIN IMMEDIATE: dos solicitudes a la vez no pueden pasar
        ambas la revisión. Una cita existente (mover) se ignora a sí misma y solo se reescribe si sigue confirmada."""
        with self._base.transaccion() as c:
            fila = c.execute("SELECT estado FROM citas WHERE id = ?", (cita.id,)).fetchone()
            if fila is not None and fila[0] != CONFIRMADA:
                raise CitaNoModificable(mensaje_de_cita_cerrada(fila[0]))
            ocupada = c.execute(
                "SELECT 1 FROM citas WHERE barbero_id = ? AND id <> ? AND estado IN (?, ?) "
                "AND inicio < ? AND fin > ? LIMIT 1",
                (cita.barbero_id, cita.id, *_OCUPAN, a_texto_utc(cita.fin), a_texto_utc(cita.inicio))).fetchone()
            if ocupada:
                raise BarberoOcupado("El barbero ya tiene una cita en ese horario.")
            if fila is None and limite_de_citas_futuras is not None:
                (futuras,) = c.execute("SELECT count(*) FROM citas WHERE cliente_id = ? AND estado = ? AND inicio > ?",
                                       (cita.cliente_id, CONFIRMADA, a_texto_utc(ahora))).fetchone()
                if futuras >= limite_de_citas_futuras:
                    raise DemasiadasCitas(mensaje_de_limite(limite_de_citas_futuras))
            _guardar(c, cita)

    def cambiar_estado(self, cita_id, desde, hasta):
        with self._base.conexion() as c:  # una sola sentencia UPDATE: la base la ejecuta de forma atómica
            return c.execute("UPDATE citas SET estado = ? WHERE id = ? AND estado = ?",
                             (hasta, cita_id, desde)).rowcount == 1

    def citas_en_rango(self, desde=None, hasta=None, barbero_id=None, cliente_id=None):
        condiciones, parametros = ["estado IN (?, ?)"], list(_OCUPAN)
        for texto, valor in (("inicio >= ?", desde and a_texto_utc(desde)), ("inicio < ?", hasta and a_texto_utc(hasta)),
                             ("barbero_id = ?", barbero_id), ("cliente_id = ?", cliente_id)):
            if valor is not None:
                condiciones.append(texto)
                parametros.append(valor)
        with self._base.conexion() as c:
            filas = c.execute(f"SELECT {_COLUMNAS} FROM citas WHERE {' AND '.join(condiciones)} "
                              "ORDER BY inicio, id", parametros).fetchall()
        return [_a_cita(f) for f in filas]
