"""El estado del proyecto: en qué etapa va, qué se decidió y qué evidencia hay. Es la memoria entre sesiones."""
import datetime
import json
import os

ETAPAS = ["entrevista", "investigacion", "eleccion", "plan", "resumen", "aprobado", "construccion", "salida", "entregado"]
BANDERAS = ["pagos", "datos-personales", "cuentas", "multiusuario", "whatsapp", "movil", "base-de-datos", "archivos", "ia", "interfaz"]
PERFILES = ["agenda", "tienda", "bot", "api", "sitio", "gestion", "movil", "otro"]
COMANDOS = ["pruebas", "lint", "build", "auditoria"]

SIGUIENTE = {
    "entrevista": "Termina el brief con la persona, léeselo y, cuando lo confirme, ejecuta 'avanzar investigacion'.",
    "investigacion": "Investiga lo vigente, compara tres opciones en investigacion.md y ejecuta 'avanzar eleccion'.",
    "eleccion": "Presenta las tres opciones. Cuando la persona elija: 'elegir --opcion X --porque ...' y 'avanzar plan'.",
    "plan": "Escribe casos de uso, arquitectura, datos, pruebas, el pre-mortem y las etapas con su contrato (hecho cuando y cómo se verifica). Cierra todas las [DUDA]. Ejecuta 'verificar' y luego 'avanzar resumen'.",
    "resumen": "Explícale el plan en lenguaje llano y pide el visto bueno. Con sus palabras: 'avanzar aprobado --evidencia ...'.",
    "aprobado": "Ejecuta 'avanzar construccion' para empezar por la etapa 0.",
    "construccion": "Construye la siguiente etapa abierta con pruebas primero y ciérrala con 'etapa-cerrar'. Al terminar todas: 'avanzar salida'.",
    "salida": "Ejecuta 'verificar', completa lo manual con 'marcar' y revisa 'puntaje'. Si no es 'no listo': 'avanzar entregado'.",
    "entregado": "Entrega hecha. El envío a producción lo decide y lo hace la persona con la guía de entrega.",
}


def hoy():
    return os.environ.get("INGENIERO_HOY") or datetime.date.today().isoformat()


def carpeta(repo):
    return os.path.join(repo, "docs", "ingeniero")


def ruta_estado(repo):
    return os.path.join(carpeta(repo), "estado.json")


def existe(repo):
    return os.path.isfile(ruta_estado(repo))


def nuevo(nombre, perfil):
    return {"version": 2, "nombre": nombre, "perfil": perfil, "creado": hoy(), "etapa": "entrevista", "modo": "nuevo",
            "entrevista": "completa",
            "banderas": {b: False for b in BANDERAS}, "comandos": {c: None for c in COMANDOS},
            "eleccion": None, "aprobacion": None,
            "etapas": [etapa_nueva(0, "Esqueleto", ["La estructura por módulos y el marco de pruebas están creados, y una prueba de ejemplo pasa"],
                                  ["item:P2"])],
            "marcas": {}, "descartes": {}, "verificaciones": {}, "historial": []}


def etapa_nueva(id_, nombre, hecho_cuando=None, verificar=None, sin_verificacion=None):
    """Una etapa de construcción con su contrato: cuándo está hecha y cómo se comprueba."""
    return {"id": id_, "nombre": nombre, "estado": "pendiente", "evidencia": None, "fecha": None,
            "hecho_cuando": list(hecho_cuando or []), "verificar": list(verificar or []),
            "sin_verificacion": sin_verificacion, "ultima_verificacion": None}


def cargar(repo):
    ruta = ruta_estado(repo)
    if not os.path.isfile(ruta):
        raise SystemExit("No hay un proyecto iniciado en %s. Empieza con: iniciar --nombre \"...\" --perfil <perfil>" % repo)
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def guardar(repo, est):
    os.makedirs(carpeta(repo), exist_ok=True)
    ruta = ruta_estado(repo)
    tmp = ruta + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(est, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, ruta)


def registrar(est, accion, detalle=""):
    est["historial"].append({"fecha": hoy(), "accion": accion, "detalle": detalle})


def evidencia_valida(texto, minimo_palabras=3, minimo_letras=15):
    """La evidencia tiene que decir algo concreto: no basta con 'ok' ni 'listo'."""
    t = (texto or "").strip()
    return len(t) >= minimo_letras and len(t.split()) >= minimo_palabras
