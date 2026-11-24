"""Límite de intentos fallidos de inicio de sesión: 5 por correo dentro de una ventana de 15 minutos."""
import threading
from datetime import timedelta

from app.compartido.reloj import reloj_real

_LIMITE_DE_CORREOS_EN_MEMORIA = 10_000


class LimiteDeIntentos:
    def __init__(self, reloj=reloj_real, maximo=5, ventana=timedelta(minutes=15)):
        self._reloj = reloj
        self._maximo = maximo
        self._ventana = ventana
        self._fallos = {}
        self._cerrojo = threading.Lock()

    def _recientes(self, correo):
        ahora = self._reloj()
        recientes = [t for t in self._fallos.get(correo, []) if ahora - t < self._ventana]
        if recientes:
            self._fallos[correo] = recientes
        else:
            self._fallos.pop(correo, None)
        return recientes

    def bloqueado(self, correo):
        with self._cerrojo:
            return len(self._recientes(correo)) >= self._maximo

    def registrar_fallo(self, correo):
        with self._cerrojo:
            if len(self._fallos) > _LIMITE_DE_CORREOS_EN_MEMORIA:
                for otro in list(self._fallos):
                    self._recientes(otro)
            self._fallos.setdefault(correo, []).append(self._reloj())

    def reiniciar(self, correo):
        with self._cerrojo:
            self._fallos.pop(correo, None)
