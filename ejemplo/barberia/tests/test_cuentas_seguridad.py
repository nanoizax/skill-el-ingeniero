"""Contraseñas con scrypt y tokens de sesión firmados: lo que se guarda y lo que se rechaza."""
from datetime import timedelta

import pytest
from ayudas import AHORA, CLAVE_DE_PRUEBA, CONTRASENA_DE_PRUEBA, Reloj

from app.cuentas.casos_de_uso import RegistrarCliente
from app.cuentas.dominio import SesionInvalida
from app.cuentas.repositorio import RepositorioDeUsuariosEnMemoria
from app.cuentas.seguridad import EmisorDeTokens, hashear_contrasena, verificar_contrasena


def test_contrasena_no_se_guarda_en_texto():
    repositorio = RepositorioDeUsuariosEnMemoria()
    usuario = RegistrarCliente(repositorio).ejecutar("Ana Pérez", "ana@ejemplo.test", CONTRASENA_DE_PRUEBA)
    guardado = repositorio.por_correo("ana@ejemplo.test")
    assert guardado.contrasena_hash == usuario.contrasena_hash
    assert CONTRASENA_DE_PRUEBA not in guardado.contrasena_hash
    partes = guardado.contrasena_hash.split("$")
    assert partes[:4] == ["scrypt", str(2**14), "8", "1"]
    assert len(partes) == 6 and len(partes[4]) > 0 and len(partes[5]) > 0
    assert verificar_contrasena(CONTRASENA_DE_PRUEBA, guardado.contrasena_hash)


def test_la_misma_contrasena_da_hashes_distintos_por_la_sal():
    assert hashear_contrasena(CONTRASENA_DE_PRUEBA) != hashear_contrasena(CONTRASENA_DE_PRUEBA)


def test_verificar_rechaza_contrasena_mala_y_hash_danado():
    almacenado = hashear_contrasena(CONTRASENA_DE_PRUEBA)
    assert verificar_contrasena(CONTRASENA_DE_PRUEBA, almacenado)
    assert not verificar_contrasena("otra-contrasena-123", almacenado)  # pragma: allowlist secret
    for roto in ("", "texto-cualquiera", "scrypt$x$8$1$aa$bb", "scrypt$16384$8$1$zz$zz", "md5$1$2$3$4$5"):
        assert not verificar_contrasena(CONTRASENA_DE_PRUEBA, roto)


def test_el_token_tiene_el_formato_usuario_expiracion_firma_y_dura_8_horas():
    token = EmisorDeTokens(CLAVE_DE_PRUEBA, reloj=Reloj()).emitir("u-1").token
    usuario, expiracion, firma = token.split(".")
    assert usuario == "u-1" and len(firma) > 20
    assert int(expiracion) == int((AHORA + timedelta(hours=8)).timestamp())


def test_un_token_vigente_se_acepta_hasta_el_ultimo_segundo():
    reloj = Reloj()
    emisor = EmisorDeTokens(CLAVE_DE_PRUEBA, reloj=reloj)
    token = emisor.emitir("u-1").token
    assert emisor.verificar(token) == "u-1"
    reloj.avanzar(hours=7, minutes=59, seconds=59)  # límite: todavía vale
    assert emisor.verificar(token) == "u-1"


def test_token_alterado_se_rechaza():
    emisor = EmisorDeTokens(CLAVE_DE_PRUEBA, reloj=Reloj())
    usuario, expiracion, firma = emisor.emitir("u-1").token.split(".")
    ajeno = EmisorDeTokens("otra-clave-de-pruebas-0002", reloj=Reloj()).emitir("u-1").token  # pragma: allowlist secret
    ultimo = "0" if firma[-1] != "0" else "1"
    alterados = [
        f"u-2.{expiracion}.{firma}",  # otro usuario con la firma de este
        f"{usuario}.{int(expiracion) + 3600}.{firma}",  # vida extendida a mano
        f"{usuario}.{expiracion}.{firma[:-1]}{ultimo}",  # firma con un carácter cambiado
        f"{usuario}.{expiracion}.",  # sin firma
        ajeno,  # firmado con otra clave
        "", "basura", "a.b", "a.b.c.d", f"{usuario}.no-es-numero.{firma}",
    ]
    for token in alterados:
        with pytest.raises(SesionInvalida):
            emisor.verificar(token)


def test_token_vencido_se_rechaza():
    reloj = Reloj()
    emisor = EmisorDeTokens(CLAVE_DE_PRUEBA, reloj=reloj)
    token = emisor.emitir("u-1").token
    reloj.avanzar(hours=8)  # límite: a las 8 horas exactas ya venció
    with pytest.raises(SesionInvalida):
        emisor.verificar(token)
    reloj.avanzar(seconds=1)
    with pytest.raises(SesionInvalida):
        emisor.verificar(token)


def test_el_emisor_exige_una_clave():
    with pytest.raises(ValueError):
        EmisorDeTokens("")
