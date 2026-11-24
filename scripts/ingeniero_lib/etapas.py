"""El contrato de cada etapa de construcción: cuándo está hecha y cómo se comprueba, y la forma de retomarla.

Una etapa no se cierra porque alguien diga que terminó: se cierra cuando sus comandos de verificación pasan.
Un comando puede ser uno del proyecto (por ejemplo `python -m pytest -q tests/test_citas.py`) o `item:S1`, que exige
que pase la comprobación automática de ese punto del checklist.
"""
import re

from . import checklist as ck
from . import estado as e
from . import verificar as ver


def _buscar(est, id_):
    etapa = next((x for x in est["etapas"] if x["id"] == id_), None)
    if not etapa:
        raise SystemExit("No existe la etapa %s." % id_)
    return etapa


def _revisar_contrato(hecho_cuando, verificar):
    for criterio in hecho_cuando or []:
        if len(criterio.split()) < 4:
            raise SystemExit("Cada \"hecho cuando\" tiene que decir algo concreto (al menos cuatro palabras): \"%s\"." % criterio)
    vagas = ver.frases_vagas_en("\n".join(hecho_cuando or []))
    if vagas:
        raise SystemExit("Los criterios usan frases que no se pueden comprobar (%s). Describe qué se ve o qué se recibe, con un dato "
                         "concreto." % ", ".join(vagas[:4]))
    for cmd in verificar or []:
        if not cmd.strip():
            raise SystemExit("Un comando de verificación no puede estar vacío.")
        if cmd.strip().lower().startswith("item:"):
            item = next((i for i in ck.cargar_items() if i["id"] == cmd.strip()[5:].strip().upper()), None)
            if not item or not item.get("auto"):
                raise SystemExit("\"%s\" no es un punto del checklist que se compruebe solo." % cmd)


def agregar(est, nombre, hecho_cuando=None, verificar=None, sin_verificacion=None):
    if e.ETAPAS.index(est["etapa"]) < e.ETAPAS.index("plan") or est["etapa"] == "entregado":
        raise SystemExit("Las etapas de construcción se definen desde el plan hasta la construcción (ahora: %s)." % est["etapa"])
    if not nombre.strip():
        raise SystemExit("La etapa necesita un nombre.")
    _revisar_contrato(hecho_cuando, verificar)
    nueva = e.etapa_nueva(max([x["id"] for x in est["etapas"]] + [-1]) + 1, nombre.strip(), hecho_cuando, verificar, sin_verificacion)
    est["etapas"].append(nueva)
    e.registrar(est, "etapa-agregar", "%d %s" % (nueva["id"], nueva["nombre"]))
    return nueva


def contrato(est, id_, hecho_cuando=None, verificar=None, sin_verificacion=None):
    etapa = _buscar(est, id_)
    _revisar_contrato(hecho_cuando, verificar)
    if hecho_cuando is not None:
        etapa["hecho_cuando"] = list(hecho_cuando)
    if verificar is not None:
        etapa["verificar"] = list(verificar)
    if sin_verificacion is not None:
        etapa["sin_verificacion"] = sin_verificacion
    etapa["ultima_verificacion"] = None  # el contrato cambió: la verificación anterior ya no vale
    e.registrar(est, "etapa-contrato", "%d %s" % (etapa["id"], etapa["nombre"]))
    return etapa


def _correr(repo, est, cmd):
    if cmd.strip().lower().startswith("item:"):
        item = next(i for i in ck.cargar_items() if i["id"] == cmd.strip()[5:].strip().upper())
        return ver.comprobar(repo, est, item)
    return ver.correr_comando(repo, cmd)


def verificar_etapa(repo, est, id_):
    """Corre los comandos del contrato de la etapa y guarda el resultado. No cambia el estado de la etapa."""
    etapa = _buscar(est, id_)
    if not etapa["verificar"]:
        ok = bool(etapa.get("sin_verificacion"))
        return {"id": etapa["id"], "nombre": etapa["nombre"], "ok": ok, "resultados": [],
                "mensaje": ("Esta etapa se declaró sin verificación automática: %s" % etapa["sin_verificacion"]) if ok else
                           "La etapa no dice cómo se verifica. Define comandos con etapa-contrato o explica por qué no se puede."}
    resultados = []
    for cmd in etapa["verificar"]:
        ok, detalle = _correr(repo, est, cmd)
        resultados.append({"comando": cmd, "ok": ok, "detalle": detalle})
    ok = all(r["ok"] for r in resultados)
    etapa["ultima_verificacion"] = {"ok": ok, "fecha": e.hoy(), "resultados": resultados}
    return {"id": etapa["id"], "nombre": etapa["nombre"], "ok": ok, "resultados": resultados}


def _punto_de_retorno(etapa):
    slug = re.sub(r"[^a-z0-9]+", "-", etapa["nombre"].lower()).strip("-")[:30]
    return "git tag etapa-%02d-%s" % (etapa["id"], slug)


def cerrar(repo, est, id_, evidencia=None):
    if est["etapa"] != "construccion":
        raise SystemExit("Las etapas se cierran durante la construcción (ahora: %s)." % est["etapa"])
    etapa = _buscar(est, id_)
    if etapa["estado"] == "cerrada":
        raise SystemExit("La etapa %s ya estaba cerrada." % id_)
    anteriores = [x for x in est["etapas"] if x["id"] < id_ and x["estado"] != "cerrada"]
    if anteriores:
        raise SystemExit("Antes hay que cerrar la etapa %s (%s)." % (anteriores[0]["id"], anteriores[0]["nombre"]))
    if not etapa["verificar"] and not etapa.get("sin_verificacion"):
        raise SystemExit("La etapa %s no dice cómo se verifica. Define comandos con etapa-contrato o explica por qué no se puede "
                         "con --sin-verificacion." % id_)
    if etapa["verificar"]:
        r = verificar_etapa(repo, est, id_)
        if not r["ok"]:
            return {"cerrada": False, "id": id_, "nombre": etapa["nombre"], "motivo": "La verificación de la etapa no pasó.",
                    "fallos": [x for x in r["resultados"] if not x["ok"]]}
        texto = "Verificación ejecutada: " + "; ".join(x["comando"] for x in r["resultados"]) + "."
        if evidencia and evidencia.strip():
            texto += " " + evidencia.strip()
    else:
        if not e.evidencia_valida(evidencia, minimo_palabras=4, minimo_letras=25):
            raise SystemExit("Una etapa sin verificación automática pide evidencia: qué se comprobó a mano y con qué resultado.")
        texto = evidencia.strip()
    etapa.update(estado="cerrada", evidencia=texto, fecha=e.hoy())
    e.registrar(est, "etapa-cerrar", "%d %s" % (etapa["id"], etapa["nombre"]))
    return {"cerrada": True, "id": etapa["id"], "nombre": etapa["nombre"], "estado": "cerrada", "evidencia": texto,
            "punto_de_retorno": "Si la persona lo pide, deja un punto de retorno: %s" % _punto_de_retorno(etapa)}


def _tarjeta(etapa):
    return {"id": etapa["id"], "nombre": etapa["nombre"], "estado": etapa["estado"], "hecho_cuando": etapa["hecho_cuando"],
            "verificar": etapa["verificar"], "sin_verificacion": etapa.get("sin_verificacion")}


def siguiente(repo, est, iniciar=False):
    """Qué sigue. Si una etapa quedó 'en curso' (una sesión se cortó), la retoma y comprueba cómo quedó."""
    if est["etapa"] != "construccion":
        return {"mensaje": "Las etapas se trabajan en la construcción (ahora: %s). %s" % (est["etapa"], e.SIGUIENTE[est["etapa"]])}
    en_curso = [x for x in est["etapas"] if x["estado"] == "en_curso"]
    if en_curso:
        etapa = en_curso[0]
        return {"reanudando": True, "etapa": _tarjeta(etapa), "verificacion_ahora": verificar_etapa(repo, est, etapa["id"]),
                "mensaje": "Esta etapa quedó a medias. Revisa cómo está el árbol de trabajo antes de seguir, y cierra con etapa-cerrar "
                           "cuando la verificación pase."}
    pendientes = sorted((x for x in est["etapas"] if x["estado"] == "pendiente"), key=lambda x: x["id"])
    if not pendientes:
        return {"mensaje": "No quedan etapas abiertas. Ejecuta 'verificar' y 'avanzar salida'."}
    etapa = pendientes[0]
    if iniciar:
        etapa["estado"] = "en_curso"
        e.registrar(est, "etapa-iniciar", "%d %s" % (etapa["id"], etapa["nombre"]))
    return {"reanudando": False, "iniciada": bool(iniciar), "etapa": _tarjeta(etapa),
            "como_cerrar": "Cuando la verificación pase: etapa-cerrar --id %d. Pruebas primero, código mínimo, toda la suite." % etapa["id"]}
