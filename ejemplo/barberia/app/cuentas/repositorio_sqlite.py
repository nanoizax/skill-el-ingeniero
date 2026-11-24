"""Adaptador SQLite del repositorio de usuarios."""
import sqlite3

from app.cuentas.dominio import CorreoYaRegistrado, Usuario, normalizar_correo

_COLUMNAS = "id, nombre, correo, rol, contrasena_hash"


def _a_usuario(fila):
    return Usuario(id=fila[0], nombre=fila[1], correo=fila[2], rol=fila[3], contrasena_hash=fila[4])


class RepositorioDeUsuariosSqlite:
    def __init__(self, base):
        self._base = base

    def guardar(self, usuario):
        try:
            with self._base.conexion() as c:
                c.execute(f"INSERT INTO usuarios ({_COLUMNAS}) VALUES (?, ?, ?, ?, ?) ON CONFLICT (id) DO UPDATE SET "
                          "nombre = excluded.nombre, correo = excluded.correo, rol = excluded.rol, "
                          "contrasena_hash = excluded.contrasena_hash",
                          (usuario.id, usuario.nombre, usuario.correo, usuario.rol, usuario.contrasena_hash))
        except sqlite3.IntegrityError as error:
            if "usuarios.correo" in str(error):  # la restricción UNIQUE: dos registros con el mismo correo
                raise CorreoYaRegistrado("Ese correo ya tiene una cuenta.") from None
            raise

    def por_correo(self, correo):
        with self._base.conexion() as c:
            fila = c.execute(f"SELECT {_COLUMNAS} FROM usuarios WHERE correo = ?", (normalizar_correo(correo),)).fetchone()
        return _a_usuario(fila) if fila else None

    def por_id(self, usuario_id):
        with self._base.conexion() as c:
            fila = c.execute(f"SELECT {_COLUMNAS} FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
        return _a_usuario(fila) if fila else None
