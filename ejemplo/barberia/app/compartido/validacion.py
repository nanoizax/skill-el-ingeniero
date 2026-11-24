"""Validación de textos que llegan de afuera: tipo, largo, codificación y caracteres de control."""
import unicodedata

from app.compartido.errores import DatosInvalidos

MAXIMO_DE_ID = 64


def texto_valido(valor, campo, maximo, minimo=0, permitir_formato=False):
    """Devuelve el mismo texto si es una cadena del largo permitido, codificable en UTF-8 y sin caracteres de
    control (categoría Cc, incluido NUL) ni de formato invisibles (categoría Cf: inversión de texto, espacios de
    ancho cero, etc.). Las contraseñas pueden llevar Cf (los emojis compuestos usan la unión de ancho cero).
    Si no, lanza DatosInvalidos con un mensaje para la persona."""
    if not isinstance(valor, str):
        raise DatosInvalidos(f"{campo} debe ser un texto.")
    if not minimo <= len(valor) <= maximo:  # el largo se revisa primero: no se recorre un texto gigante
        raise DatosInvalidos(f"{campo} debe tener entre {minimo} y {maximo} caracteres.")
    try:
        valor.encode("utf-8")
    except UnicodeEncodeError:
        raise DatosInvalidos(f"{campo} tiene caracteres que no se pueden guardar.") from None
    prohibidas = {"Cc"} if permitir_formato else {"Cc", "Cf"}
    if any(unicodedata.category(caracter) in prohibidas for caracter in valor):
        raise DatosInvalidos(f"{campo} tiene caracteres de control o invisibles que no se permiten.")
    return valor


def id_valido(valor, campo="El identificador"):
    return texto_valido(valor, campo, MAXIMO_DE_ID, minimo=1)
