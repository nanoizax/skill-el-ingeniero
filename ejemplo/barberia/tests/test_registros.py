"""Los registros del servidor guardan el detalle de un error, pero nunca el cuerpo de la solicitud ni el token de sesión."""
import logging

from app.compartido.roles import CLIENTE


def test_un_error_inesperado_se_registra_sin_datos_sensibles(mundo, caplog):
    class Roto:
        def ejecutar(self, *args, **kwargs):
            raise RuntimeError("fallo interno de prueba")

    mundo.servicios.agendar_cita = Roto()
    _, cabeceras = mundo.entrar(CLIENTE)
    token = cabeceras["Authorization"].split(" ", 1)[1]
    solicitud = {"barbero_id": "ana", "cliente_id": "cliente-1", "inicio": "2026-12-01T15:00:00-03:00",
                 "duracion_minutos": 30, "nota": "texto-muy-sensible-987"}
    with caplog.at_level(logging.ERROR, logger="barberia"):
        r = mundo.http.post("/citas", json=solicitud, headers=cabeceras)
    assert r.status_code == 500
    assert "fallo interno de prueba" in caplog.text  # el detalle sí queda, para quien mantiene el sistema
    assert "texto-muy-sensible-987" not in caplog.text
    assert token not in caplog.text
