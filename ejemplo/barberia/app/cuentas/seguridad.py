"""Contraseñas (scrypt) y tokens de sesión firmados con HMAC-SHA256. Solo biblioteca estándar."""
import hashlib
import hmac
import os
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.compartido.reloj import reloj_real
from app.cuentas.dominio import SesionInvalida

N, R, P = 2**14, 8, 1
LARGO_DE_SAL = 16
LARGO_DE_HASH = 32
_hash_falso = []


def _derivar(contrasena, sal, n, r, p):
    return hashlib.scrypt(contrasena.encode("utf-8"), salt=sal, n=n, r=r, p=p, dklen=LARGO_DE_HASH,
                          maxmem=256 * n * r)


def hashear_contrasena(contrasena):
    """Texto 'scrypt$N$r$p$sal$hash' (sal y hash en hexadecimal) con una sal aleatoria nueva."""
    sal = os.urandom(LARGO_DE_SAL)
    return f"scrypt${N}${R}${P}${sal.hex()}${_derivar(contrasena, sal, N, R, P).hex()}"


def verificar_contrasena(contrasena, almacenado):
    try:
        nombre, n, r, p, sal, esperado = almacenado.split("$")
        n, r, p = int(n), int(r), int(p)
        sal, esperado = bytes.fromhex(sal), bytes.fromhex(esperado)
        # Se acotan los parámetros para que un texto dañado no pida memoria o tiempo desmedidos.
        if nombre != "scrypt" or not (1 < n <= 2**16 and n & (n - 1) == 0 and 0 < r <= 16 and 0 < p <= 4):
            return False
        calculado = _derivar(contrasena, sal, n, r, p)
    except (ValueError, TypeError, AttributeError):
        return False
    return hmac.compare_digest(calculado, esperado)


def hash_falso():
    """Un hash válido de una contraseña que nadie conoce: sirve para gastar el mismo tiempo con correos inexistentes."""
    if not _hash_falso:
        _hash_falso.append(hashear_contrasena(os.urandom(16).hex()))
    return _hash_falso[0]


@dataclass(frozen=True)
class Sesion:
    token: str
    expira_en: datetime


class EmisorDeTokens:
    """Token con formato usuario_id.expiracion.firma; la expiración va en segundos desde 1970."""

    def __init__(self, clave, reloj=reloj_real, duracion=timedelta(hours=8)):
        if not clave:
            raise ValueError("La clave de firma no puede estar vacía.")
        self._clave = clave.encode("utf-8")
        self._reloj = reloj
        self._duracion = duracion

    def _firmar(self, texto):
        return hmac.new(self._clave, texto.encode("utf-8"), hashlib.sha256).hexdigest()

    def emitir(self, usuario_id):
        if not usuario_id or "." in usuario_id:
            raise ValueError("El id de usuario no puede estar vacío ni contener puntos.")
        expira_en = self._reloj() + self._duracion
        texto = f"{usuario_id}.{int(expira_en.timestamp())}"
        return Sesion(token=f"{texto}.{self._firmar(texto)}", expira_en=expira_en)

    def verificar(self, token):
        """Devuelve el id del usuario o lanza SesionInvalida si el token está alterado o venció."""
        partes = token.split(".") if isinstance(token, str) else []
        if len(partes) != 3 or not partes[0]:
            raise SesionInvalida()
        usuario_id, expiracion, firma = partes
        esperada = self._firmar(f"{usuario_id}.{expiracion}")
        if not hmac.compare_digest(esperada.encode("utf-8"), firma.encode("utf-8")):
            raise SesionInvalida()
        try:
            vence = int(expiracion)
        except ValueError:
            raise SesionInvalida() from None
        if int(self._reloj().timestamp()) >= vence:
            raise SesionInvalida()
        return usuario_id
