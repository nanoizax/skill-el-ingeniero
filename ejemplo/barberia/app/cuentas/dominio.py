"""Reglas de las cuentas. Esta capa no conoce la API ni la base de datos."""
import re
from dataclasses import dataclass

from app.compartido.errores import DatosInvalidos, ErrorDeNegocio
from app.compartido.roles import BARBERO, RECEPCION
from app.compartido.validacion import texto_valido

MIN_CONTRASENA = 10
MAX_CONTRASENA = 200
MAX_NOMBRE = 120
MAX_CORREO = 254
ROLES_DE_PERSONAL = (BARBERO, RECEPCION)
NOMBRE_ANONIMIZADO = "Cliente anonimizado"
DOMINIO_ANONIMO = "anonimo.invalid"
# Un texto sin la forma 'scrypt$...': nunca verifica ninguna contraseña, así la cuenta queda inutilizable.
HASH_INUTILIZABLE = "anonimizado"
_FORMATO_DE_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class CredencialesInvalidas(ErrorDeNegocio):
    codigo = "credenciales_invalidas"
    tipo = "no_autenticado"

    def __init__(self):
        # Mismo texto para correo inexistente y contraseña mala: no se revela qué correos tienen cuenta.
        super().__init__("Correo o contraseña incorrectos")


class CorreoYaRegistrado(ErrorDeNegocio):
    codigo = "correo_ya_registrado"
    tipo = "conflicto"


class ContrasenaDebil(ErrorDeNegocio):
    codigo = "contrasena_debil"


class DemasiadosIntentos(ErrorDeNegocio):
    codigo = "demasiados_intentos"
    tipo = "limite"

    def __init__(self):
        super().__init__("Demasiados intentos fallidos. Espera 15 minutos e intenta de nuevo.")


class NoAutorizado(ErrorDeNegocio):
    codigo = "no_autorizado"
    tipo = "prohibido"


class SesionInvalida(ErrorDeNegocio):
    codigo = "sesion_invalida"
    tipo = "no_autenticado"

    def __init__(self):
        super().__init__("Tu sesión no es válida o venció. Inicia sesión de nuevo.")


class UsuarioNoEncontrado(ErrorDeNegocio):
    codigo = "usuario_no_encontrado"
    tipo = "no_encontrado"


@dataclass(frozen=True)
class Usuario:
    id: str
    nombre: str
    correo: str
    rol: str
    contrasena_hash: str


def esta_anonimizado(usuario):
    return usuario.contrasena_hash == HASH_INUTILIZABLE


def normalizar_correo(correo):
    return correo.strip().lower()


def validar_credenciales_de_entrada(correo, contrasena):
    """Para el inicio de sesión: solo el formato y el largo (la contraseña se compara, no se evalúa)."""
    texto_valido(correo, "El correo", MAX_CORREO)
    texto_valido(contrasena, "La contraseña", MAX_CONTRASENA, permitir_formato=True)


def validar_registro(nombre, correo, contrasena):
    """Devuelve (nombre, correo) limpios o lanza el error que corresponda."""
    nombre = texto_valido(nombre, "El nombre", MAX_NOMBRE).strip()
    correo = normalizar_correo(texto_valido(correo, "El correo", MAX_CORREO))
    texto_valido(contrasena, "La contraseña", MAX_CONTRASENA, permitir_formato=True)
    if not nombre:
        raise DatosInvalidos("Escribe tu nombre.")
    if not _FORMATO_DE_CORREO.match(correo):
        raise DatosInvalidos("Escribe un correo válido.")
    if len(contrasena) < MIN_CONTRASENA:
        raise ContrasenaDebil(f"La contraseña debe tener al menos {MIN_CONTRASENA} caracteres.")
    return nombre, correo
