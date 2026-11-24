"""Limitador por ventana de tiempo deslizante (por ejemplo, por dirección de red). Reloj inyectable."""
import ipaddress
import threading
from datetime import timedelta

from app.compartido.errores import DemasiadasSolicitudes
from app.compartido.reloj import reloj_real

_MAXIMO_DE_CLAVES_EN_MEMORIA = 10_000


def clave_de_direccion(texto):
    """Forma canónica de una dirección para usarla de clave: una IPv4 y su versión mapeada a IPv6
    (::ffff:203.0.113.5) son la misma, y una IPv6 se escribe siempre igual. Lo que no sea una IP se usa tal cual."""
    if not texto:
        return "desconocida"
    try:
        ip = ipaddress.ip_address(texto.split("%", 1)[0])  # sin el identificador de interfaz (fe80::1%eth0)
    except ValueError:
        return texto
    if ip.version == 6 and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    return ip.compressed


class LimitePorVentana:
    """Permite `maximo` usos por clave dentro de `ventana`; el siguiente lanza DemasiadasSolicitudes."""

    def __init__(self, maximo, ventana: timedelta, reloj=reloj_real):
        self._maximo = maximo
        self._ventana = ventana
        self._reloj = reloj
        self._usos = {}
        self._cerrojo = threading.Lock()

    def _recientes(self, clave, ahora):
        recientes = [t for t in self._usos.get(clave, []) if ahora - t < self._ventana]
        if recientes:
            self._usos[clave] = recientes
        else:
            self._usos.pop(clave, None)
        return recientes

    def consumir(self, clave):
        with self._cerrojo:
            ahora = self._reloj()
            if len(self._usos) > _MAXIMO_DE_CLAVES_EN_MEMORIA:  # limpieza para que la memoria no crezca sin fin
                for otra in list(self._usos):
                    self._recientes(otra, ahora)
            if len(self._recientes(clave, ahora)) >= self._maximo:
                raise DemasiadasSolicitudes()
            self._usos.setdefault(clave, []).append(ahora)
