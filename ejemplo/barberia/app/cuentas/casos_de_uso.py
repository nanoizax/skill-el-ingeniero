"""Casos de uso de las cuentas: una acción por clase."""
import uuid
from dataclasses import replace

from app.compartido.errores import DatosInvalidos
from app.compartido.roles import CLIENTE, DUENO
from app.cuentas.dominio import (
    DOMINIO_ANONIMO,
    HASH_INUTILIZABLE,
    NOMBRE_ANONIMIZADO,
    ROLES_DE_PERSONAL,
    CorreoYaRegistrado,
    CredencialesInvalidas,
    DemasiadosIntentos,
    NoAutorizado,
    SesionInvalida,
    Usuario,
    UsuarioNoEncontrado,
    esta_anonimizado,
    normalizar_correo,
    validar_credenciales_de_entrada,
    validar_registro,
)
from app.cuentas.seguridad import hash_falso, hashear_contrasena, verificar_contrasena


def _crear_usuario(usuarios, nombre, correo, contrasena, rol):
    nombre, correo = validar_registro(nombre, correo, contrasena)
    if usuarios.por_correo(correo):
        raise CorreoYaRegistrado("Ese correo ya tiene una cuenta.")
    usuario = Usuario(id=str(uuid.uuid4()), nombre=nombre, correo=correo, rol=rol,
                      contrasena_hash=hashear_contrasena(contrasena))
    usuarios.guardar(usuario)  # el repositorio vuelve a garantizar la unicidad si dos registros llegan a la vez
    return usuario


class RegistrarCliente:
    def __init__(self, usuarios, limite_por_direccion=None):
        self._usuarios = usuarios
        self._limite = limite_por_direccion

    def ejecutar(self, nombre, correo, contrasena, direccion=None):
        if self._limite is not None and direccion is not None:
            self._limite.consumir(direccion)  # máximo de registros por hora desde una misma dirección
        return _crear_usuario(self._usuarios, nombre, correo, contrasena, CLIENTE)


class CrearPersonal:
    def __init__(self, usuarios):
        self._usuarios = usuarios

    def ejecutar(self, actor, nombre, correo, contrasena, rol):
        if actor.rol != DUENO:
            raise NoAutorizado("Solo el dueño puede crear personal.")
        if rol not in ROLES_DE_PERSONAL:
            raise DatosInvalidos("El rol del personal debe ser barbero o recepcion.")
        return _crear_usuario(self._usuarios, nombre, correo, contrasena, rol)


class CrearDueno:
    """Se usa solo desde el script de arranque (scripts/crear_dueno.py): sin dueño nadie puede crear personal."""

    def __init__(self, usuarios):
        self._usuarios = usuarios

    def ejecutar(self, nombre, correo, contrasena):
        return _crear_usuario(self._usuarios, nombre, correo, contrasena, DUENO)


class IniciarSesion:
    def __init__(self, usuarios, limite, emisor, limite_por_direccion=None):
        self._usuarios = usuarios
        self._limite = limite
        self._emisor = emisor
        self._limite_por_direccion = limite_por_direccion

    def ejecutar(self, correo, contrasena, direccion=None):
        if self._limite_por_direccion is not None and direccion is not None:
            self._limite_por_direccion.consumir(direccion)  # máximo de intentos por dirección, además del de por correo
        validar_credenciales_de_entrada(correo, contrasena)
        clave = normalizar_correo(correo)
        if self._limite.bloqueado(clave):
            raise DemasiadosIntentos()
        usuario = self._usuarios.por_correo(clave)
        # Con correo inexistente se verifica contra un hash falso: tarda lo mismo y no delata qué correos existen.
        acierto = verificar_contrasena(contrasena, usuario.contrasena_hash if usuario else hash_falso())
        if usuario is None or not acierto:
            self._limite.registrar_fallo(clave)
            raise CredencialesInvalidas()
        self._limite.reiniciar(clave)
        return self._emisor.emitir(usuario.id)


class UsuarioDeSesion:
    def __init__(self, usuarios, emisor):
        self._usuarios = usuarios
        self._emisor = emisor

    def ejecutar(self, token):
        usuario = self._usuarios.por_id(self._emisor.verificar(token))
        if usuario is None or esta_anonimizado(usuario):  # una cuenta anonimizada pierde también sus sesiones abiertas
            raise SesionInvalida()
        return usuario


class AnonimizarCliente:
    """Borrado a pedido: quita el nombre y el correo, deja la contraseña inutilizable y conserva el id para que las
    citas y los cobros sigan existiendo sin datos personales."""

    def __init__(self, usuarios):
        self._usuarios = usuarios

    def ejecutar(self, correo):
        usuario = self._usuarios.por_correo(correo) if isinstance(correo, str) else None
        if usuario is None:
            raise UsuarioNoEncontrado("No hay ninguna cuenta con ese correo.")
        if usuario.rol != CLIENTE:
            raise DatosInvalidos("Solo se anonimizan cuentas de clientes.")
        anonimo = replace(usuario, nombre=NOMBRE_ANONIMIZADO, correo=f"anon-{usuario.id}@{DOMINIO_ANONIMO}",
                          contrasena_hash=HASH_INUTILIZABLE)
        self._usuarios.guardar(anonimo)
        return anonimo
