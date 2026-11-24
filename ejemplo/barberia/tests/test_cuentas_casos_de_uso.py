"""Casos de uso de cuentas: registro, personal, inicio de sesión y límite de intentos."""
import pytest
from ayudas import CLAVE_DE_PRUEBA, CONTRASENA_DE_PRUEBA, Reloj

from app.compartido.errores import DatosInvalidos
from app.compartido.roles import BARBERO, CLIENTE, DUENO, RECEPCION, Actor
from app.cuentas.casos_de_uso import CrearDueno, CrearPersonal, IniciarSesion, RegistrarCliente, UsuarioDeSesion
from app.cuentas.dominio import (
    ContrasenaDebil,
    CorreoYaRegistrado,
    CredencialesInvalidas,
    DemasiadosIntentos,
    NoAutorizado,
    SesionInvalida,
)
from app.cuentas.intentos import LimiteDeIntentos
from app.cuentas.repositorio import RepositorioDeUsuariosEnMemoria
from app.cuentas.seguridad import EmisorDeTokens

MENSAJE_DE_FALLO = "Correo o contraseña incorrectos"
MALA = "contrasena-equivocada"  # pragma: allowlist secret


@pytest.fixture
def usuarios():
    return RepositorioDeUsuariosEnMemoria()


@pytest.fixture
def sesion(usuarios):
    reloj = Reloj()
    RegistrarCliente(usuarios).ejecutar("Ana Pérez", "ana@ejemplo.test", CONTRASENA_DE_PRUEBA)
    emisor = EmisorDeTokens(CLAVE_DE_PRUEBA, reloj=reloj)
    return IniciarSesion(usuarios, LimiteDeIntentos(reloj), emisor), reloj


def fallar(iniciar, veces, correo="ana@ejemplo.test"):
    for _ in range(veces):
        with pytest.raises(CredencialesInvalidas):
            iniciar.ejecutar(correo, MALA)


def test_registrar_cliente_crea_un_usuario_con_rol_cliente(usuarios):
    usuario = RegistrarCliente(usuarios).ejecutar("  Ana Pérez ", " ANA@Ejemplo.test ", CONTRASENA_DE_PRUEBA)
    assert usuario.rol == CLIENTE and usuario.nombre == "Ana Pérez" and usuario.correo == "ana@ejemplo.test"
    assert usuarios.por_id(usuario.id) == usuario


def test_no_se_registra_dos_veces_el_mismo_correo_aunque_cambien_las_mayusculas(usuarios):
    RegistrarCliente(usuarios).ejecutar("Ana", "ana@ejemplo.test", CONTRASENA_DE_PRUEBA)
    with pytest.raises(CorreoYaRegistrado):
        RegistrarCliente(usuarios).ejecutar("Otra Ana", "ANA@ejemplo.test", CONTRASENA_DE_PRUEBA)


def test_la_contrasena_necesita_al_menos_10_caracteres(usuarios):
    with pytest.raises(ContrasenaDebil):
        RegistrarCliente(usuarios).ejecutar("Ana", "ana@ejemplo.test", "123456789")  # 9: límite  # pragma: allowlist secret
    usuario = RegistrarCliente(usuarios).ejecutar("Ana", "ana@ejemplo.test", "1234567890")  # pragma: allowlist secret
    assert usuario.rol == CLIENTE


@pytest.mark.parametrize("nombre,correo", [("", "a@ejemplo.test"), ("   ", "a@ejemplo.test"),
                                           ("Ana", "sin-arroba"), ("Ana", "a@sin-punto"), ("Ana", "")])
def test_nombre_o_correo_invalidos_se_rechazan(usuarios, nombre, correo):
    with pytest.raises(DatosInvalidos):
        RegistrarCliente(usuarios).ejecutar(nombre, correo, CONTRASENA_DE_PRUEBA)


@pytest.mark.parametrize("rol", [BARBERO, RECEPCION])
def test_el_dueno_crea_personal(usuarios, rol):
    usuario = CrearPersonal(usuarios).ejecutar(Actor("d-1", DUENO), "Luis", "luis@ejemplo.test", CONTRASENA_DE_PRUEBA, rol)
    assert usuario.rol == rol


@pytest.mark.parametrize("rol_del_actor", [RECEPCION, BARBERO, CLIENTE])
def test_solo_el_dueno_crea_personal(usuarios, rol_del_actor):
    with pytest.raises(NoAutorizado):
        CrearPersonal(usuarios).ejecutar(Actor("x", rol_del_actor), "Luis", "l@ejemplo.test", CONTRASENA_DE_PRUEBA, BARBERO)
    assert usuarios.por_correo("l@ejemplo.test") is None


@pytest.mark.parametrize("rol", [DUENO, CLIENTE, "admin", ""])
def test_el_personal_solo_puede_ser_barbero_o_recepcion(usuarios, rol):
    with pytest.raises(DatosInvalidos):
        CrearPersonal(usuarios).ejecutar(Actor("d-1", DUENO), "Luis", "l@ejemplo.test", CONTRASENA_DE_PRUEBA, rol)


def test_crear_dueno_deja_un_usuario_con_rol_dueno(usuarios):
    assert CrearDueno(usuarios).ejecutar("Don Mario", "mario@ejemplo.test", CONTRASENA_DE_PRUEBA).rol == DUENO


def test_iniciar_sesion_devuelve_un_token_que_identifica_al_usuario(usuarios, sesion):
    iniciar, reloj = sesion
    resultado = iniciar.ejecutar("ANA@ejemplo.test", CONTRASENA_DE_PRUEBA)
    emisor = EmisorDeTokens(CLAVE_DE_PRUEBA, reloj=reloj)
    assert UsuarioDeSesion(usuarios, emisor).ejecutar(resultado.token).correo == "ana@ejemplo.test"


def test_un_token_de_un_usuario_que_ya_no_existe_se_rechaza(usuarios):
    emisor = EmisorDeTokens(CLAVE_DE_PRUEBA, reloj=Reloj())
    with pytest.raises(SesionInvalida):
        UsuarioDeSesion(usuarios, emisor).ejecutar(emisor.emitir("fantasma").token)


def test_sexto_intento_fallido_queda_bloqueado(sesion):
    iniciar, _ = sesion
    fallar(iniciar, 5)
    with pytest.raises(DemasiadosIntentos):
        iniciar.ejecutar("ana@ejemplo.test", MALA)
    with pytest.raises(DemasiadosIntentos):  # bloqueada incluso con la contraseña correcta
        iniciar.ejecutar("ana@ejemplo.test", CONTRASENA_DE_PRUEBA)


def test_el_bloqueo_es_por_correo_y_se_levanta_a_los_15_minutos(sesion, usuarios):
    iniciar, reloj = sesion
    RegistrarCliente(usuarios).ejecutar("Luis", "luis@ejemplo.test", CONTRASENA_DE_PRUEBA)
    fallar(iniciar, 5)
    assert iniciar.ejecutar("luis@ejemplo.test", CONTRASENA_DE_PRUEBA).token  # otro correo no se afecta
    reloj.avanzar(minutes=14, seconds=59)  # límite: todavía bloqueada
    with pytest.raises(DemasiadosIntentos):
        iniciar.ejecutar("ana@ejemplo.test", CONTRASENA_DE_PRUEBA)
    reloj.avanzar(seconds=1)
    assert iniciar.ejecutar("ana@ejemplo.test", CONTRASENA_DE_PRUEBA).token


def test_un_acierto_reinicia_la_cuenta_de_fallos(sesion):
    iniciar, _ = sesion
    fallar(iniciar, 4)
    assert iniciar.ejecutar("ana@ejemplo.test", CONTRASENA_DE_PRUEBA).token
    fallar(iniciar, 5)  # otra vez 5 fallos permitidos
    with pytest.raises(DemasiadosIntentos):
        iniciar.ejecutar("ana@ejemplo.test", MALA)


def test_correo_inexistente_y_contrasena_mala_dan_el_mismo_mensaje(sesion):
    iniciar, _ = sesion
    with pytest.raises(CredencialesInvalidas) as sin_correo:
        iniciar.ejecutar("nadie@ejemplo.test", CONTRASENA_DE_PRUEBA)
    with pytest.raises(CredencialesInvalidas) as mala_clave:
        iniciar.ejecutar("ana@ejemplo.test", MALA)
    assert sin_correo.value.mensaje == mala_clave.value.mensaje == MENSAJE_DE_FALLO
    assert sin_correo.value.codigo == mala_clave.value.codigo


def test_un_correo_inexistente_tambien_se_bloquea_para_no_revelar_si_existe(sesion):
    iniciar, _ = sesion
    fallar(iniciar, 5, correo="nadie@ejemplo.test")
    with pytest.raises(DemasiadosIntentos):
        iniciar.ejecutar("nadie@ejemplo.test", MALA)
