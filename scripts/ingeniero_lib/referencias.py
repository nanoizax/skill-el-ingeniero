"""Comprueba que lo que una persona declara como evidencia cite cosas que existen de verdad en el proyecto.

No prueba que lo declarado sea cierto, pero evita la evidencia inventada: la prueba citada tiene que existir, el archivo
citado tiene que estar, la librería citada tiene que estar en las dependencias o en el código.
"""
import fnmatch
import os
import re

from .util import EXT_CODIGO, leer, recorrer

ARCHIVOS_DE_PRUEBA = ("test_*.py", "*_test.py", "*.test.js", "*.test.jsx", "*.test.ts", "*.test.tsx", "*.spec.js", "*.spec.ts",
                      "*Test.java", "*Tests.java", "*_test.go", "*_test.dart", "*Tests.cs", "*Test.cs", "*_test.rs", "*Test.php")
_CARPETA_DE_PRUEBAS = re.compile(r"(^|/)(tests?|__tests__|spec)/.+\.(py|js|ts|php|rb)$")
_NOMBRES_DE_PRUEBA = [
    re.compile(r"\bdef (test_\w+)"),
    re.compile(r"\b(?:it|test)\s*\(\s*['\"`]([^'\"`]+)['\"`]"),
    re.compile(r"\bfunc (Test\w+)"),
    re.compile(r"@Test[^\n]*\n\s*(?:public\s+)?(?:void|fun)\s+(\w+)"),
    re.compile(r"#\[test\][^\n]*\n(?:\s*#\[[^\n]*\n)*\s*(?:async\s+)?fn\s+(\w+)"),
    re.compile(r"\[(?:Fact|Theory)\][^\n]*\n\s*public\s+\w+\s+(\w+)"),
    re.compile(r"\bpublic function (test\w+)"),
]
MANIFIESTOS = ("requirements*.txt", "pyproject.toml", "package.json", "composer.json", "go.mod", "pubspec.yaml", "Gemfile",
               "pom.xml", "build.gradle*", "*.csproj", "Cargo.toml")


def archivos_de_prueba(repo):
    return [r for r in recorrer(repo)
            if any(fnmatch.fnmatch(os.path.basename(r), p) for p in ARCHIVOS_DE_PRUEBA) or _CARPETA_DE_PRUEBAS.search(r)]


def nombres_de_pruebas(repo):
    """{nombre de la prueba: archivo donde está}."""
    nombres = {}
    for ruta in archivos_de_prueba(repo):
        texto = leer(os.path.join(repo, ruta)) or ""
        for rx in _NOMBRES_DE_PRUEBA:
            for n in rx.findall(texto):
                nombres.setdefault(n, ruta)
    return nombres


def _normal(t):
    return re.sub(r"[\s_\-]+", " ", (t or "").lower()).strip()


def _prueba(repo, evidencia, a):
    existentes = nombres_de_pruebas(repo)
    if not existentes:
        return False, "El proyecto no tiene pruebas, así que no hay ninguna prueba que citar."
    texto = _normal(evidencia)
    def sin_prefijo(n):
        return re.sub(r"^test ", "", _normal(n))  # a veces se cita la prueba sin el "test_" del principio
    citadas = {n for n in existentes if len(n) >= 6 and (_normal(n) in texto or (len(sin_prefijo(n)) >= 12 and sin_prefijo(n) in texto))}
    # citar el archivo de pruebas también vale, como una cita más por archivo
    citadas |= {ruta for ruta in set(existentes.values()) if ruta.lower() in evidencia.lower().replace("\\", "/")}
    minimo = a.get("min", 1)
    if len(citadas) < minimo:
        return False, ("La evidencia tiene que citar por su nombre al menos %d prueba(s) que exista(n) en el proyecto "
                       "(por ejemplo %s)." % (minimo, ", ".join(sorted(existentes)[:2])))
    return True, "Cita %d prueba(s) que existen: %s." % (len(citadas), ", ".join(sorted(citadas)[:3]))


_RUTA = re.compile(r"[\w.\-]+(?:[/\\][\w.\-]+)+|[\w\-]+\.[A-Za-z0-9]{1,6}")


def _archivo(repo, evidencia, a):
    existentes = []
    for token in set(_RUTA.findall(evidencia)):
        limpio = token.replace("\\", "/").strip("./") if token.startswith("./") else token.replace("\\", "/")
        if os.path.exists(os.path.join(repo, limpio)):
            existentes.append(limpio)
    minimo = a.get("min", 1)
    if len(existentes) < minimo:
        return False, "La evidencia tiene que citar al menos %d archivo(s) o carpeta(s) que existan en el proyecto." % minimo
    return True, "Cita archivos que existen: %s." % ", ".join(sorted(existentes)[:3])


def _dependencia(repo, evidencia, a):
    texto = evidencia.lower()
    opciones = [o for o in a["opciones"] if o.lower() in texto]
    if not opciones:
        return False, "La evidencia tiene que nombrar la librería o el algoritmo usado (por ejemplo %s)." % ", ".join(a["opciones"][:4])
    en_manifiestos = ""
    for ruta in recorrer(repo):
        if any(fnmatch.fnmatch(os.path.basename(ruta), p) for p in MANIFIESTOS):
            en_manifiestos += (leer(os.path.join(repo, ruta)) or "").lower() + "\n"
    codigo = ""
    for ruta in recorrer(repo, EXT_CODIGO):
        codigo += (leer(os.path.join(repo, ruta)) or "").lower() + "\n"
    for o in opciones:
        if o.lower() in en_manifiestos or o.lower() in codigo:
            return True, "%s está en las dependencias o en el código." % o
    return False, "Citas %s, pero no aparece en las dependencias ni en el código del proyecto." % ", ".join(opciones)


TIPOS = {"prueba": _prueba, "archivo": _archivo, "dependencia": _dependencia}


def validar(repo, item, evidencia):
    """Aplica las validaciones del ítem (una o varias) a la evidencia. Devuelve (cumple, detalle)."""
    reglas = item["valida"] if isinstance(item["valida"], list) else [item["valida"]]
    detalles = []
    for regla in reglas:
        ok, detalle = TIPOS[regla["tipo"]](repo, evidencia, regla)
        if not ok:
            return False, detalle
        detalles.append(detalle)
    return True, " ".join(detalles)
