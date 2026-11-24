#!/usr/bin/env python3
"""ingeniero: estado, comprobaciones y checklist de un proyecto construido por etapas.

Solo librería estándar. Guarda todo en <proyecto>/docs/ingeniero/. Nunca despliega, compra ni instala nada.

  iniciar        Crea docs/ingeniero con las plantillas y el estado.
  estado         En qué etapa va el proyecto, qué falta y cuál es el siguiente paso.
  datos          Declara lo que maneja el proyecto (pagos, datos personales...) y su perfil.
  comandos       Guarda los comandos del proyecto: pruebas, lint, build y auditoría de dependencias.
  avanzar        Pasa a la siguiente etapa si se cumplen sus requisitos.
  retroceder     Vuelve a una etapa anterior (por ejemplo, por un cambio de alcance).
  elegir         Guarda la opción de tecnología que eligió la persona.
  etapa-agregar  Agrega una etapa con su contrato: cuándo está hecha (--hecho-cuando) y cómo se verifica (--verificar).
  etapa-contrato Cambia el contrato de una etapa que ya existe.
  etapa-verificar Corre la verificación de una etapa sin cerrarla.
  etapa-cerrar   Cierra una etapa si su verificación pasa.
  siguiente      Qué etapa sigue; retoma la que quedó a medias si una sesión se cortó.
  traspaso       Documento autosuficiente para que otra instancia, sin contexto, construya el proyecto.
  detectar       Lee un proyecto existente y propone perfil, banderas y comandos.
  rescate        Plan de arreglos de un proyecto existente, de lo más grave a lo menos grave.
  verificar      Corre las comprobaciones automáticas y actualiza el checklist.
  marcar         Registra la evidencia de un ítem que no se puede comprobar solo.
  descartar      Descarta un ítem que no aplica, con su razón (los críticos no se pueden descartar).
  pendientes     Lista lo que falta, lo crítico primero.
  puntaje        Puntaje, críticos pendientes y veredicto.
  tendencia      Compara las dos últimas verificaciones: avisa si el proyecto empeoró.
  informe        Resumen en lenguaje llano para la persona (con --guardar queda en docs/ingeniero/informe.md).
  skills         Qué skills propias están instaladas y cuáles faltan.

Todo se imprime como JSON.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ingeniero_lib import checklist as ck  # noqa: E402
from ingeniero_lib import estado as e  # noqa: E402
from ingeniero_lib import flujo  # noqa: E402
from ingeniero_lib import existente, plantillas, skills_propias  # noqa: E402

SIN_ESTADO = ("iniciar", "skills", "detectar")
SI_NO = {"si": True, "sí": True, "s": True, "true": True, "no": False, "n": False, "false": False}


def _si_no(texto):
    try:
        return SI_NO[texto.strip().lower()]
    except KeyError:
        raise SystemExit("Responde 'si' o 'no' (recibí '%s')." % texto)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ingeniero", description=__doc__.split("\n")[0])
    ap.add_argument("--repo", default=".", help="Carpeta del proyecto (por defecto, la actual)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("iniciar")
    i.add_argument("--nombre", required=True)
    i.add_argument("--perfil", default="otro", help="Uno de: " + ", ".join(e.PERFILES))
    i.add_argument("--existente", action="store_true", help="El proyecto ya existe: se lee en vez de entrevistar y se salta al rescate")
    i.add_argument("--rapido", action="store_true", help="Camino rápido: tres preguntas y supuestos dichos en voz alta")
    sub.add_parser("estado")
    d = sub.add_parser("datos")
    d.add_argument("--perfil", default=None)
    for b in e.BANDERAS:
        d.add_argument("--" + b, dest=b.replace("-", "_"), metavar="si|no", default=None)
    c = sub.add_parser("comandos")
    for k in e.COMANDOS:
        c.add_argument("--" + k, default=None, help="Comando de %s (se ejecuta sin shell, en la carpeta del proyecto)" % k)
    a = sub.add_parser("avanzar")
    a.add_argument("etapa", choices=e.ETAPAS)
    a.add_argument("--evidencia", default=None)
    r = sub.add_parser("retroceder")
    r.add_argument("etapa", choices=e.ETAPAS)
    r.add_argument("--razon", required=True)
    el = sub.add_parser("elegir")
    el.add_argument("--opcion", required=True)
    el.add_argument("--porque", required=True)
    ea = sub.add_parser("etapa-agregar")
    ea.add_argument("--nombre", required=True)
    for p_ in (ea, sub.add_parser("etapa-contrato")):
        if p_ is not ea:
            p_.add_argument("--id", type=int, required=True)
        p_.add_argument("--hecho-cuando", action="append", default=None, dest="hecho_cuando",
                        help="Algo observable que debe ser cierto al terminar (se puede repetir)")
        p_.add_argument("--verificar", action="append", default=None,
                        help="Comando que lo comprueba, o item:ID para un punto del checklist (se puede repetir)")
        p_.add_argument("--sin-verificacion", default=None, dest="sin_verificacion",
                        help="Por qué esta etapa no se puede verificar con un comando")
    ev = sub.add_parser("etapa-verificar")
    ev.add_argument("--id", type=int, required=True)
    ec = sub.add_parser("etapa-cerrar")
    ec.add_argument("--id", type=int, required=True)
    ec.add_argument("--evidencia", default=None, help="Solo hace falta si la etapa no tiene comandos de verificación")
    sg = sub.add_parser("siguiente")
    sg.add_argument("--iniciar", action="store_true", help="Deja la etapa como en curso")
    tr = sub.add_parser("traspaso")
    tr.add_argument("--guardar", action="store_true", help="Guarda el traspaso en docs/ingeniero/traspaso.md")
    sub.add_parser("detectar")
    rs = sub.add_parser("rescate")
    rs.add_argument("--crear-etapas", action="store_true", dest="crear_etapas", help="Agrega el plan como etapas de construcción")
    sub.add_parser("verificar")
    m = sub.add_parser("marcar")
    m.add_argument("id")
    m.add_argument("--evidencia", required=True)
    ds = sub.add_parser("descartar")
    ds.add_argument("id")
    ds.add_argument("--razon", required=True)
    sub.add_parser("pendientes")
    p = sub.add_parser("puntaje")
    p.add_argument("--verificar", action="store_true", help="Corre las comprobaciones antes de calcular")
    p.add_argument("--exigir", type=int, default=None, metavar="N",
                   help="Termina con código 2 si el puntaje es menor que N o queda algún crítico pendiente (para automatizaciones)")
    sub.add_parser("tendencia")
    inf = sub.add_parser("informe")
    inf.add_argument("--guardar", action="store_true", help="Guarda el informe en docs/ingeniero/informe.md")
    sub.add_parser("skills")
    args = ap.parse_args(argv)

    repo = os.path.abspath(args.repo)
    salida_exigida = 0
    if args.cmd == "iniciar":
        out = plantillas.iniciar(repo, args.nombre, args.perfil, existente=args.existente, rapido=args.rapido)
    elif args.cmd == "detectar":
        from ingeniero_lib import existente as _ex
        out = _ex.detectar_proyecto(repo)
    elif args.cmd == "skills":
        out = skills_propias.revisar(repo)
    else:
        est = e.cargar(repo)
        guardar = True
        if args.cmd == "estado":
            out, guardar = flujo.resumen_de_estado(repo, est), False
        elif args.cmd == "datos":
            banderas = {b: _si_no(getattr(args, b.replace("-", "_"))) for b in e.BANDERAS
                        if getattr(args, b.replace("-", "_")) is not None}
            out = flujo.declarar(est, banderas, args.perfil)
        elif args.cmd == "comandos":
            out = flujo.comandos(est, {k: getattr(args, k) for k in e.COMANDOS if getattr(args, k) is not None})
        elif args.cmd == "avanzar":
            out = flujo.avanzar(repo, est, args.etapa, args.evidencia)
        elif args.cmd == "retroceder":
            out = flujo.retroceder(est, args.etapa, args.razon)
        elif args.cmd == "elegir":
            out = flujo.elegir(est, args.opcion, args.porque)
        elif args.cmd == "etapa-agregar":
            out = flujo.etapa_agregar(est, args.nombre, args.hecho_cuando, args.verificar, args.sin_verificacion)
        elif args.cmd == "etapa-contrato":
            out = flujo.etapa_contrato(est, args.id, args.hecho_cuando, args.verificar, args.sin_verificacion)
        elif args.cmd == "etapa-verificar":
            out = flujo.etapa_verificar(repo, est, args.id)
        elif args.cmd == "etapa-cerrar":
            out = flujo.etapa_cerrar(repo, est, args.id, args.evidencia)
        elif args.cmd == "siguiente":
            out = flujo.siguiente(repo, est, args.iniciar)
        elif args.cmd == "traspaso":
            texto = flujo.traspaso_texto(repo, est)
            out, guardar = {"traspaso": texto}, False
            if args.guardar:
                ruta = os.path.join(e.carpeta(repo), "traspaso.md")
                with open(ruta, "w", encoding="utf-8", newline="\n") as f:
                    f.write(texto)
                out["guardado_en"] = os.path.relpath(ruta, repo).replace("\\", "/")
        elif args.cmd == "rescate":
            out = existente.rescate(repo, est, args.crear_etapas)
        elif args.cmd == "verificar":
            out = {"resultados": flujo.verificar(repo, est)}
            out["puntaje"] = ck.puntaje(est)["puntaje"]
        elif args.cmd == "marcar":
            out = flujo.marcar(repo, est, args.id, args.evidencia)
        elif args.cmd == "descartar":
            out = flujo.descartar(est, args.id, args.razon)
        elif args.cmd == "pendientes":
            out, guardar = flujo.pendientes(est), False
        elif args.cmd == "tendencia":
            out, guardar = flujo.tendencia(est), False
        elif args.cmd == "informe":
            texto = flujo.informe(est)
            out, guardar = {"informe": texto}, False
            if args.guardar:
                ruta = os.path.join(e.carpeta(repo), "informe.md")
                with open(ruta, "w", encoding="utf-8", newline="\n") as f:
                    f.write(texto)
                out["guardado_en"] = os.path.relpath(ruta, repo).replace("\\", "/")
        else:  # puntaje
            if args.verificar:
                flujo.verificar(repo, est)
            else:
                guardar = False
            out = ck.puntaje(est)
            if args.exigir is not None:
                salida_exigida = 0 if out["puntaje"] >= args.exigir and not out["criticos_pendientes"] else 2
        if guardar:
            e.guardar(repo, est)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    if salida_exigida:
        sys.exit(salida_exigida)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    main()
