"""Las acciones del proyecto: cambiar de etapa, elegir, marcar evidencia, verificar y resumir el estado."""
from . import checklist as ck
from . import estado as e
import json
import os

from . import etapas, referencias
from . import traspaso as traspaso_mod
from . import verificar as ver

_GENERICAS = {"ok", "listo", "hecho", "si", "sí", "bien", "perfecto", "ya", "todo bien"}


def _item(id_):
    for i in ck.cargar_items():
        if i["id"] == id_.upper():
            return i
    raise SystemExit("No existe el ítem %s en el checklist." % id_)


def verificar(repo, est, ids=None):
    """Corre las comprobaciones automáticas de los ítems que aplican (o solo las de `ids`) y las guarda."""
    resultados = []
    for item in ck.cargar_items():
        if not item.get("auto") or not ck.aplica(item, est) or (ids and item["id"] not in ids):
            continue
        ok, detalle = ver.comprobar(repo, est, item)
        est["verificaciones"][item["id"]] = {"ok": ok, "detalle": detalle, "fecha": e.hoy()}
        resultados.append({"id": item["id"], "titulo": item["titulo"], "cumple": ok, "detalle": detalle})
    for item in ck.cargar_items():  # la evidencia declarada tiene que seguir citando cosas que existen
        marca = est["marcas"].get(item["id"])
        if item.get("auto") or not item.get("valida") or not marca or not ck.aplica(item, est) or (ids and item["id"] not in ids):
            continue
        ok, detalle = referencias.validar(repo, item, marca["evidencia"])
        est["verificaciones"][item["id"]] = {"ok": ok, "detalle": detalle, "fecha": e.hoy()}
        resultados.append({"id": item["id"], "titulo": item["titulo"], "cumple": ok, "detalle": detalle})
    if not ids:
        registrar_puntaje(est)
    return resultados


def marcar(repo, est, id_, evidencia):
    item = _item(id_)
    if item.get("auto"):
        raise SystemExit("%s se comprueba solo: ejecuta 'verificar'. Si falla, arregla lo que dice, no lo marques a mano." % item["id"])
    if not e.evidencia_valida(evidencia) or evidencia.strip().lower() in _GENERICAS:
        raise SystemExit("La evidencia tiene que ser concreta (qué se hizo, dónde, con qué resultado). Se pide: %s" % item["evidencia"])
    estado = "declarado"
    if item.get("valida"):
        ok, detalle = referencias.validar(repo, item, evidencia)
        if not ok:
            raise SystemExit("No se registró %s. %s" % (item["id"], detalle))
        est["verificaciones"][item["id"]] = {"ok": True, "detalle": detalle, "fecha": e.hoy()}
        estado = "declarado_verificado"
    est["marcas"][item["id"]] = {"evidencia": evidencia.strip(), "fecha": e.hoy()}
    e.registrar(est, "marcar", item["id"])
    return {"id": item["id"], "titulo": item["titulo"], "estado": estado, "evidencia": evidencia.strip()}


def descartar(est, id_, razon):
    item = _item(id_)
    if item["critico"]:
        raise SystemExit("%s es crítico y no se puede descartar. Si de verdad no aplica, cambia lo que se declaró con 'datos'." % item["id"])
    if not e.evidencia_valida(razon, minimo_palabras=4, minimo_letras=20):
        raise SystemExit("Explica por qué no aplica (al menos cuatro palabras).")
    est["descartes"][item["id"]] = {"razon": razon.strip(), "fecha": e.hoy()}
    e.registrar(est, "descartar", "%s: %s" % (item["id"], razon.strip()))
    return {"id": item["id"], "estado": "descartado", "razon": razon.strip()}


def declarar(est, banderas=None, perfil=None):
    for nombre, valor in (banderas or {}).items():
        if nombre not in e.BANDERAS:
            raise SystemExit("Bandera desconocida '%s'. Opciones: %s" % (nombre, ", ".join(e.BANDERAS)))
        est["banderas"][nombre] = bool(valor)
    if perfil:
        if perfil not in e.PERFILES:
            raise SystemExit("Perfil desconocido '%s'. Opciones: %s" % (perfil, ", ".join(e.PERFILES)))
        est["perfil"] = perfil
    e.registrar(est, "datos", ", ".join("%s=%s" % (k, "sí" if v else "no") for k, v in est["banderas"].items() if v) or "ninguna")
    return {"banderas": est["banderas"], "perfil": est["perfil"]}


def comandos(est, valores):
    for clave, v in valores.items():
        if clave not in e.COMANDOS:
            raise SystemExit("Comando desconocido '%s'. Opciones: %s" % (clave, ", ".join(e.COMANDOS)))
        est["comandos"][clave] = v
    e.registrar(est, "comandos", ", ".join("%s: %s" % (k, v) for k, v in est["comandos"].items() if v))
    return {"comandos": est["comandos"]}


def elegir(est, opcion, porque):
    if est["etapa"] != "eleccion":
        raise SystemExit("La elección se hace en la etapa 'eleccion' (ahora: %s)." % est["etapa"])
    if not e.evidencia_valida(porque, minimo_palabras=3, minimo_letras=10):
        raise SystemExit("Guarda por qué eligió esa opción, con sus palabras.")
    est["eleccion"] = {"opcion": opcion.strip(), "porque": porque.strip(), "fecha": e.hoy()}
    e.registrar(est, "elegir", "%s: %s" % (opcion.strip(), porque.strip()))
    return est["eleccion"]


def etapa_agregar(est, nombre, hecho_cuando=None, verificar=None, sin_verificacion=None):
    return etapas.agregar(est, nombre, hecho_cuando, verificar, sin_verificacion)


def etapa_contrato(est, id_, hecho_cuando=None, verificar=None, sin_verificacion=None):
    return etapas.contrato(est, id_, hecho_cuando, verificar, sin_verificacion)


def etapa_verificar(repo, est, id_):
    return etapas.verificar_etapa(repo, est, id_)


def etapa_cerrar(repo, est, id_, evidencia=None):
    return etapas.cerrar(repo, est, id_, evidencia)


def siguiente(repo, est, iniciar=False):
    return etapas.siguiente(repo, est, iniciar)


def _sin_contrato(est):
    """Etapas a las que todavía les falta decir cuándo están hechas y cómo se verifican."""
    return ["%d (%s)" % (x["id"], x["nombre"]) for x in est["etapas"]
            if not x.get("hecho_cuando") or not (x.get("verificar") or x.get("sin_verificacion"))]


def _faltantes(repo, est, destino):
    """Qué le falta al proyecto para entrar en la etapa `destino`."""
    def falla(ids):
        return [r["id"] + ": " + r["detalle"] for r in verificar(repo, est, ids) if not r["cumple"]]
    if destino == "investigacion":
        return falla({"R1", "R3", "R6"})
    if destino == "eleccion":
        return falla({"I1"})
    if destino == "plan":
        return [] if est.get("eleccion") else ["La persona todavía no eligió una opción (usa 'elegir')."]
    if destino == "resumen":
        faltan = falla({"R2", "A1", "A3", "S10", "R6", "R7"})
        if len(est["etapas"]) < 2:
            faltan.append("Define al menos una etapa de construcción además del esqueleto ('etapa-agregar').")
        sin = _sin_contrato(est)
        if sin:
            faltan.append("Falta el contrato de estas etapas (cuándo están hechas y cómo se verifican): %s." % ", ".join(sin))
        return faltan
    if destino == "aprobado":
        return falla({"R4"})
    if destino == "construccion":
        faltan = [] if est.get("aprobacion") else ["La persona todavía no aprobó el plan."]
        sin = _sin_contrato(est)
        if sin:
            faltan.append("Falta el contrato de estas etapas (cuándo están hechas y cómo se verifican): %s." % ", ".join(sin))
        return faltan
    if destino == "salida":
        return falla({"E6"})
    if destino == "entregado":
        faltan = []
        if "E4" not in est["marcas"]:
            faltan.append("E4: falta la evidencia de que la persona entiende que el envío es decisión suya.")
        verificar(repo, est)
        if ck.puntaje(est)["veredicto"] == "no_listo":
            faltan.append("El veredicto es 'no está listo para enviar'. Revisa 'puntaje'.")
        return faltan
    return []


def avanzar(repo, est, destino, evidencia=None):
    if destino not in e.ETAPAS:
        raise SystemExit("Etapa desconocida '%s'. Opciones: %s" % (destino, ", ".join(e.ETAPAS)))
    actual, nuevo = e.ETAPAS.index(est["etapa"]), e.ETAPAS.index(destino)
    if nuevo == actual:
        raise SystemExit("Ya estás en la etapa %s." % destino)
    if nuevo < actual:
        raise SystemExit("Para volver atrás usa 'retroceder --razon ...'.")
    if nuevo > actual + 1:
        raise SystemExit("No se puede saltar etapas: sigue '%s'." % e.ETAPAS[actual + 1])
    if destino == "aprobado":
        if not e.evidencia_valida(evidencia, minimo_palabras=1, minimo_letras=2) or (evidencia or "").strip() == "":
            raise SystemExit("Guarda con --evidencia las palabras con que la persona aprobó el plan.")
    faltan = _faltantes(repo, est, destino)
    if faltan:
        return {"avanzo": False, "etapa": est["etapa"], "faltan": faltan}
    if destino == "aprobado":
        est["aprobacion"] = {"evidencia": evidencia.strip(), "fecha": e.hoy()}
    est["etapa"] = destino
    e.registrar(est, "avanzar", destino + ((": " + evidencia.strip()) if evidencia else ""))
    return {"avanzo": True, "etapa": destino, "siguiente": e.SIGUIENTE[destino]}


def retroceder(est, destino, razon):
    if destino not in e.ETAPAS:
        raise SystemExit("Etapa desconocida '%s'." % destino)
    if e.ETAPAS.index(destino) >= e.ETAPAS.index(est["etapa"]):
        raise SystemExit("Solo se puede retroceder a una etapa anterior a '%s'." % est["etapa"])
    if not e.evidencia_valida(razon, minimo_palabras=3, minimo_letras=15):
        raise SystemExit("Explica por qué se retrocede (por ejemplo, un cambio de alcance).")
    if e.ETAPAS.index(destino) < e.ETAPAS.index("aprobado"):
        est["aprobacion"] = None  # un plan que cambia hay que volver a aprobarlo
    if e.ETAPAS.index(destino) <= e.ETAPAS.index("eleccion"):
        est["eleccion"] = None  # si se vuelve a investigar o a elegir, la elección anterior ya no vale
    est["etapa"] = destino
    e.registrar(est, "retroceder", "%s: %s" % (destino, razon.strip()))
    return {"etapa": destino, "aviso": "Si el plan cambió, la persona tiene que volver a aprobarlo." if est["aprobacion"] is None else ""}


def resumen_de_estado(repo, est):
    p = ck.puntaje(est)
    abiertas = [x for x in est["etapas"] if x["estado"] != "cerrada"]
    return {"proyecto": est["nombre"], "perfil": est["perfil"], "etapa": est["etapa"], "modo": est.get("modo", "nuevo"),
            "entrevista": est.get("entrevista", "completa"), "siguiente": e.SIGUIENTE[est["etapa"]],
            "guias_sin_revisar": guias_sin_revisar(),
            "banderas_activas": [k for k, v in est["banderas"].items() if v], "eleccion": est["eleccion"],
            "aprobacion": est["aprobacion"], "etapas_de_construccion": est["etapas"],
            "etapa_abierta": abiertas[0] if abiertas else None,
            "puntaje": p["puntaje"], "veredicto": p["titulo_veredicto"], "criticos_pendientes": len(p["criticos_pendientes"]),
            "ultima_verificacion": max((v["fecha"] for v in est["verificaciones"].values()), default=None),
            "historial_reciente": est["historial"][-5:]}


def pendientes(est):
    filas = [f for f in ck.evaluar(est) if f["estado"] == "pendiente"]
    orden = {n: i for i, n in enumerate(e.ETAPAS)}
    filas.sort(key=lambda f: (not f["critico"], orden.get(f["etapa"], 99), -f["peso"]))
    return [{"id": f["id"], "critico": f["critico"], "tipo": f["tipo"], "titulo": f["titulo"], "que_falta": f["detalle"]} for f in filas]


def registrar_puntaje(est):
    """Guarda el puntaje de esta verificación completa, para poder ver si el proyecto mejora o empeora."""
    p = ck.puntaje(est)
    historia = est.setdefault("puntajes", [])
    registro = {"fecha": e.hoy(), "puntaje": p["puntaje"], "criticos_pendientes": len(p["criticos_pendientes"]),
                "comprobado": p["comprobado_por_el_script"]}
    if not historia or any(historia[-1][k] != registro[k] for k in ("puntaje", "criticos_pendientes", "comprobado")):
        historia.append(registro)
    del historia[:-50]


def tendencia(est):
    """Compara las dos últimas verificaciones y avisa si algo empeoró (por ejemplo, alguien borró una prueba)."""
    historia = est.get("puntajes", [])
    if len(historia) < 2:
        return {"registros": historia, "veredicto": "sin_historia",
                "mensaje": "Hace falta al menos dos verificaciones para comparar. Ejecuta 'verificar' después de cada cambio."}
    antes, ahora = historia[-2], historia[-1]
    cambio = ahora["puntaje"] - antes["puntaje"]
    nuevos_criticos = ahora["criticos_pendientes"] - antes["criticos_pendientes"]
    if cambio <= -5 or nuevos_criticos > 0:
        veredicto, mensaje = "empeoro", "El proyecto empeoró desde la verificación anterior (%+d puntos, %+d críticos pendientes). " \
            "Mira qué cambió: puede que se haya borrado una prueba o un archivo." % (cambio, nuevos_criticos)
    elif cambio > 0:
        veredicto, mensaje = "mejoro", "El proyecto mejoró %d puntos desde la verificación anterior." % cambio
    else:
        veredicto, mensaje = "estable", "Sin cambios importantes desde la verificación anterior."
    return {"registros": historia[-10:], "cambio_de_puntaje": cambio, "veredicto": veredicto, "mensaje": mensaje}


_ETAPA_EN_PALABRAS = {
    "entrevista": "Estamos conversando para entender bien lo que necesitas.",
    "investigacion": "Estamos investigando qué tecnología conviene hoy.",
    "eleccion": "Estás eligiendo entre las opciones que se investigaron.",
    "plan": "Estamos escribiendo el plan completo.",
    "resumen": "El plan está listo y espera tu visto bueno.",
    "aprobado": "Aprobaste el plan y empieza la construcción.",
    "construccion": "Estamos construyendo, una etapa pequeña a la vez.",
    "salida": "Estamos comprobando que todo esté listo para enviar.",
    "entregado": "La entrega está hecha. El envío a producción lo decides tú.",
}


def informe(est):
    """Resumen del estado en lenguaje llano, para la persona que no programa. Sin códigos ni jerga."""
    p = ck.puntaje(est)
    filas = ck.evaluar(est)
    pendientes = [f for f in filas if f["estado"] == "pendiente"]
    criticas = [f for f in pendientes if f["critico"]]
    otras = sorted((f for f in pendientes if not f["critico"]), key=lambda f: -f["peso"])[:8]
    hechas = len([f for f in filas if f["estado"] in ("comprobado", "declarado_verificado", "declarado")])
    etapas = est["etapas"]
    cerradas = len([x for x in etapas if x["estado"] == "cerrada"])
    lineas = ["# Cómo va %s" % est["nombre"], "", _ETAPA_EN_PALABRAS[est["etapa"]], "",
              "Se construyeron %d de %d etapas. De los %d puntos que revisamos, hay %d en orden y %d por resolver." % (
                  cerradas, len(etapas), len(filas), hechas, len(pendientes)),
              "Puntaje: %d de 100. Veredicto: %s." % (p["puntaje"], p["titulo_veredicto"].lower()), ""]
    lineas += ["## Lo más importante que falta", ""]
    lineas += ["- %s" % f["titulo"] for f in criticas] or ["- Nada crítico pendiente."]
    lineas += ["", "## Otras cosas por resolver", ""]
    lineas += ["- %s" % f["titulo"] for f in otras] or ["- Nada más por ahora."]
    lineas += ["", "## Lo que decides tú", "",
               "- Cuándo y dónde se publica el producto. Nosotros no lo publicamos.",
               "- Qué cuentas se crean y a nombre de quién.",
               "- Si quieres cambiar algo del plan: dínoslo y lo volvemos a revisar contigo.", ""]
    return "\n".join(lineas)


def guias_sin_revisar():
    """Las guías con datos que envejecen (perfiles, opciones, skills) llevan fecha de revisión: se avisa si pasó mucho tiempo."""
    import datetime
    from .util import RAIZ_SKILL
    ruta = os.path.join(RAIZ_SKILL, "datos", "vigencia.json")
    try:
        with open(ruta, encoding="utf-8") as f:
            datos = json.load(f)
        hoy = datetime.date.fromisoformat(e.hoy())
        return [{"guia": g, "dias": (hoy - datetime.date.fromisoformat(f)).days} for g, f in datos["revisado"].items()
                if (hoy - datetime.date.fromisoformat(f)).days > datos["dias_maximos"]]
    except (OSError, ValueError, KeyError):
        return []


def traspaso_texto(repo, est):
    return traspaso_mod.generar(repo, est)
