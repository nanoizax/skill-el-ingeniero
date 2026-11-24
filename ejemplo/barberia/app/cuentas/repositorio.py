"""El repositorio de usuarios: la interfaz que usan los casos de uso y su adaptador en memoria (para las pruebas)."""
import threading
from typing import Optional, Protocol

from app.cuentas.dominio import CorreoYaRegistrado, Usuario, normalizar_correo


class RepositorioDeUsuarios(Protocol):
    def guardar(self, usuario: Usuario) -> None: ...

    def por_correo(self, correo: str) -> Optional[Usuario]: ...

    def por_id(self, usuario_id: str) -> Optional[Usuario]: ...


class RepositorioDeUsuariosEnMemoria:
    def __init__(self):
        self._por_id = {}
        self._cerrojo = threading.Lock()

    def guardar(self, usuario):
        with self._cerrojo:
            if any(u.correo == usuario.correo and u.id != usuario.id for u in self._por_id.values()):
                raise CorreoYaRegistrado("Ese correo ya tiene una cuenta.")
            self._por_id[usuario.id] = usuario

    def por_correo(self, correo):
        correo = normalizar_correo(correo)
        return next((u for u in self._por_id.values() if u.correo == correo), None)

    def por_id(self, usuario_id):
        return self._por_id.get(usuario_id)
