"""Modo proyecto existente: leer el proyecto antes de preguntar, y armar un plan de rescate a partir de lo que falta.

Es el caso de quien ya construyó algo (a menudo con una herramienta de inteligencia artificial) y quiere saber si aguanta
en producción. No se entrevista sobre lo que el proyecto ya contesta: se lee.
"""
import json
import os
import re

from . import checklist as ck
from . import estado as e
from .util import EXT_CODIGO, leer, recorrer

_SENALES = {
    "pagos": r"stripe|mercadopago|paypal|transbank|webpay|flow\.cl|culqi|payu|braintree",
    "cuentas": r"passport|next-auth|nextauth|jsonwebtoken|bcrypt|argon2|passlib|flask-login|django\.contrib\.auth|devise|"
               r"firebase.?auth|supabase|auth0|clerk",
    "base-de-datos": r"prisma|typeorm|sequelize|mongoose|sqlalchemy|psycopg|sqlite|knex|mysql|pg\b|mongodb|firebase|supabase|django",
    "whatsapp": r"baileys|whatsapp-web\.js|whatsapp|twilio",
    "ia": r"openai|langchain|google-generativeai|ollama|llama|gemini|llm",
    "archivos": r"multer|boto3|aws-sdk|\bs3\b|uploadthing|cloudinary|python-multipart|fileupload",
    "interfaz": r"\breact\b|react-dom|vue|svelte|next|angular|flutter|jinja|tailwind|bootstrap",
}
_MANIFIESTOS = ("package.json", "requirements.txt", "requirements-dev.txt", "pyproject.toml", "composer.json", "go.mod",
                "pubspec.yaml", "Gemfile", "pom.xml", "Cargo.toml", "Pipfile")


def _dependencias(repo):
    texto = ""
    for ruta in recorrer(repo):
        if os.path.basename(ruta) in _MANIFIESTOS:
            texto += (leer(os.path.join(repo, ruta)) or "").lower() + "\n"
    return texto


def _comandos(repo, deps):
    c = {}
    pkg = leer(os.path.join(repo, "package.json"))
    if pkg:
        try:
            scripts = (json.loads(pkg).get("scripts") or {})
        except ValueError:
            scripts = {}
        if "test" in scripts and "no test specified" not in scripts["test"]:
            c["pruebas"] = "npm test"
        if "lint" in scripts:
            c["lint"] = "npm run lint"
        if "build" in scripts:
            c["build"] = "npm run build"
        c["auditoria"] = "npm audit --audit-level=high"
    elif any(f.endswith(".py") for f in recorrer(repo)):
        if "pytest" in deps or os.path.isdir(os.path.join(repo, "tests")):
            c["pruebas"] = "python -m pytest -q"
        if "ruff" in deps:
            c["lint"] = "python -m ruff check ."
        c["build"] = "python -m compileall -q ."
        if "pip-audit" in deps or "pip_audit" in deps:
            c["auditoria"] = "python -m pip_audit"
    elif os.path.isfile(os.path.join(repo, "go.mod")):
        c.update(pruebas="go test ./...", lint="go vet ./...", build="go build ./...")
    elif os.path.isfile(os.path.join(repo, "pubspec.yaml")):
        c.update(pruebas="flutter test", lint="dart analyze")
    return c


def detectar_proyecto(repo):
    """Lee el proyecto y propone el perfil, lo que maneja y los comandos. Son sugerencias: la persona las corrige."""
    deps = _dependencias(repo)
    banderas = {b: bool(re.search(rx, deps)) for b, rx in _SENALES.items()}
    if os.path.isfile(os.path.join(repo, "pubspec.yaml")) and "flutter" in deps or re.search(r"react-native|expo\b", deps):
        banderas["movil"] = True
    banderas["multiusuario"] = banderas["cuentas"]
    banderas["datos-personales"] = banderas["cuentas"] or banderas["pagos"] or banderas["whatsapp"]
    if banderas.get("movil"):
        perfil = "movil"
    elif banderas["whatsapp"] or (banderas["ia"] and not banderas["interfaz"]):
        perfil = "bot"
    elif banderas["pagos"] and banderas["interfaz"]:
        perfil = "tienda"
    elif banderas["interfaz"] and not banderas["base-de-datos"] and not banderas["cuentas"]:
        perfil = "sitio"
    elif re.search(r"express|fastify|nestjs|@nestjs|fastapi|flask|laravel|gin-gonic", deps) and not banderas["interfaz"]:
        perfil = "api"
    else:
        perfil = "otro"
    archivos = list(recorrer(repo))
    lenguajes = {}
    for a in archivos:
        ext = os.path.splitext(a)[1].lower()
        if ext in EXT_CODIGO:
            lenguajes[ext] = lenguajes.get(ext, 0) + 1
    mapa = {"archivos_de_codigo": sum(lenguajes.values()), "extensiones": dict(sorted(lenguajes.items(), key=lambda x: -x[1])[:5]),
            "usa_git": os.path.isdir(os.path.join(repo, ".git")),
            "tiene_ci": os.path.isdir(os.path.join(repo, ".github", "workflows")),
            "tiene_readme": any(os.path.isfile(os.path.join(repo, n)) for n in ("README.md", "README")),
            "archivos_de_prueba": len([a for a in archivos if re.search(r"(^|/)(tests?|__tests__)/|\.(test|spec)\.|_test\.", a)])}
    return {"perfil_sugerido": perfil, "banderas_sugeridas": {k: v for k, v in banderas.items() if v},
            "comandos_sugeridos": _comandos(repo, deps), "mapa": mapa}


def rescate(repo, est, crear_etapas=False):
    """Plan de rescate: lo que falta, de lo más grave a lo menos, agrupado en etapas de trabajo."""
    filas = [f for f in ck.evaluar(est) if f["estado"] == "pendiente"]
    grupos = {}
    for f in filas:
        grupos.setdefault(f["categoria"], []).append(f)

    def gravedad(par):
        categoria, items = par
        return (-sum(1 for i in items if i["critico"]), -sum(i["peso"] for i in items), categoria)
    plan = []
    for categoria, items in sorted(grupos.items(), key=gravedad):
        items = sorted(items, key=lambda i: (not i["critico"], -i["peso"]))
        autos = ["item:" + i["id"] for i in items if i["tipo"] == "auto"]
        plan.append({"etapa": "Rescate: %s" % categoria, "criticos": len([i for i in items if i["critico"]]),
                     "puntos": [{"id": i["id"], "titulo": i["titulo"], "critico": i["critico"], "tipo": i["tipo"]} for i in items],
                     "hecho_cuando": ["El punto queda cumplido: %s" % i["titulo"] for i in items],
                     "verificar": autos})
    creadas = []
    if crear_etapas:
        from . import etapas as et
        if est["etapa"] != "construccion":
            raise SystemExit("Las etapas de rescate se crean en la construcción (ahora: %s)." % est["etapa"])
        for p in plan:
            sin = None if p["verificar"] else "Los puntos de esta etapa los comprueba una persona: se declaran con marcar y citan lo que existe."
            creadas.append(et.agregar(est, p["etapa"], p["hecho_cuando"], p["verificar"], sin)["id"])
    puntaje = ck.puntaje(est)
    return {"puntaje_actual": puntaje["puntaje"], "veredicto": puntaje["titulo_veredicto"], "plan": plan, "etapas_creadas": creadas,
            "nota": "El plan va de lo más grave a lo menos grave. Con --crear-etapas se agregan como etapas de construcción, cada una con "
                    "su verificación."}
