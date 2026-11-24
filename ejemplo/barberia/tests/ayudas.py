"""Ayudas comunes de las pruebas: reloj controlable y constantes ficticias."""
import threading
from datetime import datetime, timedelta

from app.citas.dominio import ZONA

CLAVE_DE_PRUEBA = "clave-solo-para-pruebas-de-la-barberia-0001"  # pragma: allowlist secret
CONTRASENA_DE_PRUEBA = "contrasena-ficticia-123"  # pragma: allowlist secret
AHORA = datetime(2026, 12, 1, 9, 0, tzinfo=ZONA)  # martes por la mañana


class Reloj:
    """Reloj que se puede mover a mano para probar vencimientos y ventanas de tiempo."""

    def __init__(self, ahora=AHORA):
        self.ahora = ahora

    def __call__(self):
        return self.ahora

    def avanzar(self, **tiempo):
        self.ahora += timedelta(**tiempo)


def a_las(hora, minuto=0, dia=1):
    return datetime(2026, 12, dia, hora, minuto, tzinfo=ZONA)


def lanzar_en_paralelo(hilos, accion):
    """Lanza `hilos` hilos que arrancan juntos con accion(i). Devuelve una lista de (resultado, error)."""
    barrera = threading.Barrier(hilos)
    resultados = [None] * hilos

    def tarea(i):
        barrera.wait()
        try:
            resultados[i] = (accion(i), None)
        except Exception as error:  # se devuelve para que la prueba decida si era un error esperado
            resultados[i] = (None, error)

    lanzados = [threading.Thread(target=tarea, args=(i,)) for i in range(hilos)]
    for h in lanzados:
        h.start()
    for h in lanzados:
        h.join(timeout=60)
    return resultados
