"""El checklist: qué ítems aplican, cuáles se cumplen y con qué evidencia, el puntaje y el veredicto."""
import json
import os

from .util import RAIZ_SKILL


def cargar_items():
    with open(os.path.join(RAIZ_SKILL, "datos", "checklist.json"), encoding="utf-8") as f:
        return json.load(f)["items"]


def aplica(item, est):
    cuando = item.get("cuando", "siempre")
    if cuando == "siempre":
        return True
    resultado = True  # si hay perfiles y banderas, deben cumplirse las dos condiciones
    if "banderas" in cuando:
        resultado = resultado and any(est["banderas"].get(b) for b in cuando["banderas"])
    if "perfiles" in cuando:
        resultado = resultado and est["perfil"] in cuando["perfiles"]
    return resultado


def evaluar(est):
    """Cada ítem que aplica, con su estado: comprobado (lo verificó el script), declarado (evidencia de una persona),
    descartado (con razón) o pendiente."""
    res = []
    for item in cargar_items():
        if not aplica(item, est):
            continue
        fila = {"id": item["id"], "categoria": item["categoria"], "titulo": item["titulo"], "peso": item["peso"],
                "critico": item["critico"], "etapa": item["etapa"],
                "tipo": "auto" if item.get("auto") else ("verificable" if item.get("valida") else "libre")}
        if item["id"] in est["descartes"]:
            fila.update(estado="descartado", detalle=est["descartes"][item["id"]]["razon"])
        elif item.get("auto"):
            v = est["verificaciones"].get(item["id"])
            if v is None:
                fila.update(estado="pendiente", detalle="Sin verificar todavía. Ejecuta: verificar.")
            elif v["ok"]:
                fila.update(estado="comprobado", detalle=v["detalle"])
            else:
                fila.update(estado="pendiente", detalle=v["detalle"])
        else:
            marca = est["marcas"].get(item["id"])
            v = est["verificaciones"].get(item["id"])
            if marca and item.get("valida") and v and not v["ok"]:
                fila.update(estado="pendiente", detalle="La evidencia citaba algo que ya no se encuentra: " + v["detalle"])
            elif marca and item.get("valida"):
                fila.update(estado="declarado_verificado", detalle=marca["evidencia"], fecha=marca["fecha"])
            elif marca:
                fila.update(estado="declarado", detalle=marca["evidencia"], fecha=marca["fecha"])
            else:
                fila.update(estado="pendiente", detalle="Falta evidencia: " + item["evidencia"])
        res.append(fila)
    return res


def puntaje(est):
    filas = evaluar(est)
    activas = [f for f in filas if f["estado"] != "descartado"]
    total = sum(f["peso"] for f in activas)
    comprobado = sum(f["peso"] for f in activas if f["estado"] == "comprobado")
    verificado = sum(f["peso"] for f in activas if f["estado"] == "declarado_verificado")
    declarado = sum(f["peso"] for f in activas if f["estado"] == "declarado")
    logrado = comprobado + verificado + declarado
    nota = round(100 * logrado / total) if total else 0
    criticos = [f for f in activas if f["critico"] and f["estado"] == "pendiente"]
    parte_sin_verificar = (declarado / logrado) if logrado else 0  # lo que nadie ni nada pudo comprobar
    if criticos:
        veredicto = "no_listo"
    elif nota >= 90 and parte_sin_verificar <= 0.25:
        veredicto = "listo"
    elif nota >= 70:
        veredicto = "reservas"
    else:
        veredicto = "no_listo"
    categorias = {}
    for f in activas:
        c = categorias.setdefault(f["categoria"], {"total": 0, "logrado": 0})
        c["total"] += f["peso"]
        if f["estado"] in ("comprobado", "declarado_verificado", "declarado"):
            c["logrado"] += f["peso"]
    return {"puntaje": nota, "total_posible": total, "comprobado_por_el_script": comprobado, "declarado_con_referencia_verificada": verificado,
            "declarado_sin_verificar": declarado, "declarado_con_evidencia": verificado + declarado,
            "pendientes": len([f for f in activas if f["estado"] == "pendiente"]),
            "criticos_pendientes": [{"id": f["id"], "titulo": f["titulo"], "detalle": f["detalle"]} for f in criticos],
            "descartados": [{"id": f["id"], "titulo": f["titulo"], "razon": f["detalle"]} for f in filas if f["estado"] == "descartado"],
            "por_categoria": {k: "%d de %d" % (v["logrado"], v["total"]) for k, v in categorias.items()},
            "veredicto": veredicto, "titulo_veredicto": TITULOS[veredicto]}


TITULOS = {"listo": "LISTO PARA ENVIAR", "reservas": "LISTO CON RESERVAS", "no_listo": "NO ESTÁ LISTO PARA ENVIAR"}
