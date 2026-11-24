"""Errores de negocio: tienen un código estable para la API y un mensaje que se puede mostrar a la persona."""


class ErrorDeNegocio(Exception):
    codigo = "error_de_negocio"
    # Categoría del error; la capa de la API la traduce a un código HTTP (el dominio no sabe de HTTP).
    # Valores: invalido, no_autenticado, prohibido, no_encontrado, conflicto, limite.
    tipo = "invalido"

    def __init__(self, mensaje):
        super().__init__(mensaje)
        self.mensaje = mensaje


class DatosInvalidos(ErrorDeNegocio):
    codigo = "datos_invalidos"


class ConfiguracionInvalida(RuntimeError):
    """La aplicación no puede arrancar por una variable de entorno que falta o está mal."""


class DemasiadasSolicitudes(ErrorDeNegocio):
    codigo = "demasiadas_solicitudes"
    tipo = "limite"

    def __init__(self):
        super().__init__("Hiciste demasiadas solicitudes desde tu dirección. Espera un rato e intenta de nuevo.")
