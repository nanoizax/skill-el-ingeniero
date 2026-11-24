"""Las comprobaciones automáticas del checklist. Cada una devuelve (cumple, detalle)."""
import fnmatch
import os
import re
import shlex
import shutil
import subprocess

from . import estado as est_mod
from .referencias import archivos_de_prueba, nombres_de_pruebas
from .util import (ARCHIVOS_DE_BLOQUEO, EXT_CODIGO, con_huecos, leer, palabras, recorrer, seccion)

# ---------------------------------------------------------------- documentos


def _doc(repo, nombre):
    return leer(os.path.join(est_mod.carpeta(repo), nombre))


def _seccion(repo, est, a):
    texto = _doc(repo, a["doc"])
    if texto is None:
        return False, "Falta el documento %s." % a["doc"]
    cuerpo = seccion(texto, a["encabezado"])
    if cuerpo is None:
        return False, "En %s falta la sección \"%s\"." % (a["doc"], a["encabezado"])
    if con_huecos(cuerpo):
        return False, "En %s, la sección \"%s\" todavía tiene huecos [[...]] sin llenar." % (a["doc"], a["encabezado"])
    if palabras(cuerpo) < a["min_palabras"]:
        return False, "En %s, la sección \"%s\" es muy corta (%d palabras; mínimo %d)." % (
            a["doc"], a["encabezado"], palabras(cuerpo), a["min_palabras"])
    return True, "Sección \"%s\" de %s completa." % (a["encabezado"], a["doc"])


def _documento(repo, est, a):
    texto = _doc(repo, a["doc"])
    if texto is None:
        return False, "Falta el documento %s." % a["doc"]
    if con_huecos(texto):
        return False, "%s todavía tiene huecos [[...]] sin llenar." % a["doc"]
    if palabras(texto) < a["min_palabras"]:
        return False, "%s es muy corto (%d palabras; mínimo %d)." % (a["doc"], palabras(texto), a["min_palabras"])
    return True, "%s completo (%d palabras)." % (a["doc"], palabras(texto))


def _numero_de_casos(repo):
    texto = _doc(repo, "casos-de-uso.md") or ""
    return len(re.findall(r"^##\s+Caso\s+\d+", texto, re.M))


FRASES_VAGAS = ["funciona bien", "funciona correctamente", "funciona como debe", "se ve bien", "se ve correcto", "se ve profesional",
                "está listo", "esta listo", "sin problemas", "como se espera", "como corresponde", "adecuadamente",
                "de forma adecuada", "de manera correcta", "correctamente", "todo bien", "debería funcionar", "intuitivo",
                "fácil de usar", "facil de usar", "amigable", "bonito", "está conectado", "esta conectado"]


def frases_vagas_en(texto):
    """Frases que no se pueden comprobar ('funciona bien', 'se ve bien'): un criterio tiene que describir algo observable."""
    bajo = (texto or "").lower()
    return sorted({f for f in FRASES_VAGAS if f in bajo})


def _casos(repo, est, a):
    texto = _doc(repo, "casos-de-uso.md")
    if texto is None:
        return False, "Falta casos-de-uso.md."
    if con_huecos(texto):
        return False, "casos-de-uso.md todavía tiene huecos [[...]] sin llenar."
    casos = _numero_de_casos(repo)
    dados = len(re.findall(r"\bDado\b", texto))
    if casos < 3:
        return False, "Hay %d casos de uso; el mínimo es 3." % casos
    if dados < casos:
        return False, "Hay %d casos pero solo %d criterios \"Dado... cuando... entonces\"." % (casos, dados)
    criterios = [l.strip() for l in texto.splitlines() if re.match(r"^\s*-\s+Dado\b", l)]
    mal_formados = [c for c in criterios if not re.search(r"(?i)\bdado\b.+\bcuando\b.+\bentonces\b.+", c)]
    if mal_formados:
        return False, "Hay criterios sin la forma \"Dado... cuando... entonces...\": %s" % mal_formados[0][:100]
    vagas = frases_vagas_en("\n".join(criterios))
    if vagas:
        return False, ("Los criterios usan frases que no se pueden comprobar (%s). Describe qué se ve o qué se recibe, "
                       "con un dato concreto." % ", ".join(vagas[:4]))
    return True, "%d casos de uso con criterios que se pueden comprobar." % casos


def _sin_dudas(repo, est, a):
    abiertas = []
    carpeta = est_mod.carpeta(repo)
    for nombre in sorted(os.listdir(carpeta)):
        if nombre.endswith(".md"):
            n = len(re.findall(r"\[DUDA", leer(os.path.join(carpeta, nombre)) or ""))
            if n:
                abiertas.append("%s (%d)" % (nombre, n))
    if abiertas:
        return False, ("Quedan dudas abiertas ([DUDA: ...]) en %s. Ciérralas: pregunta a la persona, confirma un supuesto con sus "
                       "palabras o pásalas a \"Fuera de alcance\"." % ", ".join(abiertas))
    return True, "No quedan dudas abiertas."


def _premortem(repo, est, a):
    texto = _doc(repo, "premortem.md")
    if texto is None:
        return False, "Falta premortem.md."
    if con_huecos(texto):
        return False, "premortem.md todavía tiene huecos [[...]] sin llenar."
    historia = seccion(texto, "Qué pasaría si fracasa") or ""
    if palabras(historia) < 30:
        return False, "Cuenta en al menos 30 palabras cómo sería el fracaso dentro de seis meses (hay %d)." % palabras(historia)
    bloques = re.split(r"(?m)^###\s+Riesgo\s+\d+", texto)[1:]
    buenos = 0
    for b in bloques:
        m = re.search(r"(?:Qué haremos|Lo dejamos fuera):\s*(.+)", b)
        if m and palabras(m.group(1)) >= 4:
            buenos += 1
    if buenos < 3:
        return False, "Hacen falta al menos 3 riesgos con su respuesta (\"Qué haremos\" o \"Lo dejamos fuera\"); hay %d." % buenos
    angulos = [l for l in (seccion(texto, "Los ocho ángulos") or "").splitlines() if l.strip().startswith("- ")]
    if len(angulos) < 8:
        return False, "Faltan ángulos por revisar: hay %d de 8." % len(angulos)
    return True, "Pre-mortem con %d riesgos que tienen respuesta y los 8 ángulos revisados." % buenos


def _trazabilidad(repo, est, a):
    texto = _doc(repo, "casos-de-uso.md") or ""
    refs = re.findall(r"Prueba que lo cubre:\s*(.+)", texto)
    if not refs:
        return False, "Los casos de uso no dicen qué prueba los cubre (\"Prueba que lo cubre: ...\")."
    nombres = nombres_de_pruebas(repo)
    sin = []
    for ref in refs:
        piezas = [p.strip().strip("`") for p in re.split(r"[;,]| y ", ref) if p.strip()]
        if not any(os.path.exists(os.path.join(repo, p)) or p in nombres for p in piezas):
            sin.append(ref.strip())
    if sin:
        return False, "Estos casos apuntan a pruebas que no existen: %s. Actualiza casos-de-uso.md con los nombres reales." % "; ".join(sin[:3])
    return True, "Los %d casos de uso apuntan a pruebas que existen." % len(refs)


def _investigacion(repo, est, a):
    texto = _doc(repo, "investigacion.md")
    if texto is None:
        return False, "Falta investigacion.md."
    faltan = []
    if not re.search(r"Fecha de la investigaci[óo]n:\s*\d{4}-\d{2}-\d{2}", texto):
        faltan.append("la fecha real (aaaa-mm-dd)")
    if len(re.findall(r"https?://[^\s)\]]+", texto)) < 3:
        faltan.append("al menos 3 enlaces como fuente")
    for letra in "ABC":
        if not re.search(r"Opci[óo]n %s\b" % letra, texto):
            faltan.append("la opción %s" % letra)
    hallazgos = seccion(texto, "Hallazgos") or ""
    lineas = [l for l in hallazgos.splitlines() if l.strip().startswith("- ")]
    graduadas = [re.search(r"\[fuente:\s*(oficial|secundaria|opini[óo]n)\]", l, re.I) for l in lineas]
    if lineas and not all(graduadas):
        faltan.append("indicar en cada hallazgo el tipo de fuente: [fuente: oficial], [fuente: secundaria] o [fuente: opinión]")
    elif lineas and not any(g.group(1).lower() == "oficial" for g in graduadas):
        faltan.append("al menos un hallazgo con fuente oficial: sin ninguna, todo es de segunda mano")
    recomendacion = seccion(texto, "Recomendación")
    if not recomendacion or palabras(recomendacion) < 10:
        faltan.append("la recomendación")
    # los huecos solo importan en lo que ya se debió llenar: la elección se llena después
    sin_eleccion = re.sub(r"## Elección de la persona.*?(?=\n## |\Z)", "", texto, flags=re.S)
    if con_huecos(sin_eleccion):
        faltan.append("llenar los huecos [[...]]")
    if faltan:
        return False, "A investigacion.md le falta: " + "; ".join(faltan) + "."
    return True, "Investigación fechada, con fuentes y tres opciones."


def _eleccion(repo, est, a):
    e = est.get("eleccion")
    if not e:
        return False, "La persona todavía no eligió. Usa: elegir --opcion X --porque \"...\"."
    return True, "Eligió la opción %s (%s)." % (e["opcion"], e["fecha"])


def _aprobacion(repo, est, a):
    ap = est.get("aprobacion")
    if not ap:
        return False, "La persona todavía no aprobó el plan. Usa: avanzar aprobado --evidencia \"sus palabras\"."
    return True, "Aprobó el plan el %s." % ap["fecha"]


def _decisiones(repo, est, a):
    for sub in ("docs/decisiones", "docs/adr", "docs/ingeniero/decisiones"):
        carpeta = os.path.join(repo, sub)
        if os.path.isdir(carpeta) and any(f.endswith(".md") for f in os.listdir(carpeta)):
            return True, "Decisiones registradas en %s." % sub
    return False, "No hay decisiones registradas (docs/decisiones/*.md)."


def _etapas_cerradas(repo, est, a):
    etapas = est.get("etapas", [])
    abiertas = [e for e in etapas if e["estado"] != "cerrada"]
    if len(etapas) < 2:
        return False, "Hay solo %d etapa; falta al menos una etapa de funcionalidad además del esqueleto." % len(etapas)
    if abiertas:
        return False, "Etapas abiertas: " + ", ".join("%s (%s)" % (e["id"], e["nombre"]) for e in abiertas) + "."
    sin_prueba = [e for e in etapas if not (e.get("sin_verificacion") or (e.get("ultima_verificacion") or {}).get("ok"))]
    if sin_prueba:
        return False, ("Etapas cerradas sin una verificación que haya pasado: " +
                       ", ".join("%s (%s)" % (e["id"], e["nombre"]) for e in sin_prueba) + ". Ejecuta etapa-verificar.")
    return True, "%d etapas cerradas, cada una con su verificación ejecutada." % len(etapas)


# ---------------------------------------------------------------- código y repositorio

_PATRONES_SECRETOS = [
    ("clave de AWS", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("llave privada", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY")),
    ("token de GitHub", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
    ("token de Slack", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("clave tipo sk-", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("token JWT", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
    ("URL con contraseña", re.compile(r"\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqp)://[^:\s/@]+:[^@\s]{3,}@")),
    ("contraseña o clave escrita en el código", re.compile(
        r"(?i)\b[\w-]*(?:api[_-]?key|secret|token|passwd|password|contrase[ñn]a|clave)\w*[\"']?\s*[:=]\s*[\"']([^\"'\s]{12,})[\"']")),
]
_FALSOS = ("example", "changeme", "xxxx", "tu_", "tu-", "your", "<", ">", "placeholder", "dummy", "fake", "ficticio",
           "test", "secret_here", "ejemplo", "process.env", "os.environ", "getenv", "${", "{{")
_OMITIR_EN_SECRETOS = {".env.example", ".env.sample", ".env.template"}


def _parece_real(coincidencia, valor):
    bajo = (valor or coincidencia).lower()
    if any(f in bajo for f in _FALSOS):
        return False
    if valor is not None:  # patrón genérico: debe parecer una clave, no una frase
        tiene_digito = any(c.isdigit() for c in valor)
        tiene_letra = any(c.isalpha() for c in valor)
        return (tiene_digito and tiene_letra) or len(valor) >= 24
    return True


MARCA_DE_DATO_DE_PRUEBA = "pragma: allowlist secret"  # una línea con esta marca no se revisa: es un dato de prueba, no una clave real


def _hallazgos_en(texto, origen):
    texto = "\n".join(l for l in texto.splitlines() if MARCA_DE_DATO_DE_PRUEBA not in l.lower())
    res = []
    for nombre, rx in _PATRONES_SECRETOS:
        for m in rx.finditer(texto):
            valor = m.group(1) if m.groups() else None
            if _parece_real(m.group(0), valor):
                res.append("%s en %s" % (nombre, origen))
                break
    return res


def _secretos(repo, est, a):
    hallazgos = []
    for ruta in recorrer(repo):
        nombre = os.path.basename(ruta)
        if nombre in _OMITIR_EN_SECRETOS or nombre in ARCHIVOS_DE_BLOQUEO or nombre.endswith((".min.js", ".map", ".svg")):
            continue
        if nombre == ".env" or nombre.startswith(".env."):
            continue  # se espera que existan, y que Git los ignore (otro ítem lo comprueba)
        texto = leer(os.path.join(repo, ruta))
        if texto:
            hallazgos += _hallazgos_en(texto, ruta)
    historial = "no se revisó el historial (el proyecto no usa Git)"
    if os.path.isdir(os.path.join(repo, ".git")) and shutil.which("git"):
        try:
            r = subprocess.run(["git", "-C", repo, "log", "--all", "-p", "-U0", "--no-color", "--diff-filter=AM",
                                "--", ".", ":(exclude).env.example", ":(exclude)*lock*"],
                               capture_output=True, timeout=120)
            agregadas = "\n".join(l[1:] for l in r.stdout[:20_000_000].decode("utf-8", "replace").splitlines()
                                  if l.startswith("+") and not l.startswith("+++"))
            hallazgos += [h + " (historial de Git)" for h in _hallazgos_en(agregadas, "una versión anterior")]
            historial = "historial de Git revisado"
        except (subprocess.TimeoutExpired, OSError):
            historial = "no se pudo revisar el historial de Git"
    if hallazgos:
        return False, "Posibles secretos: " + "; ".join(sorted(set(hallazgos))[:6]) + "."
    return True, "No se encontraron secretos en los archivos; %s." % historial


def _env_fuera_de_git(repo, est, a):
    gitignore = leer(os.path.join(repo, ".gitignore")) or ""
    ignora = any(re.match(r"^\s*(?:/)?(?:\*\*/)?(?:\.env|\*\.env|\.env\*)\s*$", l) for l in gitignore.splitlines())
    versionados = []
    if os.path.isdir(os.path.join(repo, ".git")) and shutil.which("git"):
        r = subprocess.run(["git", "-C", repo, "ls-files"], capture_output=True, text=True, encoding="utf-8", errors="replace")
        versionados = [f for f in r.stdout.splitlines()
                       if (os.path.basename(f) == ".env" or (os.path.basename(f).startswith(".env.")
                                                              and os.path.basename(f) not in _OMITIR_EN_SECRETOS))]
    if versionados:
        return False, "Hay archivos de entorno dentro de Git: %s." % ", ".join(versionados)
    if not ignora:
        return False, "El archivo .gitignore no incluye .env."
    return True, ".env está en .gitignore y no hay archivos de entorno versionados."


def _env_ejemplo(repo, est, a):
    for nombre in (".env.example", ".env.sample", ".env.template"):
        if os.path.isfile(os.path.join(repo, nombre)):
            return True, "Existe %s." % nombre
    return False, "Falta el archivo .env.example con los nombres de las variables."


def _lockfile(repo, est, a):
    if os.path.isfile(os.path.join(repo, "requirements.txt")) and not any(
            os.path.isfile(os.path.join(repo, n)) for n in ("poetry.lock", "uv.lock", "Pipfile.lock")):
        lineas = [l.strip() for l in (leer(os.path.join(repo, "requirements.txt")) or "").splitlines()
                  if l.strip() and not l.strip().startswith(("#", "-"))]
        sueltas = [l for l in lineas if "==" not in l]
        if lineas and not sueltas:
            return True, "requirements.txt con versiones exactas."
        if lineas:
            return False, "requirements.txt tiene dependencias sin versión exacta: %s." % ", ".join(sueltas[:4])
    manifiestos = {"package.json": ("package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lockb"),
                   "pyproject.toml": ("poetry.lock", "uv.lock", "Pipfile.lock"),
                   "composer.json": ("composer.lock",), "go.mod": ("go.sum",), "Cargo.toml": ("Cargo.lock",),
                   "pubspec.yaml": ("pubspec.lock",), "Gemfile": ("Gemfile.lock",)}
    vistos = False
    for manifiesto, locks in manifiestos.items():
        if os.path.isfile(os.path.join(repo, manifiesto)):
            vistos = True
            if not any(os.path.isfile(os.path.join(repo, l)) for l in locks):
                return False, "Hay %s pero falta su archivo de bloqueo (%s)." % (manifiesto, " o ".join(locks))
    if not vistos:
        return False, "No se encontró un archivo de dependencias (package.json, pyproject.toml, requirements.txt...)."
    return True, "Las versiones de las dependencias están fijadas."


def _readme(repo, est, a):
    for nombre in ("README.md", "README", "readme.md"):
        texto = leer(os.path.join(repo, nombre))
        if texto is not None:
            if palabras(texto) < 120:
                return False, "El README es muy corto (%d palabras; mínimo 120)." % palabras(texto)
            if not re.search(r"instal|ejecut|arranc|iniciar|\brun\b|\bstart\b", texto, re.I):
                return False, "El README no explica cómo instalar o ejecutar el proyecto."
            return True, "README con %d palabras que explica cómo ejecutarlo." % palabras(texto)
    return False, "Falta el archivo README.md."


def _archivos_de_codigo(repo):
    return [r for r in recorrer(repo, EXT_CODIGO) if not r.startswith("docs/")]


def _salud(repo, est, a):
    for ruta in _archivos_de_codigo(repo):
        texto = leer(os.path.join(repo, ruta)) or ""
        if re.search(r"""['"`/](?:health|healthz|salud|ping)\b|healthcheck|health_check""", texto, re.I):
            return True, "Punto de salud encontrado en %s." % ruta
    return False, "No se encontró un punto de salud (por ejemplo GET /health)."


def _archivos_grandes(repo, est, a):
    grandes = []
    for ruta in _archivos_de_codigo(repo):
        texto = leer(os.path.join(repo, ruta))
        if texto and len(texto.splitlines()) > 500 and ".min." not in ruta and ".generated." not in ruta:
            grandes.append("%s (%d líneas)" % (ruta, len(texto.splitlines())))
    if grandes:
        return False, "Archivos de más de 500 líneas: " + ", ".join(grandes[:5]) + "."
    return True, "Ningún archivo de código pasa de 500 líneas."


def _pendientes(repo, est, a):
    total, donde = 0, []
    for ruta in _archivos_de_codigo(repo):
        n = len(re.findall(r"\b(?:TODO|FIXME|XXX|HACK)\b", leer(os.path.join(repo, ruta)) or ""))
        if n:
            total += n
            donde.append(ruta)
    if total > 5:
        return False, "%d pendientes (TODO, FIXME) en el código, por ejemplo en %s." % (total, ", ".join(donde[:3]))
    return True, "%d pendientes en el código (máximo 5)." % total


_FUNCIONES_DE_PRUEBA = re.compile(r"\bdef test_|\b(?:it|test)\s*\(|@Test\b|\bfunc Test\w+|#\[test\]|\[Fact\]|\[Theory\]|\bpublic function test")
_VERIFICACIONES = re.compile(r"\bassert\b|\bassert[A-Z_]\w*\(|\bexpect\s*\(|pytest\.raises|\.should\b|assertThrows|\bAssert\.\w+|"
                             r"\bt\.(?:Fatal|Error)f?\(|assert_eq!|assert!|\.toBe|\.toEqual|\.toThrow")


def _pruebas_existen(repo, est, a):
    archivos = archivos_de_prueba(repo)
    textos = [leer(os.path.join(repo, r)) or "" for r in archivos]
    pruebas = sum(len(_FUNCIONES_DE_PRUEBA.findall(t)) for t in textos)
    verificaciones = sum(len(_VERIFICACIONES.findall(t)) for t in textos)
    casos = _numero_de_casos(repo)
    if not archivos:
        return False, "No se encontraron archivos de pruebas."
    if pruebas < max(casos, 1):
        return False, "Hay %d pruebas para %d casos de uso: falta al menos una por caso." % (pruebas, casos)
    if verificaciones < pruebas:
        return False, "Hay %d pruebas pero solo %d verificaciones (assert, expect...): alguna prueba no comprueba nada." % (
            pruebas, verificaciones)
    return True, "%d pruebas con %d verificaciones en %d archivos, para %d casos de uso." % (
        pruebas, verificaciones, len(archivos), casos)


def _migraciones(repo, est, a):
    for sub in ("migrations", "prisma/migrations", "db/migrate", "database/migrations", "alembic/versions", "src/migrations",
                "supabase/migrations"):
        carpeta = os.path.join(repo, sub)
        if os.path.isdir(carpeta) and os.listdir(carpeta):
            return True, "Migraciones en %s." % sub
    return False, "No se encontró una carpeta de migraciones con archivos."


def _ci(repo, est, a):
    flujos = os.path.join(repo, ".github", "workflows")
    if os.path.isdir(flujos) and any(f.endswith((".yml", ".yaml")) for f in os.listdir(flujos)):
        return True, "Flujo de CI en .github/workflows."
    for nombre in (".gitlab-ci.yml", "azure-pipelines.yml", "Jenkinsfile", ".circleci/config.yml"):
        if os.path.exists(os.path.join(repo, nombre)):
            return True, "CI configurado (%s)." % nombre
    return False, "No hay una automatización de CI (por ejemplo .github/workflows)."


# ---------------------------------------------------------------- comandos del proyecto


def correr_comando(repo, cmd, espera=900):
    """Ejecuta un comando del proyecto sin shell, en la carpeta del proyecto. Devuelve (cumple, detalle)."""
    argv = [p[1:-1] if len(p) >= 2 and p[0] == p[-1] and p[0] in "'\"" else p
            for p in shlex.split(cmd, posix=(os.name != "nt"))]
    exe = shutil.which(argv[0])
    if not exe:
        return False, "No se encontró el comando \"%s\"." % argv[0]
    entorno = dict(os.environ, CI="1")
    try:
        r = subprocess.run([exe] + argv[1:], cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=espera, env=entorno, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return False, "\"%s\" tardó más de %d minutos y se detuvo." % (cmd, espera // 60)
    if r.returncode == 0:
        return True, "\"%s\" terminó sin errores." % cmd
    cola = " ".join(((r.stdout or "") + (r.stderr or "")).split())[-300:]
    return False, "\"%s\" falló (código %d): %s" % (cmd, r.returncode, cola)


def _comando(repo, est, a):
    clave = a["clave"]
    cmd = (est.get("comandos") or {}).get(clave)
    if not cmd:
        return False, "No hay comando configurado para \"%s\". Usa: comandos --%s \"<comando>\"." % (clave, clave)
    return correr_comando(repo, cmd)


_JERGA = ["api", "endpoint", "backend", "frontend", "framework", "repositorio", "despliegue", "deploy", "servidor", "hosting",
          "migración", "migraciones", "token", "hash", "pipeline", "orm", "sql", "json", "docker", "contenedor", "microservicio",
          "middleware", "refactor", "dependencias", "linter", "commit", "git", "cron", "webhook", "caché", "cache"]
_EXPLICA = ("(", "o sea", "es decir", "significa", " es un ", " es una ", " es el ", " es la ", " son ")


def _lenguaje_llano(repo, est, a):
    texto = _doc(repo, a["doc"])
    if texto is None:
        return False, "Falta el documento %s." % a["doc"]
    if con_huecos(texto):
        return False, "%s todavía tiene huecos [[...]] sin llenar." % a["doc"]
    if palabras(texto) < a["min_palabras"]:
        return False, "%s es muy corto (%d palabras; mínimo %d)." % (a["doc"], palabras(texto), a["min_palabras"])
    sin_explicar = []
    for linea in texto.splitlines():
        bajo = linea.lower()
        for t in _JERGA:
            m = re.search(r"\b%s\b" % re.escape(t), bajo)
            if m and not any(x in bajo[m.end():] or x in bajo for x in _EXPLICA):
                sin_explicar.append(t)
    if sin_explicar:
        return False, ("Hay palabras técnicas sin explicar para quien no programa: %s. Explícalas en la misma línea o "
                       "cámbialas por una palabra común." % ", ".join(sorted(set(sin_explicar))[:6]))
    frases = [f for f in re.split(r"[.!?\n]+", texto) if f.strip() and not f.strip().startswith("#")]
    largas = [f for f in frases if len(f.split()) > 40]
    promedio = sum(len(f.split()) for f in frases) / max(len(frases), 1)
    if largas or promedio > 22:
        return False, "Las frases son muy largas (promedio %.0f palabras; ninguna debería pasar de 40). Acórtalas." % promedio
    return True, "Resumen en lenguaje llano (%d palabras, frases de %.0f palabras en promedio)." % (palabras(texto), promedio)


def _investigacion_vigente(repo, est, a):
    texto = _doc(repo, "investigacion.md") or ""
    m = re.search(r"Fecha de la investigaci[óo]n:\s*(\d{4})-(\d{2})-(\d{2})", texto)
    if not m:
        return False, "investigacion.md no tiene una fecha válida."
    import datetime
    try:
        fecha = datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        hoy = datetime.date.fromisoformat(est_mod.hoy())
    except ValueError:
        return False, "La fecha de la investigación no es válida."
    dias = (hoy - fecha).days
    if dias > a.get("max_dias", 60):
        return False, "La investigación tiene %d días: precios y versiones ya pueden haber cambiado. Vuelve a consultarlos." % dias
    return True, "La investigación tiene %d días (máximo %d)." % (dias, a.get("max_dias", 60))


def _variables_documentadas(repo, est, a):
    ejemplo = leer(os.path.join(repo, ".env.example")) or ""
    nombres = re.findall(r"^\s*([A-Z][A-Z0-9_]*)\s*=", ejemplo, re.M)
    if not ejemplo:
        return False, "Falta .env.example: no hay lista de variables que documentar."
    ok, detalle = _seccion(repo, est, {"doc": "entrega.md", "encabezado": "Variables de entorno", "min_palabras": a.get("min_palabras", 10)})
    if not ok:
        return ok, detalle
    cuerpo = seccion(_doc(repo, "entrega.md"), "Variables de entorno")
    faltan = [n for n in nombres if n not in cuerpo]
    if faltan:
        return False, "Estas variables de .env.example no están explicadas en la guía de entrega: %s." % ", ".join(faltan)
    return True, "Las %d variables de .env.example están explicadas en la guía de entrega." % len(nombres)


def _alguno_existe(repo, est, a):
    for ruta in a["opciones"]:
        if os.path.exists(os.path.join(repo, ruta)):
            return True, "Existe %s." % ruta
    return False, "No se encontró ninguno de: %s." % ", ".join(a["opciones"])


TIPOS = {
    "sin_dudas": _sin_dudas, "premortem": _premortem, "trazabilidad": _trazabilidad,
    "lenguaje_llano": _lenguaje_llano, "investigacion_vigente": _investigacion_vigente,
    "variables_documentadas": _variables_documentadas, "alguno_existe": _alguno_existe,
    "seccion": _seccion, "documento": _documento, "casos": _casos, "investigacion": _investigacion, "eleccion": _eleccion,
    "aprobacion": _aprobacion, "decisiones": _decisiones, "etapas_cerradas": _etapas_cerradas, "secretos": _secretos,
    "env_fuera_de_git": _env_fuera_de_git, "env_ejemplo": _env_ejemplo, "lockfile": _lockfile, "readme": _readme,
    "salud": _salud, "archivos_grandes": _archivos_grandes, "pendientes_en_codigo": _pendientes,
    "pruebas_existen": _pruebas_existen, "migraciones": _migraciones, "ci": _ci, "comando": _comando,
}


def comprobar(repo, est, item):
    """Ejecuta la comprobación automática de un ítem. Devuelve (cumple, detalle)."""
    auto = item["auto"]
    try:
        return TIPOS[auto["tipo"]](repo, est, auto)
    except OSError as e:  # un archivo ilegible no tumba todo el informe
        return False, "No se pudo comprobar: %s." % e
