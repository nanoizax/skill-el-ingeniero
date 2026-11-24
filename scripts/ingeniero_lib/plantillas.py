"""Crea la carpeta docs/ingeniero con las plantillas y el estado inicial."""
import os
import re
import shutil

from . import estado as est_mod
from .util import RAIZ_SKILL


def iniciar(repo, nombre, perfil, existente=False, rapido=False):
    if perfil not in est_mod.PERFILES:
        raise SystemExit("Perfil desconocido '%s'. Opciones: %s" % (perfil, ", ".join(est_mod.PERFILES)))
    if est_mod.existe(repo):
        raise SystemExit("Ya hay un proyecto iniciado en %s. Usa 'estado' para retomarlo." % repo)
    destino = est_mod.carpeta(repo)
    os.makedirs(destino, exist_ok=True)
    origen = os.path.join(RAIZ_SKILL, "plantilla")
    copiados = []
    for archivo in sorted(os.listdir(origen)):
        if not archivo.endswith(".md"):
            continue
        with open(os.path.join(origen, archivo), encoding="utf-8") as f:
            texto = f.read()
        texto = texto.replace("[[nombre del proyecto]]", nombre)
        if archivo == "brief.md":
            texto = re.sub(r"^Fecha: \[\[fecha\]\]", "Fecha: " + est_mod.hoy(), texto, count=1, flags=re.M)
        ruta = os.path.join(destino, archivo)
        if not os.path.exists(ruta):
            with open(ruta, "w", encoding="utf-8", newline="\n") as f:
                f.write(texto)
            copiados.append(archivo)
    est = est_mod.nuevo(nombre, perfil)
    est["entrevista"] = "rapida" if rapido else "completa"
    informe = None
    if existente:
        from . import existente as ex
        informe = ex.detectar_proyecto(repo)
        est["modo"] = "existente"
        est["etapa"] = "construccion"
        est["perfil"] = perfil if perfil != "otro" else informe["perfil_sugerido"]
        est["banderas"].update({k: True for k in informe["banderas_sugeridas"] if k in est_mod.BANDERAS})
        est["comandos"].update(informe["comandos_sugeridos"])
        est["etapas"] = []
    est_mod.registrar(est, "iniciar", "Proyecto \"%s\", perfil %s%s." % (nombre, est["perfil"], " (proyecto existente)" if existente else ""))
    est_mod.guardar(repo, est)
    salida = {"carpeta": os.path.relpath(destino, repo).replace("\\", "/"), "documentos": copiados, "etapa": est["etapa"],
              "modo": est["modo"], "siguiente": est_mod.SIGUIENTE["entrevista"]}
    if existente:
        salida["siguiente"] = ("Se leyó el proyecto. Revisa lo detectado (perfil, banderas y comandos) y corrígelo con 'datos' y "
                               "'comandos'. Luego 'verificar' y 'rescate' para ver qué falta y en qué orden arreglarlo.")
        salida["lo_que_se_leyo"] = informe
    return salida
