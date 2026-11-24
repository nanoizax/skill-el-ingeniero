"""Raíz de composición: aquí (y solo aquí) se eligen los adaptadores y se arman los casos de uso."""
import os
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from app.citas.casos_de_uso import (
    AgendarCita,
    AgendarCitaPorUsuario,
    CancelarCita,
    MarcarAtendida,
    MoverCita,
    VerAgenda,
    VerMisCitas,
)
from app.citas.repositorio import RepositorioEnMemoria
from app.citas.repositorio_sqlite import RepositorioDeCitasSqlite
from app.cobros.casos_de_uso import CierreDeCaja, RegistrarCobro
from app.cobros.repositorio import RepositorioDeCobrosEnMemoria
from app.cobros.repositorio_sqlite import RepositorioDeCobrosSqlite
from app.compartido.db import BaseDeDatos
from app.compartido.errores import ConfiguracionInvalida
from app.compartido.limites import LimitePorVentana
from app.compartido.migraciones import aplicar_migraciones
from app.compartido.reloj import reloj_real
from app.cuentas.casos_de_uso import CrearPersonal, IniciarSesion, RegistrarCliente, UsuarioDeSesion
from app.cuentas.intentos import LimiteDeIntentos
from app.cuentas.repositorio import RepositorioDeUsuariosEnMemoria
from app.cuentas.repositorio_sqlite import RepositorioDeUsuariosSqlite
from app.cuentas.seguridad import EmisorDeTokens


@dataclass
class Servicios:
    usuarios: Any
    emisor: Any
    registrar_cliente: Any
    crear_personal: Any
    iniciar_sesion: Any
    usuario_de_sesion: Any
    citas: Any
    agendar_cita: Any
    cancelar_cita: Any
    mover_cita: Any
    marcar_atendida: Any
    ver_agenda: Any
    ver_mis_citas: Any
    cobros: Any
    registrar_cobro: Any
    cierre_de_caja: Any


def construir_servicios(clave, database_url=None, en_memoria=False, reloj=None):
    reloj = reloj or reloj_real
    if en_memoria:  # solo para pruebas: nada se guarda en disco
        usuarios, citas, cobros = RepositorioDeUsuariosEnMemoria(), RepositorioEnMemoria(), RepositorioDeCobrosEnMemoria()
    else:
        url = database_url or os.environ.get("DATABASE_URL")
        if not url:
            raise ConfiguracionInvalida("Falta la variable de entorno DATABASE_URL (por ejemplo sqlite:///barberia.db).")
        base = BaseDeDatos(url)
        aplicar_migraciones(base)  # deja el esquema al día antes de atender solicitudes
        usuarios, citas, cobros = (RepositorioDeUsuariosSqlite(base), RepositorioDeCitasSqlite(base),
                                   RepositorioDeCobrosSqlite(base))
    emisor = EmisorDeTokens(clave, reloj=reloj)
    return Servicios(
        usuarios=usuarios,
        emisor=emisor,
        registrar_cliente=RegistrarCliente(usuarios, LimitePorVentana(10, timedelta(hours=1), reloj)),
        crear_personal=CrearPersonal(usuarios),
        iniciar_sesion=IniciarSesion(usuarios, LimiteDeIntentos(reloj), emisor,
                                     LimitePorVentana(30, timedelta(minutes=15), reloj)),
        usuario_de_sesion=UsuarioDeSesion(usuarios, emisor),
        citas=citas,
        agendar_cita=AgendarCitaPorUsuario(AgendarCita(citas, reloj=reloj), usuarios),
        cancelar_cita=CancelarCita(citas),
        mover_cita=MoverCita(citas, reloj=reloj),
        marcar_atendida=MarcarAtendida(citas, reloj=reloj),
        ver_agenda=VerAgenda(citas, reloj=reloj),
        ver_mis_citas=VerMisCitas(citas),
        cobros=cobros,
        registrar_cobro=RegistrarCobro(cobros, citas, reloj=reloj),
        cierre_de_caja=CierreDeCaja(cobros, reloj=reloj),
    )
