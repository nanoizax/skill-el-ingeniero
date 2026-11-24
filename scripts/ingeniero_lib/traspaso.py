"""El traspaso: un documento autosuficiente para que otra instancia (sin ningún contexto) construya el proyecto."""
import os

from . import estado as e
from .util import leer, seccion

REGLAS = [
    "Pruebas primero: escribe las pruebas de la etapa, míralas fallar y recién después escribe el código mínimo que las hace pasar.",
    "Una etapa se cierra solo cuando sus comandos de verificación pasan (`ingeniero.py etapa-cerrar`), nunca porque se diga que terminó.",
    "Ningún secreto escrito en el código: las claves salen de variables de entorno, y `.env` no se sube a Git. Los datos de prueba que "
    "parezcan claves llevan en su línea el comentario `pragma: allowlist secret`.",
    "No se agrega nada fuera de la lista de etapas ni de \"Qué se construye\". Un cambio de alcance se avisa a la persona.",
    "Si una prueba falla, se arregla el código o se discute la prueba con la persona. No se borra ni se desactiva para avanzar.",
    "No se despliega, no se compra, no se crean cuentas a nombre de la persona y no se piden claves. El envío a producción lo hace ella.",
    "Commit y push solo si la persona lo pide.",
    "Si falta algo para decidir, se pregunta. No se inventa.",
]


def _sec(repo, doc, titulo, vacio="(sin información)"):
    texto = leer(os.path.join(e.carpeta(repo), doc)) or ""
    cuerpo = (seccion(texto, titulo) or "").strip()
    return cuerpo if cuerpo and "[[" not in cuerpo else vacio


def generar(repo, est):
    eleccion = est.get("eleccion") or {}
    lineas = ["# Traspaso: %s" % est["nombre"], "",
              "Este documento es autosuficiente: una instancia nueva, sin ningún contexto, puede construir el proyecto leyéndolo. "
              "Todo lo que sigue sale de `docs/ingeniero/` y de `estado.json`; si algo no coincide, manda lo que diga ese estado.", "",
              "## Reglas que no se negocian", ""]
    lineas += ["%d. %s" % (i, r) for i, r in enumerate(REGLAS, 1)]
    lineas += ["", "## Qué se construye", "", _sec(repo, "brief.md", "Qué quiere lograr"), "",
               "**Primera versión, imprescindible:**", "", _sec(repo, "brief.md", "Imprescindible"), "",
               "**Fuera de alcance (no se construye):**", "", _sec(repo, "brief.md", "Fuera de alcance"), "",
               "## Pila elegida", "",
               ("Opción %s: %s." % (eleccion.get("opcion"), eleccion.get("porque"))) if eleccion else "(sin elección registrada)", "",
               _sec(repo, "arquitectura.md", "Tecnología"), "",
               "## Estructura del código", "", _sec(repo, "arquitectura.md", "Estructura del código"), "",
               "## Reglas de los datos y de la seguridad", "", _sec(repo, "modelo-de-datos.md", "Reglas de los datos"), "",
               _sec(repo, "seguridad.md", "Riesgos principales"), "", "## Etapas", ""]
    for etapa in est["etapas"]:
        lineas += ["### Etapa %d: %s (%s)" % (etapa["id"], etapa["nombre"], etapa["estado"].replace("_", " ")), "", "**Hecho cuando:**"]
        lineas += ["- %s" % c for c in etapa["hecho_cuando"]] or ["- (sin criterios: pídelos antes de construir)"]
        lineas += ["", "**Cómo se verifica:**"]
        if etapa["verificar"]:
            lineas += ["- `%s`" % c for c in etapa["verificar"]]
        else:
            lineas += ["- %s" % (etapa.get("sin_verificacion") or "(sin verificación definida: pídela antes de construir)")]
        lineas.append("")
    lineas += ["## Cómo trabajar una etapa", "",
               "1. `ingeniero.py --repo <proyecto> siguiente --iniciar` muestra la etapa que sigue y la deja en curso.",
               "2. Escribe las pruebas, míralas fallar, escribe el código mínimo, corre toda la suite.",
               "3. `ingeniero.py --repo <proyecto> etapa-verificar --id N` corre los comandos del contrato sin cerrar la etapa.",
               "4. `ingeniero.py --repo <proyecto> etapa-cerrar --id N` la cierra si la verificación pasa.",
               "5. Si la sesión se corta, `siguiente` retoma la etapa en curso y comprueba cómo quedó.",
               "6. Al terminar todas: `verificar`, `puntaje` y una revisión independiente (la hace alguien que no construyó).", "",
               "## Comandos del proyecto", ""]
    comandos = {k: v for k, v in (est.get("comandos") or {}).items() if v}
    lineas += ["- %s: `%s`" % (k, v) for k, v in comandos.items()] or ["- (sin comandos configurados: `ingeniero.py comandos`)"]
    lineas += ["", "## Dónde leer más", "",
               "- `docs/ingeniero/casos-de-uso.md`: los casos de uso con su criterio de aceptación.",
               "- `docs/ingeniero/arquitectura.md` y `modelo-de-datos.md`: el diseño completo.",
               "- `docs/ingeniero/seguridad.md` y `premortem.md`: los riesgos y qué se hará con cada uno.",
               "- `docs/ingeniero/entrega.md`: la guía de entrega para la persona.", ""]
    return "\n".join(lineas)
