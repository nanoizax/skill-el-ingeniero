"""Qué skills propias de Soy Tegno están instaladas y cuáles faltan. Nunca instala nada."""
import json
import os

from .util import RAIZ_SKILL


def _carpetas_ocultas_de_skills(base):
    """Cualquier carpeta oculta con una subcarpeta `skills` (cada herramienta de desarrollo usa la suya)."""
    try:
        nombres = sorted(os.listdir(base))
    except OSError:
        return []
    return [os.path.join(base, n, "skills") for n in nombres
            if n.startswith(".") and os.path.isdir(os.path.join(base, n, "skills"))]


def carpetas_de_skills(repo):
    extra = [p for p in os.environ.get("INGENIERO_SKILLS_DIRS", "").split(os.pathsep) if p]
    return extra + _carpetas_ocultas_de_skills(os.path.expanduser("~")) + _carpetas_ocultas_de_skills(repo)


def revisar(repo):
    with open(os.path.join(RAIZ_SKILL, "datos", "skills-propias.json"), encoding="utf-8") as f:
        datos = json.load(f)
    carpetas = [c for c in carpetas_de_skills(repo)]
    instaladas, faltan = [], []
    for s in datos["skills"]:
        donde = next((c for c in carpetas if os.path.isfile(os.path.join(c, s["nombre"], "SKILL.md"))), None)
        if donde:
            instaladas.append({"nombre": s["nombre"], "etapa": s["etapa"], "en": donde})
        else:
            faltan.append({"nombre": s["nombre"], "etapa": s["etapa"], "para": s["para"],
                           "enlace": "%s/%s" % (datos["organizacion"], s["repo"])})
    return {"instaladas": instaladas, "faltan": faltan, "buscado_en": carpetas,
            "nota": "No se instaló nada. Si falta alguna, sugiérele a la persona el enlace y usa mientras tanto la versión "
                    "mínima de references/nuestras-skills.md. Instalar es decisión suya."}
