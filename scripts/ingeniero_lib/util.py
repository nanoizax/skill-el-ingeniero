"""Utilidades comunes: lectura de archivos, recorrido del proyecto, palabras y secciones de un documento."""
import os
import re
import unicodedata

RAIZ_SKILL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

IGNORAR = {".git", "node_modules", ".venv", "venv", "env", "dist", "build", "__pycache__", ".next", ".nuxt", ".dart_tool",
           "vendor", "target", ".gradle", ".idea", ".vscode", "coverage", ".pytest_cache", ".mypy_cache", ".turbo", ".cache"}
EXT_CODIGO = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".php", ".go", ".rb", ".java", ".kt", ".cs", ".dart",
              ".rs", ".swift", ".vue", ".svelte"}
ARCHIVOS_DE_BLOQUEO = {"package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lockb", "poetry.lock", "uv.lock", "Pipfile.lock",
                       "composer.lock", "go.sum", "Cargo.lock", "pubspec.lock", "Gemfile.lock"}


def leer(ruta, limite=1_000_000):
    """Texto del archivo, o None si es binario, enorme o no se puede leer."""
    try:
        if os.path.getsize(ruta) > limite:
            return None
        with open(ruta, "rb") as f:
            datos = f.read()
    except OSError:
        return None
    if b"\0" in datos:
        return None
    return datos.decode("utf-8", errors="replace")


def recorrer(repo, extensiones=None):
    """Rutas relativas (con /) de los archivos del proyecto, sin carpetas generadas ni dependencias."""
    for raiz, carpetas, archivos in os.walk(repo):
        carpetas[:] = [c for c in carpetas if c not in IGNORAR]
        for nombre in archivos:
            if extensiones is not None and os.path.splitext(nombre)[1].lower() not in extensiones:
                continue
            yield os.path.relpath(os.path.join(raiz, nombre), repo).replace("\\", "/")


def palabras(texto):
    return len(re.findall(r"[\wÀ-ſ]+", texto or ""))


def _normalizar(t):
    t = unicodedata.normalize("NFD", t or "")
    return "".join(c for c in t if unicodedata.category(c) != "Mn").lower().strip()


_ENCABEZADO = re.compile(r"^(#{1,6})\s+(.*?)\s*$")


def seccion(texto, encabezado):
    """Texto de la sección cuyo encabezado empieza por `encabezado` (sin tildes ni mayúsculas), o None si no existe."""
    buscado = _normalizar(encabezado)
    lineas = (texto or "").splitlines()
    for i, linea in enumerate(lineas):
        m = _ENCABEZADO.match(linea)
        if not m or not _normalizar(m.group(2)).startswith(buscado):
            continue
        nivel, cuerpo = len(m.group(1)), []
        for sig in lineas[i + 1:]:
            m2 = _ENCABEZADO.match(sig)
            if m2 and len(m2.group(1)) <= nivel:
                break
            cuerpo.append(sig)
        return "\n".join(cuerpo)
    return None


def con_huecos(texto):
    """¿Quedan huecos [[...]] sin llenar de la plantilla?"""
    return "[[" in (texto or "")
