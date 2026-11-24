"""Pruebas de la skill el-ingeniero: flujo por etapas, comprobaciones automáticas, checklist, puntaje y plantillas."""
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, os.path.join(RAIZ, "scripts"))

from ingeniero_lib import checklist as ck  # noqa: E402
from ingeniero_lib import estado as e  # noqa: E402
from ingeniero_lib import flujo, plantillas, referencias, skills_propias, verificar  # noqa: E402
from ingeniero_lib.util import palabras, seccion  # noqa: E402

CLI = [sys.executable, os.path.join(RAIZ, "scripts", "ingeniero.py")]


def _borrar(func, ruta, _):
    os.chmod(ruta, stat.S_IWRITE)
    func(ruta)


def leer_archivo(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


CMD_OK = '"%s" -c "print(1)"' % sys.executable
CMD_MAL = '"%s" -c "raise SystemExit(3)"' % sys.executable
CRITERIO = "La persona ve la cita confirmada con su hora y su barbero"


def premortem_completo():
    riesgos = "".join("### Riesgo %d: algo\n- Por qué podría pasar: porque sí\n- Qué haremos: una medida concreta para evitarlo\n\n" % n
                      for n in (1, 2, 3))
    angulos = "".join("- Ángulo %d: respuesta concreta sobre este punto\n" % n for n in range(1, 9))
    return ("# Pre-mortem\n\n## Qué pasaría si fracasa en seis meses\n%s\n\n## Los riesgos que sobrevivieron\n\n%s"
            "## Los ocho ángulos revisados\n%s" % (" ".join(["palabra"] * 40), riesgos, angulos))


def parrafo(n):
    return " ".join(["palabra"] * n)


def escribir(repo, ruta, texto):
    p = os.path.join(repo, *ruta.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(texto)


def git(repo, *args):
    r = subprocess.run(["git", "-C", repo, "-c", "user.name=Prueba", "-c", "user.email=p@example.invalid"] + list(args),
                       capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    return r.stdout


class Proyecto(unittest.TestCase):
    """Un proyecto vacío con el ingeniero iniciado (perfil agenda)."""

    def setUp(self):
        self.repo = tempfile.mkdtemp(prefix="ing-")
        self.addCleanup(lambda: shutil.rmtree(self.repo, onerror=_borrar))
        plantillas.iniciar(self.repo, "Barbería de prueba", "agenda")
        self.est = e.cargar(self.repo)

    def doc(self, nombre, texto):
        escribir(self.repo, "docs/ingeniero/" + nombre, texto)

    def guardar(self):
        e.guardar(self.repo, self.est)

    def llenar_brief(self):
        self.doc("brief.md", "# Brief\n\n## Qué quiere lograr\n%s\n\n## Fuera de alcance\n- %s\n\n## Confirmación\n"
                 "La persona confirmó este brief con estas palabras: \"sí, es correcto\".\n" % (parrafo(100), parrafo(6)))

    def llenar_investigacion(self):
        self.doc("investigacion.md", "# Investigación\n\nFecha de la investigación: 2026-11-24\n\n## Hallazgos\n"
                 "- uno [fuente: oficial]: https://a.example/1\n- dos [fuente: secundaria]: https://b.example/2\n- tres [fuente: opinión]: https://c.example/3\n\n"
                 "### Opción A: uno\ntexto\n### Opción B: dos\ntexto\n### Opción C: tres\ntexto\n\n"
                 "## Recomendación\n%s\n\n## Elección de la persona\npendiente\n\n## Skills y repositorios revisados\n%s\n\n"
                 "## No verificado\nninguno\n" % (parrafo(15), parrafo(12)))

    def llenar_plan(self):
        casos = "".join("## Caso %d: algo\n- Criterio de aceptación:\n  - Dado una cosa, cuando pasa algo, entonces ocurre.\n\n" % n
                        for n in (1, 2, 3))
        self.doc("casos-de-uso.md", "# Casos de uso\n\n" + casos)
        self.doc("arquitectura.md", "# Arquitectura\n\n%s\n" % parrafo(130))
        self.doc("modelo-de-datos.md", "# Modelo\n\n%s\n" % parrafo(70))
        self.doc("seguridad.md", "# Seguridad\n\n## Datos personales\n%s\n\n## Cuentas y permisos\n%s\n" % (parrafo(35), parrafo(10)))
        self.doc("plan-de-pruebas.md", "# Plan\n\n%s\n" % parrafo(50))
        self.doc("premortem.md", premortem_completo())

    def llenar_resumen(self):
        frase = "Vas a poder agendar las citas desde el celular y ver la caja del día."
        self.doc("resumen-para-la-persona.md", "# Resumen\n\n%s\n" % " ".join([frase] * 8))

    def llenar_entrega(self):
        self.doc("entrega.md", "# Guía de entrega\n\n## Qué recibes\n%s\n\n## Variables de entorno\n%s\n\n"
                 "## Costos mensuales estimados\n%s\n\n## Cuentas que debes crear tú\n%s\n\n## Respaldo y restauración\n%s\n"
                 % (parrafo(30), parrafo(20), parrafo(20), parrafo(15), parrafo(110)))


class TestPlantillas(Proyecto):
    def test_iniciar_crea_los_documentos_y_el_estado(self):
        archivos = set(os.listdir(os.path.join(self.repo, "docs", "ingeniero")))
        self.assertLessEqual({"brief.md", "investigacion.md", "casos-de-uso.md", "arquitectura.md", "modelo-de-datos.md",
                              "plan-de-pruebas.md", "seguridad.md", "entrega.md", "resumen-para-la-persona.md", "etapas.md",
                              "estado.json"}, archivos)
        self.assertEqual((self.est["etapa"], self.est["perfil"], self.est["nombre"]), ("entrevista", "agenda", "Barbería de prueba"))
        brief = leer_archivo(os.path.join(self.repo, "docs", "ingeniero", "brief.md"))
        self.assertIn("Barbería de prueba", brief)
        self.assertRegex(brief, r"Fecha: \d{4}-\d{2}-\d{2}")
        self.assertIn("[[", brief)  # lo demás son huecos que hay que llenar

    def test_no_se_pisa_un_proyecto_ni_se_acepta_un_perfil_inventado(self):
        with self.assertRaises(SystemExit):
            plantillas.iniciar(self.repo, "otro", "agenda")
        otro = tempfile.mkdtemp(prefix="ing-")
        self.addCleanup(lambda: shutil.rmtree(otro, onerror=_borrar))
        with self.assertRaises(SystemExit):
            plantillas.iniciar(otro, "x", "inventado")

    def test_el_estado_dice_donde_va_sin_proyecto_se_niega(self):
        otro = tempfile.mkdtemp(prefix="ing-")
        self.addCleanup(lambda: shutil.rmtree(otro, onerror=_borrar))
        with self.assertRaises(SystemExit):
            e.cargar(otro)


class TestSeccion(unittest.TestCase):
    def test_busca_sin_tildes_ni_mayusculas_y_corta_en_el_siguiente_encabezado(self):
        t = "# A\nuno\n## Confirmación\ndos tres\n### Sub\ncuatro\n## Otra\ncinco\n"
        self.assertEqual(palabras(seccion(t, "confirmacion")), 4)  # incluye su subsección
        self.assertIsNone(seccion(t, "No existe"))
        self.assertEqual(seccion(t, "Otra").strip(), "cinco")


class TestComprobaciones(Proyecto):
    def comprobar(self, tipo, **extra):
        return verificar.TIPOS[tipo](self.repo, self.est, dict(extra))

    def test_secretos_en_archivos_y_placeholders(self):
        escribir(self.repo, "src/a.js", "const x = 1;\n")
        self.assertTrue(self.comprobar("secretos")[0])
        escribir(self.repo, "src/config.js", 'const k = "AKIAABCDEFGHIJKLMNOP";\n')
        ok, detalle = self.comprobar("secretos")
        self.assertFalse(ok)
        self.assertIn("AWS", detalle)
        escribir(self.repo, "src/config.js", "const k = process.env.CLAVE;\nconst ejemplo = 'tu_clave_aqui_12345';\n")
        self.assertTrue(self.comprobar("secretos")[0])
        escribir(self.repo, "src/db.py", 'password = "Zx9Kq2Lm8Rt4Vw7"\n')
        self.assertFalse(self.comprobar("secretos")[0])

    def test_una_linea_marcada_como_dato_de_prueba_no_cuenta_pero_la_de_al_lado_si(self):
        escribir(self.repo, "tests/ayudas.py", 'CONTRASENA = "contrasena-ficticia-123"  # pragma: allowlist secret (dato de prueba)\n')
        self.assertTrue(self.comprobar("secretos")[0])
        escribir(self.repo, "tests/ayudas.py", 'CONTRASENA = "contrasena-ficticia-123"  # pragma: allowlist secret\nclave_real = "Zx9Kq2Lm8Rt4Vw7Hh"\n')
        ok, detalle = self.comprobar("secretos")
        self.assertFalse(ok)  # la marca solo cubre su propia línea
        self.assertIn("escrita en el código", detalle)

    def test_los_archivos_env_no_cuentan_pero_el_ejemplo_tampoco_marca(self):
        escribir(self.repo, ".env", "TOKEN=AKIAABCDEFGHIJKLMNOP\n")
        escribir(self.repo, ".env.example", "TOKEN=\n")
        self.assertTrue(self.comprobar("secretos")[0])

    def test_un_secreto_borrado_sigue_en_el_historial(self):
        git(self.repo, "init", "-q", "-b", "main")
        escribir(self.repo, "a.py", 'clave_secreta = "Zx9Kq2Lm8Rt4Vw7Hh"\n')
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "mala idea")
        escribir(self.repo, "a.py", "import os\nclave = os.environ['X']\n")
        git(self.repo, "commit", "-aq", "-m", "arreglo")
        ok, detalle = self.comprobar("secretos")
        self.assertFalse(ok)
        self.assertIn("historial", detalle)

    def test_env_fuera_de_git(self):
        self.assertFalse(self.comprobar("env_fuera_de_git")[0])  # sin .gitignore
        escribir(self.repo, ".gitignore", "node_modules/\n.env\n")
        self.assertTrue(self.comprobar("env_fuera_de_git")[0])
        git(self.repo, "init", "-q", "-b", "main")
        escribir(self.repo, ".env", "A=1\n")
        git(self.repo, "add", "-f", ".env")
        ok, detalle = self.comprobar("env_fuera_de_git")
        self.assertFalse(ok)
        self.assertIn(".env", detalle)

    def test_env_ejemplo_lockfile_readme(self):
        self.assertFalse(self.comprobar("env_ejemplo")[0])
        escribir(self.repo, ".env.example", "A=\n")
        self.assertTrue(self.comprobar("env_ejemplo")[0])
        self.assertFalse(self.comprobar("lockfile")[0])  # no hay manifiesto
        escribir(self.repo, "package.json", "{}")
        self.assertFalse(self.comprobar("lockfile")[0])
        escribir(self.repo, "package-lock.json", "{}")
        self.assertTrue(self.comprobar("lockfile")[0])
        escribir(self.repo, "README.md", "# Hola\nInstala y ejecuta. " + parrafo(130))
        self.assertTrue(self.comprobar("readme")[0])
        escribir(self.repo, "README.md", "# Hola\n" + parrafo(130))
        self.assertFalse(self.comprobar("readme")[0])  # no dice cómo ejecutar

    def test_requirements_con_versiones_exactas(self):
        escribir(self.repo, "requirements.txt", "flask\nrequests==2.0\n")
        self.assertFalse(self.comprobar("lockfile")[0])
        escribir(self.repo, "requirements.txt", "flask==3.0\nrequests==2.0\n")
        self.assertTrue(self.comprobar("lockfile")[0])

    def test_salud_archivos_grandes_pendientes_ci_migraciones(self):
        escribir(self.repo, "src/app.js", "app.get('/health', (r, s) => s.send('ok'));\n")
        self.assertTrue(self.comprobar("salud")[0])
        self.assertTrue(self.comprobar("archivos_grandes")[0])
        escribir(self.repo, "src/grande.js", "x\n" * 600)
        ok, detalle = self.comprobar("archivos_grandes")
        self.assertFalse(ok)
        self.assertIn("grande.js", detalle)
        escribir(self.repo, "src/p.js", "// TODO a\n// TODO b\n// FIXME c\n// TODO d\n// TODO e\n// TODO f\n")
        self.assertFalse(self.comprobar("pendientes_en_codigo")[0])
        self.assertFalse(self.comprobar("ci")[0])
        escribir(self.repo, ".github/workflows/ci.yml", "name: ci\n")
        self.assertTrue(self.comprobar("ci")[0])
        self.assertFalse(self.comprobar("migraciones")[0])
        escribir(self.repo, "prisma/migrations/001/migration.sql", "select 1;\n")
        self.assertTrue(self.comprobar("migraciones")[0])

    def test_las_carpetas_de_dependencias_no_cuentan(self):
        escribir(self.repo, "node_modules/x/gigante.js", "x\n" * 900)
        escribir(self.repo, "node_modules/x/secreto.js", 'const k = "AKIAABCDEFGHIJKLMNOP";\n')
        self.assertTrue(self.comprobar("archivos_grandes")[0])
        self.assertTrue(self.comprobar("secretos")[0])

    def test_pruebas_deben_alcanzar_a_los_casos_de_uso(self):
        self.llenar_plan()  # 3 casos
        self.assertFalse(self.comprobar("pruebas_existen")[0])  # sin archivos
        escribir(self.repo, "tests/test_a.py", "def test_uno():\n    assert 1\n\ndef test_dos():\n    assert 2\n")
        ok, detalle = self.comprobar("pruebas_existen")
        self.assertFalse(ok)
        self.assertIn("2 pruebas para 3 casos", detalle)
        escribir(self.repo, "tests/test_b.py", "def test_tres():\n    pass\n")
        ok, detalle = self.comprobar("pruebas_existen")
        self.assertFalse(ok)  # tres pruebas, pero una no comprueba nada
        self.assertIn("alguna prueba no comprueba nada", detalle)
        escribir(self.repo, "tests/test_b.py", "def test_tres():\n    assert 3\n")
        self.assertTrue(self.comprobar("pruebas_existen")[0])

    def test_casos_de_uso_exigen_tres_con_criterio(self):
        self.assertFalse(self.comprobar("casos")[0])  # plantilla con huecos
        self.doc("casos-de-uso.md", "## Caso 1: a\nDado x\n## Caso 2: b\nDado y\n")
        self.assertIn("mínimo es 3", self.comprobar("casos")[1])
        self.doc("casos-de-uso.md", "## Caso 1: a\nDado x\n## Caso 2: b\n## Caso 3: c\n")
        self.assertIn("criterios", self.comprobar("casos")[1])
        self.llenar_plan()
        self.assertTrue(self.comprobar("casos")[0])

    def test_investigacion_pide_fecha_fuentes_y_tres_opciones(self):
        self.assertFalse(self.comprobar("investigacion")[0])
        self.llenar_investigacion()
        self.assertTrue(self.comprobar("investigacion")[0])
        self.doc("investigacion.md", leer_archivo(os.path.join(self.repo, "docs/ingeniero/investigacion.md"))
                 .replace("https://b.example/2", "sin enlace").replace("### Opción C: tres", "### Otra: tres"))
        ok, detalle = self.comprobar("investigacion")
        self.assertFalse(ok)
        self.assertIn("3 enlaces", detalle)
        self.assertIn("opción C", detalle)

    def test_cada_hallazgo_declara_su_tipo_de_fuente_y_alguno_es_oficial(self):
        self.llenar_investigacion()
        ruta = os.path.join(self.repo, "docs/ingeniero/investigacion.md")
        original = leer_archivo(ruta)
        self.doc("investigacion.md", original.replace(" [fuente: secundaria]", ""))
        ok, detalle = self.comprobar("investigacion")
        self.assertFalse(ok)
        self.assertIn("tipo de fuente", detalle)
        self.doc("investigacion.md", original.replace("[fuente: oficial]", "[fuente: secundaria]"))
        ok, detalle = self.comprobar("investigacion")
        self.assertFalse(ok)
        self.assertIn("fuente oficial", detalle)
        self.doc("investigacion.md", original)
        self.assertTrue(self.comprobar("investigacion")[0])

    def test_comando_ejecuta_y_cuenta_solo_el_exito(self):
        self.est["comandos"]["pruebas"] = None
        self.assertIn("No hay comando", self.comprobar("comando", clave="pruebas")[1])
        self.est["comandos"]["pruebas"] = '"%s" -c "print(1)"' % sys.executable
        self.assertTrue(self.comprobar("comando", clave="pruebas")[0])
        self.est["comandos"]["pruebas"] = '"%s" -c "raise SystemExit(3)"' % sys.executable
        ok, detalle = self.comprobar("comando", clave="pruebas")
        self.assertFalse(ok)
        self.assertIn("código 3", detalle)
        self.est["comandos"]["pruebas"] = "comando-que-no-existe-xyz"
        self.assertIn("No se encontró", self.comprobar("comando", clave="pruebas")[1])


class TestControlesNuevos(Proyecto):
    def comprobar(self, tipo, **extra):
        return verificar.TIPOS[tipo](self.repo, self.est, dict(extra))

    def resumen(self, texto):
        self.doc("resumen-para-la-persona.md", texto)
        return self.comprobar("lenguaje_llano", doc="resumen-para-la-persona.md", min_palabras=20)

    def test_el_resumen_no_puede_llenarse_de_jerga_sin_explicar(self):
        base = "Vas a poder agendar tus citas desde el celular. " * 4
        ok, detalle = self.resumen(base + "Usaremos un endpoint y una API con un backend.\n")
        self.assertFalse(ok)
        self.assertIn("api", detalle)
        self.assertIn("endpoint", detalle)
        ok, _ = self.resumen(base + "Usaremos una API (la forma en que dos programas se hablan).\n")
        self.assertTrue(ok)

    def test_el_resumen_no_puede_tener_frases_enormes(self):
        ok, detalle = self.resumen(" ".join(["palabra"] * 60) + ".\n")
        self.assertFalse(ok)
        self.assertIn("frases son muy largas", detalle)

    def test_la_investigacion_vieja_se_avisa(self):
        self.llenar_investigacion()  # fecha 2026-11-24
        anterior = os.environ.get("INGENIERO_HOY")
        os.environ["INGENIERO_HOY"] = "2026-12-20"
        self.addCleanup(lambda: os.environ.__setitem__("INGENIERO_HOY", anterior) if anterior else os.environ.pop("INGENIERO_HOY", None))
        self.assertTrue(self.comprobar("investigacion_vigente", max_dias=60)[0])
        os.environ["INGENIERO_HOY"] = "2027-03-01"
        ok, detalle = self.comprobar("investigacion_vigente", max_dias=60)
        self.assertFalse(ok)
        self.assertIn("97 días", detalle)

    def test_cada_variable_de_entorno_tiene_que_estar_explicada(self):
        self.assertIn("Falta .env.example", self.comprobar("variables_documentadas", min_palabras=5)[1])
        escribir(self.repo, ".env.example", "SECRET_KEY=\nDATABASE_URL=\n")
        self.doc("entrega.md", "## Variables de entorno\nSECRET_KEY firma las sesiones y no se comparte con nadie jamás.\n")
        ok, detalle = self.comprobar("variables_documentadas", min_palabras=5)
        self.assertFalse(ok)
        self.assertIn("DATABASE_URL", detalle)
        self.doc("entrega.md", "## Variables de entorno\nSECRET_KEY firma las sesiones y no se comparte. DATABASE_URL dice dónde está la base.\n")
        self.assertTrue(self.comprobar("variables_documentadas", min_palabras=5)[0])

    def test_alguno_existe(self):
        self.assertFalse(self.comprobar("alguno_existe", opciones=["sitemap.xml", "robots.txt"])[0])
        escribir(self.repo, "public/robots.txt", "User-agent: *\n")
        self.assertTrue(self.comprobar("alguno_existe", opciones=["sitemap.xml", "public/robots.txt"])[0])


class TestReferencias(Proyecto):
    def test_la_prueba_citada_tiene_que_existir(self):
        escribir(self.repo, "tests/test_a.py", "def test_un_cliente_no_ve_lo_de_otro():\n    assert True\n")
        regla = {"tipo": "prueba", "min": 1}
        self.assertTrue(referencias._prueba(self.repo, "test_un_cliente_no_ve_lo_de_otro falla como debe", regla)[0])
        self.assertTrue(referencias._prueba(self.repo, "la prueba un cliente no ve lo de otro lo demuestra", regla)[0])
        ok, detalle = referencias._prueba(self.repo, "test_inventada_que_no_existe", regla)
        self.assertFalse(ok)
        self.assertIn("test_un_cliente_no_ve_lo_de_otro", detalle)  # sugiere una que sí existe
        self.assertTrue(referencias._prueba(self.repo, "está en tests/test_a.py", regla)[0])  # citar el archivo también vale

    def test_se_pueden_exigir_varias_pruebas(self):
        escribir(self.repo, "tests/test_a.py", "def test_primera_prueba():\n    assert 1\n\ndef test_segunda_prueba():\n    assert 2\n")
        regla = {"tipo": "prueba", "min": 2}
        self.assertFalse(referencias._prueba(self.repo, "test_primera_prueba", regla)[0])
        self.assertTrue(referencias._prueba(self.repo, "test_primera_prueba y test_segunda_prueba", regla)[0])

    def test_sin_pruebas_no_hay_nada_que_citar(self):
        ok, detalle = referencias._prueba(self.repo, "test_lo_que_sea", {"tipo": "prueba", "min": 1})
        self.assertFalse(ok)
        self.assertIn("no tiene pruebas", detalle)

    def test_el_archivo_citado_tiene_que_existir(self):
        escribir(self.repo, "scripts/respaldo.py", "x = 1\n")
        regla = {"tipo": "archivo", "min": 1}
        self.assertTrue(referencias._archivo(self.repo, "se hace con scripts/respaldo.py cada noche", regla)[0])
        self.assertFalse(referencias._archivo(self.repo, "se hace con scripts/no_existe.py", regla)[0])
        self.assertFalse(referencias._archivo(self.repo, "se hace todas las noches", regla)[0])

    def test_la_libreria_citada_tiene_que_estar_en_las_dependencias_o_en_el_codigo(self):
        regla = {"tipo": "dependencia", "opciones": ["argon2", "bcrypt", "scrypt"]}
        self.assertIn("nombrar la librería", referencias._dependencia(self.repo, "las guardo bien", regla)[1])
        self.assertIn("no aparece", referencias._dependencia(self.repo, "uso bcrypt", regla)[1])
        escribir(self.repo, "requirements.txt", "bcrypt==4.0.0\n")
        self.assertTrue(referencias._dependencia(self.repo, "uso bcrypt", regla)[0])
        escribir(self.repo, "app/seguridad.py", "import hashlib\nhashlib.scrypt(b'a', salt=b'b', n=2, r=1, p=1)\n")
        self.assertTrue(referencias._dependencia(self.repo, "uso hashlib.scrypt de la biblioteca estándar", regla)[0])

    def test_varias_reglas_deben_cumplirse_todas(self):
        escribir(self.repo, "requirements.txt", "bcrypt==4.0.0\n")
        escribir(self.repo, "tests/test_a.py", "def test_la_contrasena_no_queda_en_texto():\n    assert True\n")
        item = next(i for i in ck.cargar_items() if i["id"] == "S5")
        self.assertTrue(referencias.validar(self.repo, item, "bcrypt y test_la_contrasena_no_queda_en_texto")[0])
        self.assertFalse(referencias.validar(self.repo, item, "bcrypt")[0])  # falta la prueba
        self.assertFalse(referencias.validar(self.repo, item, "test_la_contrasena_no_queda_en_texto")[0])  # falta la librería


class TestChecklist(Proyecto):
    def test_aplica_segun_banderas_y_perfil(self):
        ids = lambda: {f["id"] for f in ck.evaluar(self.est)}  # noqa: E731
        self.assertNotIn("S4", ids())
        self.assertNotIn("O3", ids())
        self.assertIn("O1", ids())  # el perfil agenda tiene punto de salud
        flujo.declarar(self.est, {"multiusuario": True, "base-de-datos": True, "pagos": True})
        self.assertLessEqual({"S4", "O3", "O4", "S9", "A3", "A4"}, ids())
        flujo.declarar(self.est, perfil="sitio")
        self.assertNotIn("O1", ids())

    def test_sin_nada_hecho_no_esta_listo(self):
        p = ck.puntaje(self.est)
        self.assertEqual((p["puntaje"], p["veredicto"]), (0, "no_listo"))
        self.assertTrue(p["criticos_pendientes"])

    def _todo_comprobado(self, parte_declarada=0):
        """Marca todo como cumplido para probar las reglas del veredicto."""
        flujo.declarar(self.est, {b: True for b in e.BANDERAS})
        filas = ck.evaluar(self.est)
        for f in filas:
            if f["tipo"] == "auto":
                self.est["verificaciones"][f["id"]] = {"ok": True, "detalle": "ok", "fecha": "2026-11-24"}
            else:
                self.est["marcas"][f["id"]] = {"evidencia": "evidencia concreta de prueba", "fecha": "2026-11-24"}

    def test_las_reglas_del_veredicto(self):
        self._todo_comprobado()
        p = ck.puntaje(self.est)
        self.assertEqual(p["puntaje"], 100)
        self.assertEqual(p["veredicto"], "listo")  # con todas las banderas, lo comprobado pesa más que lo declarado
        # un crítico pendiente lo tumba aunque el puntaje sea alto
        self.est["marcas"].pop("O4")
        p = ck.puntaje(self.est)
        self.assertGreaterEqual(p["puntaje"], 90)
        self.assertEqual(p["veredicto"], "no_listo")
        self.assertEqual([c["id"] for c in p["criticos_pendientes"]], ["O4"])

    def test_si_lo_que_nadie_pudo_comprobar_pesa_mucho_queda_con_reservas(self):
        self._todo_comprobado()
        p = ck.puntaje(self.est)
        self.assertEqual((p["puntaje"], p["veredicto"]), (100, "listo"))
        # se descarta todo lo comprobable que no es crítico: queda casi solo lo declarado sin verificar
        for item in ck.cargar_items():
            if (item.get("auto") or item.get("valida")) and not item["critico"]:
                self.est["descartes"][item["id"]] = {"razon": "descartado para la prueba", "fecha": "2026-11-24"}
        for item in ck.cargar_items():  # y se vuelven libres los críticos verificables, que es lo que no pesa tanto
            if item["critico"] and item.get("valida"):
                self.est["verificaciones"].pop(item["id"], None)
        p = ck.puntaje(self.est)
        self.assertEqual(p["puntaje"], 100)
        self.assertGreater(p["declarado_sin_verificar"], 0)
        libres = p["declarado_sin_verificar"] / (p["comprobado_por_el_script"] + p["declarado_con_referencia_verificada"]
                                                 + p["declarado_sin_verificar"])
        self.assertEqual(p["veredicto"], "reservas" if libres > 0.25 else "listo")

    def test_la_evidencia_que_cita_algo_que_dejo_de_existir_vuelve_a_pendiente(self):
        escribir(self.repo, "tests/test_permisos.py", "def test_un_cliente_no_ve_lo_de_otro():\n    assert True\n")
        flujo.declarar(self.est, {"multiusuario": True})
        flujo.marcar(self.repo, self.est, "S4", "test_un_cliente_no_ve_lo_de_otro intenta ver lo ajeno y falla")
        self.assertEqual(next(f for f in ck.evaluar(self.est) if f["id"] == "S4")["estado"], "declarado_verificado")
        os.remove(os.path.join(self.repo, "tests", "test_permisos.py"))  # la prueba citada desaparece
        flujo.verificar(self.repo, self.est)
        fila = next(f for f in ck.evaluar(self.est) if f["id"] == "S4")
        self.assertEqual(fila["estado"], "pendiente")
        self.assertIn("ya no se encuentra", fila["detalle"])

    def test_puntaje_entre_70_y_89_es_con_reservas(self):
        self._todo_comprobado()
        for f in sorted(ck.evaluar(self.est), key=lambda f: f["peso"]):
            if ck.puntaje(self.est)["puntaje"] < 90:
                break
            if not f["critico"]:
                self.est["verificaciones"].pop(f["id"], None)
                self.est["marcas"].pop(f["id"], None)
        p = ck.puntaje(self.est)
        self.assertTrue(70 <= p["puntaje"] < 90, p["puntaje"])
        self.assertEqual(p["veredicto"], "reservas")

    def test_menos_de_70_no_esta_listo_aunque_no_haya_criticos_pendientes(self):
        self._todo_comprobado()
        for f in ck.evaluar(self.est):
            if not f["critico"]:
                self.est["verificaciones"].pop(f["id"], None)
                self.est["marcas"].pop(f["id"], None)
        p = ck.puntaje(self.est)
        self.assertFalse(p["criticos_pendientes"])
        self.assertLess(p["puntaje"], 70)
        self.assertEqual(p["veredicto"], "no_listo")

    def test_lo_descartado_sale_del_denominador_y_se_reporta(self):
        flujo.declarar(self.est, {"whatsapp": True})
        antes = ck.puntaje(self.est)["total_posible"]
        flujo.descartar(self.est, "S14", "No usamos WhatsApp en la primera versión de verdad")
        p = ck.puntaje(self.est)
        self.assertEqual(p["total_posible"], antes - 2)
        self.assertEqual(p["descartados"][0]["id"], "S14")

    def test_los_criticos_no_se_descartan(self):
        with self.assertRaises(SystemExit):
            flujo.descartar(self.est, "R2", "Porque no queremos escribir casos de uso nunca")
        with self.assertRaises(SystemExit):
            flujo.descartar(self.est, "S8", "no")  # sin razón

    def test_casi_todo_se_comprueba_con_el_proyecto_y_solo_unos_pocos_dependen_de_la_palabra(self):
        flujo.declarar(self.est, {b: True for b in e.BANDERAS})
        filas = ck.evaluar(self.est)
        total = sum(f["peso"] for f in filas)
        libres = sum(f["peso"] for f in filas if f["tipo"] == "libre")
        auto = sum(f["peso"] for f in filas if f["tipo"] == "auto")
        self.assertLessEqual(libres / total, 0.15)  # lo que nadie ni nada puede comprobar es una parte pequeña
        self.assertGreaterEqual(auto / total, 0.4)

    def test_los_items_de_perfil_solo_aplican_a_ese_perfil_y_exigen_las_dos_condiciones_si_hay_dos(self):
        ids = lambda: {f["id"] for f in ck.evaluar(self.est)}  # noqa: E731
        self.assertLessEqual({"AG1", "AG2"}, ids())  # el perfil de estas pruebas es agenda
        self.assertNotIn("T4", ids())
        flujo.declarar(self.est, {"pagos": True})
        self.assertNotIn("T4", ids())  # pagos solo no basta: tiene que ser una tienda
        flujo.declarar(self.est, perfil="tienda")
        self.assertIn("T4", ids())
        self.assertNotIn("AG1", ids())
        flujo.declarar(self.est, {"pagos": False})
        self.assertNotIn("T4", ids())  # una tienda sin pagos tampoco

class TestFlujo(Proyecto):
    def avanzar_hasta_resumen(self):
        self.llenar_brief()
        self.assertTrue(flujo.avanzar(self.repo, self.est, "investigacion")["avanzo"])
        self.llenar_investigacion()
        self.assertTrue(flujo.avanzar(self.repo, self.est, "eleccion")["avanzo"])
        flujo.elegir(self.est, "A", "me gusta la más simple")
        self.assertTrue(flujo.avanzar(self.repo, self.est, "plan")["avanzo"])
        self.llenar_plan()
        flujo.declarar(self.est, {"base-de-datos": True, "datos-personales": True})
        flujo.etapa_agregar(self.est, "Agendar una cita", [CRITERIO], [CMD_OK])
        flujo.etapa_contrato(self.est, 0, [CRITERIO + " en el esqueleto"], [CMD_OK])
        self.assertTrue(flujo.avanzar(self.repo, self.est, "resumen")["avanzo"])

    def test_no_se_avanza_con_documentos_incompletos_y_dice_que_falta(self):
        r = flujo.avanzar(self.repo, self.est, "investigacion")
        self.assertFalse(r["avanzo"])
        self.assertTrue(any(f.startswith("R1") for f in r["faltan"]))
        self.assertEqual(self.est["etapa"], "entrevista")

    def test_no_se_saltan_etapas_ni_se_vuelve_con_avanzar(self):
        with self.assertRaises(SystemExit):
            flujo.avanzar(self.repo, self.est, "plan")
        with self.assertRaises(SystemExit):
            flujo.avanzar(self.repo, self.est, "entrevista")

    def test_el_camino_completo_hasta_la_construccion(self):
        self.avanzar_hasta_resumen()
        # no hay construccion sin la aprobacion de la persona con sus palabras
        r = flujo.avanzar(self.repo, self.est, "aprobado", "sí, adelante")
        self.assertFalse(r["avanzo"])  # falta el resumen en lenguaje llano
        self.llenar_resumen()
        with self.assertRaises(SystemExit):
            flujo.avanzar(self.repo, self.est, "aprobado")  # sin evidencia
        self.assertTrue(flujo.avanzar(self.repo, self.est, "aprobado", "Sí, apruébalo, empiecen")["avanzo"])
        self.assertEqual(self.est["aprobacion"]["evidencia"], "Sí, apruébalo, empiecen")
        self.assertTrue(flujo.avanzar(self.repo, self.est, "construccion")["avanzo"])

    def test_la_eleccion_solo_se_guarda_en_su_etapa_y_con_razon(self):
        with self.assertRaises(SystemExit):
            flujo.elegir(self.est, "A", "porque sí quiero esa")
        self.llenar_brief()
        flujo.avanzar(self.repo, self.est, "investigacion")
        self.llenar_investigacion()
        flujo.avanzar(self.repo, self.est, "eleccion")
        with self.assertRaises(SystemExit):
            flujo.elegir(self.est, "A", "x")
        self.assertEqual(flujo.elegir(self.est, "B", "es más barata para mí")["opcion"], "B")

    def test_retroceder_obliga_a_aprobar_de_nuevo(self):
        self.avanzar_hasta_resumen()
        self.llenar_resumen()
        flujo.avanzar(self.repo, self.est, "aprobado", "sí, aprobado")
        flujo.avanzar(self.repo, self.est, "construccion")
        with self.assertRaises(SystemExit):
            flujo.retroceder(self.est, "plan", "x")
        r = flujo.retroceder(self.est, "plan", "la persona agregó el WhatsApp al alcance")
        self.assertEqual((r["etapa"], self.est["aprobacion"]), ("plan", None))
        self.assertIn("aprobarlo", r["aviso"])
        with self.assertRaises(SystemExit):
            flujo.retroceder(self.est, "plan", "otra razón válida distinta")  # ya está ahí

    def en_construccion(self):
        self.avanzar_hasta_resumen()
        self.llenar_resumen()
        flujo.avanzar(self.repo, self.est, "aprobado", "sí, aprobado")
        self.assertTrue(flujo.avanzar(self.repo, self.est, "construccion")["avanzo"])

    def test_una_etapa_se_cierra_solo_si_pasa_su_verificacion_y_en_orden(self):
        self.en_construccion()
        with self.assertRaises(SystemExit):
            flujo.etapa_cerrar(self.repo, self.est, 1)  # falta cerrar la 0
        flujo.etapa_contrato(self.est, 0, [CRITERIO + " en el esqueleto"], [CMD_MAL])
        r = flujo.etapa_cerrar(self.repo, self.est, 0)
        self.assertFalse(r["cerrada"])  # la verificación falla: no se cierra
        self.assertEqual(self.est["etapas"][0]["estado"], "pendiente")
        self.assertEqual(self.est["etapas"][0]["ultima_verificacion"]["ok"], False)
        flujo.etapa_contrato(self.est, 0, [CRITERIO + " en el esqueleto"], [CMD_OK])
        r = flujo.etapa_cerrar(self.repo, self.est, 0)
        self.assertTrue(r["cerrada"])
        self.assertIn("Verificación ejecutada", r["evidencia"])  # la evidencia la deja el script, no la narra nadie
        self.assertIn("git tag etapa-00-esqueleto", r["punto_de_retorno"])
        with self.assertRaises(SystemExit):
            flujo.etapa_cerrar(self.repo, self.est, 0)  # ya estaba cerrada
        self.assertTrue(flujo.etapa_cerrar(self.repo, self.est, 1, "agendar funciona")["cerrada"])
        self.assertTrue(verificar.TIPOS["etapas_cerradas"](self.repo, self.est, {})[0])

    def test_una_etapa_sin_comandos_exige_decir_por_que_y_dar_evidencia(self):
        self.en_construccion()
        flujo.etapa_contrato(self.est, 0, [CRITERIO + " en el esqueleto"], [], "se mira a mano")
        with self.assertRaises(SystemExit):
            flujo.etapa_cerrar(self.repo, self.est, 0, "listo")  # evidencia floja
        r = flujo.etapa_cerrar(self.repo, self.est, 0, "se abrió la pantalla y se vio la lista con tres citas de prueba")
        self.assertTrue(r["cerrada"])

    def test_una_etapa_cerrada_sin_verificacion_no_cuenta_para_el_checklist(self):
        self.en_construccion()
        for x in self.est["etapas"]:
            x["estado"] = "cerrada"  # cerradas "a mano": sin verificación que haya pasado
        ok, detalle = verificar.TIPOS["etapas_cerradas"](self.repo, self.est, {})
        self.assertFalse(ok)
        self.assertIn("sin una verificación", detalle)

    def test_un_item_del_checklist_puede_ser_la_verificacion_de_una_etapa(self):
        self.en_construccion()
        flujo.etapa_contrato(self.est, 0, [CRITERIO + " en el esqueleto"], ["item:P2"])
        self.est["comandos"]["pruebas"] = CMD_OK
        r = flujo.etapa_verificar(self.repo, self.est, 0)
        self.assertTrue(r["ok"])
        self.est["comandos"]["pruebas"] = CMD_MAL
        self.assertFalse(flujo.etapa_verificar(self.repo, self.est, 0)["ok"])

    def test_no_se_puede_ir_a_salida_con_etapas_abiertas(self):
        self.avanzar_hasta_resumen()
        self.llenar_resumen()
        flujo.avanzar(self.repo, self.est, "aprobado", "sí, aprobado")
        flujo.avanzar(self.repo, self.est, "construccion")
        r = flujo.avanzar(self.repo, self.est, "salida")
        self.assertFalse(r["avanzo"])
        self.assertTrue(any("Etapas abiertas" in f for f in r["faltan"]))

    def test_marcar_exige_evidencia_concreta_y_no_acepta_lo_automatico(self):
        for mala in ("ok", "listo", "sí", "bien hecho"):
            with self.assertRaises(SystemExit):
                flujo.marcar(self.repo, self.est, "A5", mala)
        with self.assertRaises(SystemExit):
            flujo.marcar(self.repo, self.est, "S1", "ya revisé que no hay secretos en el código")  # lo comprueba el script
        with self.assertRaises(SystemExit):
            flujo.marcar(self.repo, self.est, "ZZ9", "una evidencia cualquiera con palabras")
        with self.assertRaises(SystemExit):  # cita archivos que no existen
            flujo.marcar(self.repo, self.est, "a5", "módulos en src/modulos/citas.py y src/modulos/cobros.py con capas")
        escribir(self.repo, "src/modulos/citas.py", "x = 1\n")
        escribir(self.repo, "src/modulos/cobros.py", "y = 2\n")
        r = flujo.marcar(self.repo, self.est, "a5", "módulos en src/modulos/citas.py y src/modulos/cobros.py con capas")
        self.assertEqual(r["estado"], "declarado_verificado")
        fila = next(f for f in ck.evaluar(self.est) if f["id"] == "A5")
        self.assertEqual(fila["estado"], "declarado_verificado")

    def test_entregar_pide_la_evidencia_de_que_la_persona_decide(self):
        self.est["etapa"] = "salida"
        r = flujo.avanzar(self.repo, self.est, "entregado")
        self.assertFalse(r["avanzo"])
        self.assertTrue(any(f.startswith("E4") for f in r["faltan"]))

    def test_verificar_guarda_los_resultados_y_ver_el_estado_no_cambia_nada(self):
        self.llenar_brief()
        flujo.verificar(self.repo, self.est, {"R1", "R3"})
        self.assertTrue(self.est["verificaciones"]["R1"]["ok"])
        resumen = flujo.resumen_de_estado(self.repo, self.est)
        self.assertEqual(resumen["etapa"], "entrevista")
        self.assertIn("siguiente", resumen)

    def test_pendientes_ordena_lo_critico_primero(self):
        lista = flujo.pendientes(self.est)
        criticos = [f["critico"] for f in lista]
        self.assertEqual(criticos, sorted(criticos, reverse=True))
        self.assertTrue(lista[0]["critico"])


class TestPuertasNuevas(Proyecto):
    def test_una_duda_abierta_impide_avanzar_a_la_investigacion(self):
        self.llenar_brief()
        escribir(self.repo, "docs/ingeniero/brief.md", leer_archivo(os.path.join(self.repo, "docs/ingeniero/brief.md"))
                 + "\n- [DUDA: ¿los clientes necesitan cuenta o solo agendan con su nombre?]\n")
        r = flujo.avanzar(self.repo, self.est, "investigacion")
        self.assertFalse(r["avanzo"])
        self.assertTrue(any(f.startswith("R6") and "brief.md" in f for f in r["faltan"]))
        self.llenar_brief()  # la persona contestó: ya no hay marcador
        self.assertTrue(flujo.avanzar(self.repo, self.est, "investigacion")["avanzo"])

    def test_sin_premortem_no_se_pide_la_aprobacion(self):
        self.llenar_brief()
        flujo.avanzar(self.repo, self.est, "investigacion")
        self.llenar_investigacion()
        flujo.avanzar(self.repo, self.est, "eleccion")
        flujo.elegir(self.est, "A", "me gusta la más simple")
        flujo.avanzar(self.repo, self.est, "plan")
        self.llenar_plan()
        os.remove(os.path.join(self.repo, "docs/ingeniero/premortem.md"))
        flujo.etapa_agregar(self.est, "Agendar una cita", [CRITERIO], [CMD_OK])
        flujo.etapa_contrato(self.est, 0, [CRITERIO + " en el esqueleto"], [CMD_OK])
        flujo.declarar(self.est, {"base-de-datos": True, "datos-personales": True})
        r = flujo.avanzar(self.repo, self.est, "resumen")
        self.assertFalse(r["avanzo"])
        self.assertTrue(any(f.startswith("R7") for f in r["faltan"]))

    def test_el_premortem_pide_historia_riesgos_con_respuesta_y_los_ocho_angulos(self):
        comprobar = lambda: verificar.TIPOS["premortem"](self.repo, self.est, {})  # noqa: E731
        self.assertFalse(comprobar()[0])  # plantilla con huecos
        self.doc("premortem.md", premortem_completo())
        self.assertTrue(comprobar()[0])
        corto = premortem_completo().replace(" ".join(["palabra"] * 40), "se cae")
        self.doc("premortem.md", corto)
        self.assertIn("30 palabras", comprobar()[1])
        sin_respuesta = premortem_completo().replace("- Qué haremos: una medida concreta para evitarlo", "- Qué haremos: nada", 1)
        self.doc("premortem.md", sin_respuesta)
        self.assertIn("al menos 3 riesgos", comprobar()[1])
        pocos = premortem_completo().replace("- Ángulo 8: respuesta concreta sobre este punto\n", "")
        self.doc("premortem.md", pocos)
        self.assertIn("7 de 8", comprobar()[1])

    def test_no_se_construye_si_a_alguna_etapa_le_falta_su_contrato(self):
        self.avanzar_hasta_resumen()
        self.llenar_resumen()
        flujo.avanzar(self.repo, self.est, "aprobado", "sí, aprobado")
        self.est["etapas"][1]["verificar"] = []
        self.est["etapas"][1]["sin_verificacion"] = None
        r = flujo.avanzar(self.repo, self.est, "construccion")
        self.assertFalse(r["avanzo"])
        self.assertTrue(any("contrato" in f for f in r["faltan"]))

    def avanzar_hasta_resumen(self):
        self.llenar_brief()
        flujo.avanzar(self.repo, self.est, "investigacion")
        self.llenar_investigacion()
        flujo.avanzar(self.repo, self.est, "eleccion")
        flujo.elegir(self.est, "A", "me gusta la más simple")
        flujo.avanzar(self.repo, self.est, "plan")
        self.llenar_plan()
        flujo.declarar(self.est, {"base-de-datos": True, "datos-personales": True})
        flujo.etapa_agregar(self.est, "Agendar una cita", [CRITERIO], [CMD_OK])
        flujo.etapa_contrato(self.est, 0, [CRITERIO + " en el esqueleto"], [CMD_OK])
        self.assertTrue(flujo.avanzar(self.repo, self.est, "resumen")["avanzo"])


class TestContratosYCriterios(Proyecto):
    def test_los_criterios_no_pueden_ser_frases_vagas(self):
        for vaga in ("La pantalla funciona bien", "El sistema se ve profesional y todo bien", "Debería funcionar correctamente"):
            with self.assertRaises(SystemExit):
                flujo.etapa_contrato(self.est, 0, [vaga + " para el cliente"], [CMD_OK])
        with self.assertRaises(SystemExit):
            flujo.etapa_contrato(self.est, 0, ["Funciona"], [CMD_OK])  # demasiado corto
        flujo.etapa_contrato(self.est, 0, ["El cliente recibe un 409 si la hora ya está ocupada"], [CMD_OK])

    def test_un_item_que_no_se_comprueba_solo_no_sirve_como_verificacion(self):
        with self.assertRaises(SystemExit):
            flujo.etapa_contrato(self.est, 0, [CRITERIO + " en el esqueleto"], ["item:A5"])  # A5 es manual
        with self.assertRaises(SystemExit):
            flujo.etapa_contrato(self.est, 0, [CRITERIO + " en el esqueleto"], ["item:NOEXISTE"])
        flujo.etapa_contrato(self.est, 0, [CRITERIO + " en el esqueleto"], ["item:S1", "item:p2"])

    def test_cambiar_el_contrato_invalida_la_verificacion_anterior(self):
        self.est["comandos"]["pruebas"] = CMD_OK
        flujo.etapa_verificar(self.repo, self.est, 0)
        self.assertIsNotNone(self.est["etapas"][0]["ultima_verificacion"])
        flujo.etapa_contrato(self.est, 0, [CRITERIO + " de otra manera"], [CMD_OK])
        self.assertIsNone(self.est["etapas"][0]["ultima_verificacion"])

    def test_los_criterios_de_los_casos_de_uso_tampoco_pueden_ser_vagos_ni_estar_mal_formados(self):
        casos = lambda c: "".join("## Caso %d: x\n- Criterio de aceptación:\n  - %s\n- Prueba que lo cubre: tests/a.py\n" % (n, c)  # noqa: E731
                                  for n in (1, 2, 3))
        comprobar = lambda: verificar.TIPOS["casos"](self.repo, self.est, {})  # noqa: E731
        self.doc("casos-de-uso.md", casos("Dado un cliente, cuando agenda, entonces la cita funciona correctamente."))
        ok, detalle = comprobar()
        self.assertFalse(ok)
        self.assertIn("funciona correctamente", detalle)
        self.doc("casos-de-uso.md", casos("Dado un cliente, la cita queda confirmada."))
        self.assertIn("Dado... cuando... entonces", comprobar()[1])
        self.doc("casos-de-uso.md", casos("Dado un cliente, cuando agenda, entonces recibe una cita con estado confirmada."))
        self.assertTrue(comprobar()[0])

    def test_cada_caso_de_uso_tiene_que_apuntar_a_una_prueba_que_existe(self):
        comprobar = lambda: verificar.TIPOS["trazabilidad"](self.repo, self.est, {})  # noqa: E731
        self.assertFalse(comprobar()[0])  # la plantilla sin llenar no cuenta
        self.doc("casos-de-uso.md", "## Caso 1: a\n- Prueba que lo cubre: tests/test_cancelar_cita.py\n"
                                    "## Caso 2: b\n- Prueba que lo cubre: test_agenda_del_dia\n")
        ok, detalle = comprobar()
        self.assertFalse(ok)
        self.assertIn("tests/test_cancelar_cita.py", detalle)
        escribir(self.repo, "tests/test_gestion.py", "def test_agenda_del_dia():\n    assert 1\n")
        self.doc("casos-de-uso.md", "## Caso 1: a\n- Prueba que lo cubre: tests/test_gestion.py\n"
                                    "## Caso 2: b\n- Prueba que lo cubre: test_agenda_del_dia\n")
        self.assertTrue(comprobar()[0])


class TestSiguienteYTraspaso(Proyecto):
    def preparar(self):
        self.avanzar_hasta_resumen = lambda: TestFlujo.avanzar_hasta_resumen(self)
        TestFlujo.en_construccion(self)  # reutiliza el camino hasta la construcción
        self.est["comandos"]["pruebas"] = CMD_OK

    def test_siguiente_muestra_la_etapa_con_su_contrato_y_la_deja_en_curso(self):
        self.preparar()
        r = flujo.siguiente(self.repo, self.est)
        self.assertEqual((r["reanudando"], r["etapa"]["id"], r["iniciada"]), (False, 0, False))
        self.assertEqual(r["etapa"]["verificar"], [CMD_OK])
        self.assertEqual(self.est["etapas"][0]["estado"], "pendiente")
        flujo.siguiente(self.repo, self.est, iniciar=True)
        self.assertEqual(self.est["etapas"][0]["estado"], "en_curso")

    def test_si_la_sesion_se_corto_siguiente_retoma_la_etapa_y_comprueba_como_quedo(self):
        self.preparar()
        flujo.siguiente(self.repo, self.est, iniciar=True)  # una sesión empieza la etapa 0 y se corta
        r = flujo.siguiente(self.repo, self.est)
        self.assertTrue(r["reanudando"])
        self.assertEqual(r["etapa"]["id"], 0)
        self.assertTrue(r["verificacion_ahora"]["ok"])
        self.assertIn("quedó a medias", r["mensaje"])
        self.assertTrue(flujo.etapa_cerrar(self.repo, self.est, 0)["cerrada"])  # una etapa en curso se puede cerrar
        self.assertEqual(flujo.siguiente(self.repo, self.est)["etapa"]["id"], 1)

    def test_sin_etapas_abiertas_o_fuera_de_la_construccion_lo_dice(self):
        self.assertIn("construcción", flujo.siguiente(self.repo, self.est)["mensaje"])
        self.preparar()
        for x in self.est["etapas"]:
            x["estado"] = "cerrada"
        self.assertIn("No quedan etapas abiertas", flujo.siguiente(self.repo, self.est)["mensaje"])

    def test_el_traspaso_es_autosuficiente_para_otra_instancia(self):
        self.preparar()
        self.doc("brief.md", leer_archivo(os.path.join(self.repo, "docs/ingeniero/brief.md")))
        texto = flujo.traspaso_texto(self.repo, self.est)
        for esperado in ("# Traspaso: Barbería de prueba", "Reglas que no se negocian", "Pruebas primero", "Fuera de alcance",
                         "Pila elegida", "Opción A", "### Etapa 0: Esqueleto", "### Etapa 1: Agendar una cita", CRITERIO,
                         "**Cómo se verifica:**", "pragma: allowlist secret", "siguiente --iniciar", "etapa-cerrar",
                         "revisión independiente", "pruebas: `"):
            self.assertIn(esperado, texto)
        self.assertNotIn("[[", texto)  # no deja huecos de plantilla
        self.assertIn("No se despliega, no se compra", texto.replace("no se despliega", "No se despliega"))


class TestProyectoExistente(Proyecto):
    def proyecto(self):
        repo = tempfile.mkdtemp(prefix="ing-")
        self.addCleanup(lambda: shutil.rmtree(repo, onerror=_borrar))
        escribir(repo, "package.json", json.dumps({"scripts": {"test": "jest", "build": "vite build"},
                                                   "dependencies": {"react": "19", "stripe": "1", "prisma": "5", "next-auth": "4"}}))
        escribir(repo, "src/app.test.js", "test('x', () => { expect(1).toBe(1); });\n")
        escribir(repo, "src/app.js", "export const a = 1;\n")
        return repo

    def test_detectar_lee_el_proyecto_y_propone_sin_ejecutar_nada(self):
        from ingeniero_lib import existente
        r = existente.detectar_proyecto(self.proyecto())
        self.assertEqual(r["perfil_sugerido"], "tienda")  # interfaz y pagos
        self.assertLessEqual({"pagos", "cuentas", "base-de-datos", "interfaz", "datos-personales", "multiusuario"},
                             set(r["banderas_sugeridas"]))
        self.assertEqual(r["comandos_sugeridos"]["pruebas"], "npm test")
        self.assertEqual(r["comandos_sugeridos"]["build"], "npm run build")
        self.assertEqual(r["mapa"]["archivos_de_prueba"], 1)
        self.assertFalse(r["mapa"]["usa_git"])

    def test_iniciar_existente_salta_la_entrevista_y_deja_las_sugerencias_aplicadas(self):
        repo = self.proyecto()
        r = plantillas.iniciar(repo, "Mi tienda", "otro", existente=True)
        est = e.cargar(repo)
        self.assertEqual((r["modo"], est["modo"], est["etapa"], est["perfil"]), ("existente", "existente", "construccion", "tienda"))
        self.assertTrue(est["banderas"]["pagos"] and est["banderas"]["interfaz"])
        self.assertEqual(est["comandos"]["pruebas"], "npm test")
        self.assertIsNone(est["aprobacion"])  # no se inventa una aprobación que nadie dio
        self.assertIsNone(est["eleccion"])
        self.assertIn("lo_que_se_leyo", r)

    def test_el_rescate_ordena_lo_grave_primero_y_se_puede_volver_etapas_con_verificacion(self):
        from ingeniero_lib import existente
        repo = self.proyecto()
        plantillas.iniciar(repo, "Mi tienda", "otro", existente=True)
        est = e.cargar(repo)
        r = existente.rescate(repo, est)
        self.assertGreater(len(r["plan"]), 3)
        criticos = [p["criticos"] for p in r["plan"]]
        self.assertEqual(criticos, sorted(criticos, reverse=True))  # lo más grave, primero
        self.assertEqual(r["etapas_creadas"], [])
        existente.rescate(repo, est, crear_etapas=True)
        self.assertEqual(len(est["etapas"]), len(r["plan"]))
        for etapa in est["etapas"]:
            self.assertTrue(etapa["hecho_cuando"])
            self.assertTrue(etapa["verificar"] or etapa["sin_verificacion"])  # cada etapa de rescate trae su verificación
            for cmd in etapa["verificar"]:
                self.assertTrue(cmd.startswith("item:"))

    def test_el_rescate_solo_crea_etapas_en_la_construccion(self):
        from ingeniero_lib import existente
        with self.assertRaises(SystemExit):
            existente.rescate(self.repo, self.est, crear_etapas=True)  # un proyecto nuevo en entrevista

    def test_detectar_reconoce_un_bot_y_un_proyecto_python(self):
        from ingeniero_lib import existente
        repo = tempfile.mkdtemp(prefix="ing-")
        self.addCleanup(lambda: shutil.rmtree(repo, onerror=_borrar))
        escribir(repo, "requirements.txt", "fastapi==0.1\nopenai==1.0\npytest==8\nruff==0.1\n")
        escribir(repo, "app/main.py", "x = 1\n")
        r = existente.detectar_proyecto(repo)
        self.assertEqual(r["perfil_sugerido"], "bot")
        self.assertEqual(r["comandos_sugeridos"]["pruebas"], "python -m pytest -q")
        self.assertEqual(r["comandos_sugeridos"]["lint"], "python -m ruff check .")


class TestGuiasConFecha(Proyecto):
    def test_las_guias_viejas_se_avisan_y_las_recientes_no(self):
        anterior = os.environ.get("INGENIERO_HOY")
        self.addCleanup(lambda: os.environ.__setitem__("INGENIERO_HOY", anterior) if anterior else os.environ.pop("INGENIERO_HOY", None))
        os.environ["INGENIERO_HOY"] = "2026-12-01"
        self.assertEqual(flujo.guias_sin_revisar(), [])
        os.environ["INGENIERO_HOY"] = "2027-06-01"
        vencidas = flujo.guias_sin_revisar()
        self.assertTrue(vencidas)
        self.assertTrue(all(v["dias"] > 120 for v in vencidas))
        self.assertIn("guias_sin_revisar", flujo.resumen_de_estado(self.repo, self.est))


class TestTendenciaEInforme(Proyecto):
    def test_sin_dos_verificaciones_no_hay_con_que_comparar(self):
        self.assertEqual(flujo.tendencia(self.est)["veredicto"], "sin_historia")
        flujo.verificar(self.repo, self.est)
        self.assertEqual(len(self.est["puntajes"]), 1)
        self.assertEqual(flujo.tendencia(self.est)["veredicto"], "sin_historia")

    def test_una_verificacion_sin_cambios_no_llena_el_historial(self):
        flujo.verificar(self.repo, self.est)
        flujo.verificar(self.repo, self.est)
        self.assertEqual(len(self.est["puntajes"]), 1)

    def test_la_tendencia_avisa_si_algo_empeora_y_si_mejora(self):
        self.llenar_brief()
        flujo.verificar(self.repo, self.est)
        escribir(self.repo, ".gitignore", ".env\n")
        flujo.verificar(self.repo, self.est)
        self.assertEqual(flujo.tendencia(self.est)["veredicto"], "mejoro")
        os.remove(os.path.join(self.repo, ".gitignore"))  # alguien borra algo que ya estaba en orden
        flujo.verificar(self.repo, self.est)
        r = flujo.tendencia(self.est)
        self.assertEqual(r["veredicto"], "empeoro")
        self.assertLess(r["cambio_de_puntaje"], 0)
        self.assertIn("empeoró", r["mensaje"])

    def test_la_verificacion_parcial_no_cuenta_para_el_historial(self):
        flujo.verificar(self.repo, self.est, {"R1"})
        self.assertNotIn("puntajes", self.est)

    def test_el_informe_habla_en_lenguaje_llano_y_sin_codigos(self):
        texto = flujo.informe(self.est)
        self.assertIn("# Cómo va Barbería de prueba", texto)
        self.assertIn("Estamos conversando", texto)
        self.assertIn("Lo más importante que falta", texto)
        self.assertIn("Nosotros no lo publicamos", texto)
        self.assertNotRegex(texto, r"\b[A-Z]{1,3}\d{1,2}\b")  # sin códigos de ítem como R1 o S4
        for palabra in ("endpoint", "backend", "framework", "json"):
            self.assertNotIn(palabra, texto.lower())

    def test_el_informe_cambia_cuando_avanza_el_proyecto(self):
        self.llenar_brief()
        self.assertTrue(flujo.avanzar(self.repo, self.est, "investigacion")["avanzo"])
        self.assertIn("investigando", flujo.informe(self.est))


class TestDeclarar(Proyecto):
    def test_banderas_y_comandos_validos(self):
        flujo.declarar(self.est, {"pagos": True})
        self.assertTrue(self.est["banderas"]["pagos"])
        with self.assertRaises(SystemExit):
            flujo.declarar(self.est, {"inventada": True})
        flujo.comandos(self.est, {"pruebas": "npm test"})
        self.assertEqual(self.est["comandos"]["pruebas"], "npm test")
        with self.assertRaises(SystemExit):
            flujo.comandos(self.est, {"inventado": "x"})


class TestSkillsPropias(Proyecto):
    def test_distingue_instaladas_de_faltantes_y_no_instala_nada(self):
        carpeta = tempfile.mkdtemp(prefix="ing-skills-")
        self.addCleanup(lambda: shutil.rmtree(carpeta, onerror=_borrar))
        escribir(carpeta, "arquitectura-backend/SKILL.md", "---\nname: arquitectura-backend\n---\n")
        antes = sorted(os.listdir(carpeta))
        with mock.patch.object(skills_propias, "carpetas_de_skills", lambda repo: [carpeta]):  # sin mirar las del usuario
            r = skills_propias.revisar(self.repo)
        self.assertEqual([s["nombre"] for s in r["instaladas"]], ["arquitectura-backend"])
        faltan = {s["nombre"]: s["enlace"] for s in r["faltan"]}
        self.assertIn("documentacion-viva", faltan)
        self.assertEqual(faltan["qa"], "https://github.com/nanoizax/skill-qa")
        self.assertEqual(sorted(os.listdir(carpeta)), antes)  # no se instaló nada

    def test_encuentra_las_skills_en_cualquier_carpeta_oculta_sin_nombrar_ninguna_herramienta(self):
        casa = tempfile.mkdtemp(prefix="ing-casa-")
        self.addCleanup(lambda: shutil.rmtree(casa, onerror=_borrar))
        escribir(casa, ".una-herramienta/skills/qa/SKILL.md", "---\nname: qa\n---\n")
        escribir(casa, ".otra/sin-skills/x.txt", "x")
        escribir(self.repo, ".local/skills/repaso-tecnico/SKILL.md", "---\nname: repaso-tecnico\n---\n")
        with mock.patch.dict(os.environ, {"HOME": casa, "USERPROFILE": casa}):
            carpetas = skills_propias.carpetas_de_skills(self.repo)
            r = skills_propias.revisar(self.repo)
        self.assertTrue(any(c.endswith(os.path.join(".una-herramienta", "skills")) for c in carpetas))
        self.assertFalse(any(".otra" in c for c in carpetas))
        self.assertLessEqual({"qa", "repaso-tecnico"}, {s["nombre"] for s in r["instaladas"]})

    def test_tambien_mira_las_carpetas_que_indica_la_variable_de_entorno(self):
        carpeta = tempfile.mkdtemp(prefix="ing-skills-")
        self.addCleanup(lambda: shutil.rmtree(carpeta, onerror=_borrar))
        with mock.patch.dict(os.environ, {"INGENIERO_SKILLS_DIRS": carpeta}):
            self.assertEqual(skills_propias.carpetas_de_skills(self.repo)[0], carpeta)


class TestCoherenciaDeLosDatos(unittest.TestCase):
    """El checklist, las plantillas y las guías tienen que hablar de lo mismo."""

    def setUp(self):
        self.items = ck.cargar_items()

    def test_ids_unicos_y_campos_validos(self):
        ids = [i["id"] for i in self.items]
        self.assertEqual(len(ids), len(set(ids)))
        for i in self.items:
            self.assertIn(i["etapa"], e.ETAPAS, i["id"])
            self.assertIn(i["peso"], (1, 2, 3), i["id"])
            self.assertTrue(bool(i.get("auto")) != bool(i.get("evidencia")), "%s: o es automático o pide evidencia" % i["id"])
            if i.get("valida"):
                self.assertFalse(i.get("auto"), "%s: una comprobación automática no necesita validar evidencia" % i["id"])
                reglas = i["valida"] if isinstance(i["valida"], list) else [i["valida"]]
                for r in reglas:
                    self.assertIn(r["tipo"], referencias.TIPOS, i["id"])
            cuando = i["cuando"]
            if isinstance(cuando, dict):
                for b in cuando.get("banderas", []):
                    self.assertIn(b, e.BANDERAS, i["id"])
                for p in cuando.get("perfiles", []):
                    self.assertIn(p, e.PERFILES, i["id"])
            if i.get("auto"):
                self.assertIn(i["auto"]["tipo"], verificar.TIPOS, i["id"])
                if i["auto"]["tipo"] == "comando":
                    self.assertIn(i["auto"]["clave"], e.COMANDOS, i["id"])

    def test_cada_documento_y_seccion_que_pide_el_checklist_existe_en_las_plantillas(self):
        for i in self.items:
            a = i.get("auto") or {}
            if "doc" not in a:
                continue
            ruta = os.path.join(RAIZ, "plantilla", a["doc"])
            self.assertTrue(os.path.isfile(ruta), "%s: falta la plantilla %s" % (i["id"], a["doc"]))
            if "encabezado" in a:
                with open(ruta, encoding="utf-8") as f:
                    self.assertIsNotNone(seccion(f.read(), a["encabezado"]), "%s: la plantilla %s no tiene \"%s\"" % (
                        i["id"], a["doc"], a["encabezado"]))

    def test_las_plantillas_completas_no_cumplen_nada_solas(self):
        """Una plantilla recién copiada no puede dar puntos: todos sus documentos tienen huecos."""
        repo = tempfile.mkdtemp(prefix="ing-")
        self.addCleanup(lambda: shutil.rmtree(repo, onerror=_borrar))
        plantillas.iniciar(repo, "X", "otro")
        est = e.cargar(repo)
        docs = {i["auto"]["doc"] for i in self.items if i.get("auto") and "doc" in i["auto"]}
        for d in docs:
            ok, _ = verificar.TIPOS[next(i["auto"]["tipo"] for i in self.items if i.get("auto", {}).get("doc") == d)](
                repo, est, next(i["auto"] for i in self.items if i.get("auto", {}).get("doc") == d))
            self.assertFalse(ok, d)

    def test_la_skill_nombra_todas_las_ordenes_del_script_y_las_etapas(self):
        with open(os.path.join(RAIZ, "SKILL.md"), encoding="utf-8") as f:
            skill = f.read()
        for orden in ("iniciar", "estado", "datos", "comandos", "avanzar", "retroceder", "elegir", "etapa-agregar", "etapa-cerrar",
                      "verificar", "marcar", "descartar", "pendientes", "puntaje", "tendencia", "informe", "skills",
                      "etapa-contrato", "etapa-verificar", "siguiente", "traspaso", "detectar", "rescate"):
            self.assertIn("`" + orden, skill, orden)
        for etapa in ("Entrevista", "Investigación", "Elección", "Plan", "Resumen y aprobación", "Construcción", "Salida", "Entrega"):
            self.assertIn(etapa, skill)

    def test_la_guia_de_nuestras_skills_coincide_con_los_datos(self):
        with open(os.path.join(RAIZ, "datos", "skills-propias.json"), encoding="utf-8") as f:
            datos = json.load(f)
        with open(os.path.join(RAIZ, "references", "nuestras-skills.md"), encoding="utf-8") as f:
            guia = f.read()
        for s in datos["skills"]:
            self.assertIn("`%s`" % s["nombre"], guia, s["nombre"])
            self.assertIn(s["repo"], guia, s["repo"])

    def test_las_guias_referenciadas_existen(self):
        with open(os.path.join(RAIZ, "SKILL.md"), encoding="utf-8") as f:
            skill = f.read()
        for ruta in set(re.findall(r"`((?:references|plantilla)/[\w./-]+)`", skill)):
            self.assertTrue(os.path.exists(os.path.join(RAIZ, ruta.rstrip("/"))), ruta)


class TestLineaDeComandos(unittest.TestCase):
    def correr(self, repo, *args, esperado=0):
        r = subprocess.run(CLI + ["--repo", repo] + list(args), capture_output=True, text=True, encoding="utf-8",
                           errors="replace")
        self.assertEqual(r.returncode, esperado, r.stderr)
        return json.loads(r.stdout) if esperado == 0 else r.stderr

    def test_un_recorrido_corto_por_la_linea_de_comandos(self):
        repo = tempfile.mkdtemp(prefix="ing-")
        self.addCleanup(lambda: shutil.rmtree(repo, onerror=_borrar))
        self.assertIn("No hay un proyecto", self.correr(repo, "estado", esperado=1))
        r = self.correr(repo, "iniciar", "--nombre", "Barbería", "--perfil", "agenda")
        self.assertEqual(r["etapa"], "entrevista")
        self.correr(repo, "datos", "--pagos", "si", "--datos-personales", "sí", "--cuentas", "no")
        estado = self.correr(repo, "estado")
        self.assertEqual(sorted(estado["banderas_activas"]), ["datos-personales", "pagos"])
        self.assertFalse(self.correr(repo, "avanzar", "investigacion")["avanzo"])
        self.assertEqual(self.correr(repo, "puntaje")["veredicto"], "no_listo")
        self.assertEqual(self.correr(repo, "pendientes")[0]["critico"], True)
        self.assertIn("Responde 'si' o 'no'", self.correr(repo, "datos", "--pagos", "quizás", esperado=1))
        self.assertIn("No se instaló nada", self.correr(repo, "skills")["nota"])

    def test_exigir_un_minimo_termina_con_codigo_2_si_no_se_alcanza(self):
        repo = tempfile.mkdtemp(prefix="ing-")
        self.addCleanup(lambda: shutil.rmtree(repo, onerror=_borrar))
        self.correr(repo, "iniciar", "--nombre", "X", "--perfil", "otro")
        r = subprocess.run(CLI + ["--repo", repo, "puntaje", "--exigir", "80"], capture_output=True, text=True, encoding="utf-8",
                           errors="replace")
        self.assertEqual(r.returncode, 2)
        self.assertEqual(json.loads(r.stdout)["veredicto"], "no_listo")  # igual imprime el resultado
        self.assertEqual(subprocess.run(CLI + ["--repo", repo, "puntaje", "--exigir", "0"], capture_output=True).returncode, 2)  # crítico pendiente
        self.assertEqual(subprocess.run(CLI + ["--repo", repo, "puntaje"], capture_output=True).returncode, 0)  # sin exigir no falla

    def test_tendencia_e_informe_por_la_linea_de_comandos(self):
        repo = tempfile.mkdtemp(prefix="ing-")
        self.addCleanup(lambda: shutil.rmtree(repo, onerror=_borrar))
        self.correr(repo, "iniciar", "--nombre", "Mi tienda", "--perfil", "tienda")
        self.assertEqual(self.correr(repo, "tendencia")["veredicto"], "sin_historia")
        r = self.correr(repo, "informe", "--guardar")
        self.assertIn("# Cómo va Mi tienda", r["informe"])
        self.assertTrue(os.path.isfile(os.path.join(repo, r["guardado_en"])))

    def test_estado_y_puntaje_no_modifican_el_proyecto(self):
        repo = tempfile.mkdtemp(prefix="ing-")
        self.addCleanup(lambda: shutil.rmtree(repo, onerror=_borrar))
        self.correr(repo, "iniciar", "--nombre", "X", "--perfil", "otro")
        ruta = os.path.join(repo, "docs", "ingeniero", "estado.json")
        antes = leer_archivo(ruta)
        self.correr(repo, "estado")
        self.correr(repo, "puntaje")
        self.correr(repo, "pendientes")
        self.assertEqual(leer_archivo(ruta), antes)


if __name__ == "__main__":
    unittest.main(verbosity=2)
