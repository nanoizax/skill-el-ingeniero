# skill-el-ingeniero

**Una idea de producto entra, un proyecto bien construido sale. Primero pregunta, luego planifica, luego construye por etapas y al final te dice con puntaje y evidencia si está listo para enviar. No publica nada: eso lo decides tú.**

Una skill para tu herramienta de desarrollo, con un script que guarda en qué etapa va el proyecto, comprueba lo que se puede comprobar (secretos en el código, pruebas, documentos completos, respaldos) y calcula el puntaje del checklist (con 93 pruebas propias).

---

## En resumen

Cuando le pides a tu herramienta "hazme una página", "hazme un sistema" o "hazme un agente", esta skill se pone en medio y hace de ingeniero:

- **Te entrevista** con preguntas sencillas, de a una, con opciones y una recomendación, hasta escribir un brief que reconozcas como tuyo.
- **Investiga lo vigente** (versiones, costos, normativa, proyectos parecidos) con fecha y enlace, y anota como "no verificado" lo que no pudo confirmar.
- **Te propone tres opciones de tecnología** y eliges tú. Una de las tres puede ser "no construir nada" si ya existe una solución hecha.
- **Escribe el plan completo:** casos de uso, arquitectura, base de datos, pruebas y seguridad. Y te lo explica en lenguaje llano antes de tocar código.
- **Construye por etapas**, cada una con sus casos de uso y sus pruebas escritas antes que el código. Cada etapa tiene un **contrato**: qué debe ser cierto al terminar y qué comando lo demuestra. El script la cierra solo si ese comando pasa, y si la sesión se corta, retoma donde quedó.
- **Se pregunta qué podría salir mal** antes de pedirte la aprobación (un pre-mortem de ocho ángulos), y no avanza mientras haya dudas abiertas en el brief.
- **Sirve también para un proyecto que ya existe:** lo lee en vez de entrevistarte, te dice dónde está parado y arma un plan de rescate ordenado de lo más grave a lo menos grave.
- **Deja un traspaso** que otra instancia, sin ningún contexto, puede usar para construir o continuar el proyecto.
- **Cierra con un checklist** de 85 puntos con puntaje y evidencia, y un veredicto: no está listo, listo con reservas o listo para enviar.
- **No despliega, no compra y no crea cuentas.** El producto queda listo para enviar y recibes una guía para que lo publiques cuando quieras y como quieras.

No promete cero errores. Promete un proyecto mucho más sólido que el que sale de pedirlo sin más, y te dice con honestidad qué quedó sin comprobar.

## Para qué fue creada

Esta skill fue creada **para la comunidad**, pensando sobre todo en quien no es programador y construye con una herramienta de inteligencia artificial. La herramienta hace lo que le pides, como sea: sin estructura, sin pruebas, sin plan. El producto sale, y a la vez se vuelve frágil. Explota en producción: se pierden datos, se filtran claves, nadie sabe cómo restaurar un respaldo que nunca se probó.

Un ingeniero con experiencia evita eso casi sin pensarlo, porque ya se quemó antes. Esta skill pone ese criterio por escrito y lo vuelve un proceso con puertas que no se pueden saltar.

## El problema que resuelve

- Se construye antes de entender qué se necesita.
- No hay casos de uso ni pruebas, así que nadie sabe si funciona.
- La tecnología se elige por lo que la herramienta recuerda, no por lo vigente hoy.
- Las claves terminan escritas en el código y subidas a Git.
- No hay respaldo, o hay uno que vive en la misma máquina que los datos.
- Nadie dejó por escrito qué se decidió y por qué, así que mañana nadie retoma el proyecto.
- Se dice "listo" sin ninguna evidencia.

## Las etapas

| Etapa | Qué pasa |
|---|---|
| 1. Entrevista | Preguntas sencillas hasta escribir el brief y confirmarlo contigo. |
| 2. Investigación | Mejores prácticas, versiones y costos vigentes, proyectos y skills que ayuden. Tres opciones. |
| 3. Elección | Eliges una opción y queda registrado por qué. |
| 4. Plan | Casos de uso, arquitectura, datos, pruebas, seguridad y etapas de construcción. |
| 5. Resumen y aprobación | Te lo explica en lenguaje llano y espera tu visto bueno, con tus palabras. |
| 6. Construcción | Por etapas verticales, con pruebas primero. |
| 7. Salida | Checklist completo con puntaje y evidencia. |
| 8. Entrega | Una guía para que tú lo envíes a producción cuando decidas. |

Las puertas son reales. El script no deja pasar a la investigación con un brief incompleto o con dudas abiertas, no deja pedir la aprobación sin un pre-mortem completo, no deja construir sin tu aprobación ni con una etapa sin su contrato, no deja cerrar una etapa cuya verificación falla, y no deja ir a la salida con etapas abiertas.

## El checklist

85 puntos en diez áreas, 18 de ellos críticos: requisitos, investigación, arquitectura, seguridad, pruebas, calidad, operación, documentación, entrega y los propios de cada tipo de proyecto (agenda, tienda, bot, móvil, sitio, gestión y API). Cada punto tiene un peso, y algunos son **críticos**: si falta uno, el veredicto es "no está listo", sin importar el puntaje. A cada proyecto solo le aplican los puntos que le corresponden: sin pagos no se piden los de pagos.

Los puntos son de tres clases, de la más firme a la más débil:

- **Comprobados por el script (38 puntos):** busca secretos en los archivos y en el historial de Git, comprueba que `.env` esté fuera de Git, que haya pruebas con verificaciones reales para cada caso de uso y que cada caso apunte a una prueba que existe, que no queden dudas abiertas, que el pre-mortem esté hecho, que los criterios no sean frases vagas, que el linter, el build y las pruebas pasen, que los documentos estén completos, que el resumen sea de lenguaje llano y que cada variable de entorno esté explicada.
- **Declarados con referencia verificada (33 puntos):** lo que el script no puede ver directamente, pero que **tiene que citar algo que exista**: el nombre de una prueba, un archivo o una librería. El script comprueba que lo citado esté en el proyecto, rechaza lo inventado y, si más adelante lo citado desaparece, el punto vuelve a pendiente.
- **Declarados sin verificar (14 puntos):** lo único que depende de la palabra de alguien, como lo que dijo la persona o una prueba hecha a mano. Se exige evidencia concreta ("ok" no vale), y el veredicto limita cuánto de lo logrado puede ser de esta clase.

El puntaje separa las tres clases, porque un puntaje alto hecho de cosas que nadie comprobó vale menos.

| Veredicto | Cuándo |
|---|---|
| No está listo para enviar | Falta algún punto crítico, o el puntaje es menor de 70. |
| Listo con reservas | Todos los críticos cumplidos y puntaje de 70 a 89, o puntaje alto pero con más de un cuarto de lo logrado declarado sin verificar. |
| Listo para enviar | Todos los críticos cumplidos, puntaje de 90 o más y como máximo un cuarto declarado sin verificar. |

Los puntos dependen de lo que maneje tu proyecto: pagos, datos personales, cuentas de usuario, varias personas, WhatsApp, móvil, subida de archivos o inteligencia artificial. Si no maneja pagos, no se te piden los puntos de pagos.

## Skills propias y de terceros

La skill es una orquestadora. **Primero usa las nuestras**, si las tienes instaladas: [arquitectura-backend](https://github.com/nanoizax/skill-arquitectura-backend), [decisiones-de-arquitectura](https://github.com/nanoizax/skill-decisiones-de-arquitectura), [pruebas-de-la-actividad](https://github.com/nanoizax/skill-pruebas-de-la-actividad), [documentacion-viva](https://github.com/nanoizax/skill-documentacion-viva) (la memoria del proyecto), [qa](https://github.com/nanoizax/skill-qa), [commits-limpios](https://github.com/nanoizax/skill-commits-limpios) y otras. Si falta alguna, te da el enlace y trabaja con una versión mínima de lo que esa skill haría. Nunca instala nada sola.

Las de terceros que encuentre en internet **solo las sugiere**: las lee enteras, te explica el riesgo en una línea y se instalan únicamente si tú dices que sí. Una skill es texto que la herramienta obedece, y un repositorio puede traer scripts: por eso nunca se ejecuta nada ajeno a ciegas.

## Ejemplos

En [`ejemplo/`](ejemplo/) hay dos proyectos de prueba reales, con personas simuladas, y una nota que explica cómo leerlos:

- **`barberia/`**: "un sistema para llevar la contabilidad de mi barbería y agendar las citas", **de la entrevista hasta listo para enviar: 100 de 100**. Tiene 656 pruebas, ocho etapas cerradas cada una con su contrato verificado por el script, un pre-mortem, un traspaso, una investigación con búsquedas web de ese día, un cambio de tecnología hecho con `retroceder` (que obligó a que la persona aprobara de nuevo) y la guía de entrega. Del peso total del checklist (128), 79 los comprobó el script, 40 se declararon citando pruebas o archivos que el script verificó que existen, y solo 9 dependen de la palabra de alguien.
- **`asistente-whatsapp/`**: un asistente de WhatsApp para un consultorio, con perfil bot, **hasta el inicio de la construcción**, con el pre-mortem y el contrato de cada etapa ya escritos. Su puntaje es de 27 sobre 100 y "no está listo", que es lo correcto: todavía no hay código.

El 100 no significa "sin errores". Antes de ese número, una revisión independiente (alguien que no había construido nada) probó el producto en dos rondas y encontró **ocho problemas reales** que el checklist, casi completo, no veía: reservas con barberos que no existían, falta de límites contra abusos, errores 500 con entradas extremas y una carrera entre cancelar y atender. Por eso la revisión independiente es un punto **crítico**, y por eso se corrigieron y se volvieron a probar.

## Qué la distingue de otras herramientas parecidas

Hay otras skills que también planifican antes de construir. Esta se apoya en tres diferencias:

- **Las puertas las aplica un script, no la buena voluntad.** Una etapa no se cierra porque se diga que terminó, sino porque su comando de verificación pasó. Lo que no se pudo comprobar queda marcado como tal en el puntaje.
- **Se queda hasta el final.** No se limita a dejar un plano para que otra herramienta construya: acompaña la construcción, comprueba cada etapa, calcula el puntaje y da un veredicto. Si prefieres que otra instancia construya, `traspaso` le deja un documento completo.
- **Está pensada para quien no programa**: preguntas de a una con una recomendación, un plan explicado en lenguaje llano y una guía de entrega que no da por hecho que sabes qué es un servidor.

De otras skills se tomaron ideas concretas que mejoran el proceso: las dudas bloqueantes antes de planificar, el pre-mortem, los criterios de "hecho cuando" con comando de verificación, los puntos de retorno por etapa, el modo para proyectos que ya existen y la fecha de última revisión de cada guía.

## Cuándo usarla

- Vas a construir algo completo desde cero (un sistema, una tienda, un agente, una página con funciones).
- No eres programador y quieres que el resultado se sostenga en producción.
- Eres programador y quieres un proceso y un checklist para no olvidar lo de siempre.

## Cuándo **no** usarla

- Para un cambio pequeño en un proyecto que ya existe: usa [`skill-pruebas-de-la-actividad`](https://github.com/nanoizax/skill-pruebas-de-la-actividad).
- Para un prototipo desechable que no vas a publicar.
- Si necesitas que alguien despliegue por ti: esta skill no lo hace, a propósito.

## Cómo instalarla

1. Descarga este repositorio y copia su contenido en una carpeta llamada `el-ingeniero` dentro del directorio de skills de tu herramienta de desarrollo.
2. Necesitas **Python 3.8 o superior** y **Git**. La herramienta tiene que poder buscar en internet: sin eso, la skill se detiene a propósito.
3. Listo. Se activa sola cuando pides construir algo completo. También puedes pedirla: "ingeniero, ayúdame a planificar mi proyecto".

Cada herramienta guarda sus skills en un sitio distinto; consulta la documentación de la tuya.

## Qué incluye

- **`SKILL.md`:** el método, las reglas que no se negocian y el informe de cierre.
- **`references/`:** una guía por etapa (entrevista, perfiles de proyecto, investigación, terceros, construcción, entrega, lenguaje llano y nuestras skills). Se cargan solo cuando hacen falta.
- **`plantilla/`:** los documentos del plan, con huecos `[[...]]` que hay que llenar. El script no da por cumplido un documento que aún tenga huecos.
- **`datos/checklist.json`:** los puntos del checklist, con su peso, si son críticos y cómo se comprueban.
- **`scripts/ingeniero.py`:** guarda el estado y hace lo mecánico. Órdenes: `iniciar`, `estado`, `datos`, `comandos`, `avanzar`, `retroceder`, `elegir`, `etapa-agregar`, `etapa-contrato`, `etapa-verificar`, `etapa-cerrar`, `siguiente`, `traspaso`, `detectar`, `rescate`, `verificar`, `marcar`, `descartar`, `pendientes`, `puntaje`, `tendencia`, `informe` y `skills`. `puntaje --exigir 80` termina con código 2 si no se llega al mínimo o queda un crítico pendiente, para usarlo en automatizaciones; `tendencia` avisa si el proyecto empeoró desde la verificación anterior; `informe` explica en lenguaje llano dónde va el proyecto.
- **`ejemplo/`:** la barbería de punta a punta.

## Cómo está organizado el código

`scripts/ingeniero.py` recibe las órdenes. El trabajo está en `scripts/ingeniero_lib/`: `estado.py`, `flujo.py`, `etapas.py`, `existente.py`, `traspaso.py`, `checklist.py`, `verificar.py`, `referencias.py`, `skills_propias.py`, `plantillas.py` y `util.py`. Las pruebas están en `tests/`.

## Límites honestos

- **No garantiza que el producto no falle.** Reduce mucho el riesgo y dice qué quedó sin comprobar. Un puntaje alto no es un certificado.
- **El veredicto es una regla sobre el checklist, no un oráculo.** Los puntos declarados dependen de que quien trabaja diga la verdad y dé evidencia real. El script exige evidencia concreta, pero no puede verificarla.
- **La investigación depende de la búsqueda web de tu herramienta.** En la prueba hubo fuentes que se contradecían (versiones, precios, el estado de una ley), y la skill las anotó como "no verificado". Los números que se van a fijar hay que leerlos del registro de paquetes, no de un artículo.
- **Los perfiles y las tres opciones de partida son puntos de partida.** Pueden estar desactualizados el día que la uses. Por eso la investigación siempre va primero.
- **La probé de punta a punta una sola vez, con una barbería simulada** (Python, FastAPI y SQLite), de la entrevista a listo para enviar. Un segundo proyecto, un bot de WhatsApp, llegó hasta el inicio de la construcción. Las personas de los dos ejemplos son simuladas y **el código de la barbería lo escribió una herramienta con una especificación cerrada**, no una persona sin experiencia pidiéndolo con sus palabras. No la he probado con una persona real que no programa, ni con proyectos de tienda, aplicación móvil, sitio o API, ni con otras tecnologías.
- **Un puntaje alto no reemplaza una revisión real.** En la prueba, el checklist decía "listo" mientras la revisión independiente todavía encontraba problemas. Por eso esa revisión es un punto crítico y por eso conviene que la haga alguien, o una instancia de la herramienta, que no vio el código.
- **No reemplaza una revisión legal ni de seguridad profesional.** Los puntos de datos personales y de seguridad son un mínimo sano, no una auditoría. Si tu proyecto maneja pagos o datos delicados, consulta a una persona experta.
- **Necesita internet y que tu herramienta pueda ejecutar comandos** (para correr pruebas, linter y el script).
- **Los comandos del proyecto (pruebas, linter, build, auditoría) los defines tú** con `comandos`, y el script los ejecuta sin shell en la carpeta del proyecto. Revísalos antes, como harías con cualquier comando.
- **No despliega nada.** Es una decisión de diseño, no una carencia: el envío a producción es tuyo.

## Skills relacionadas

- [`skill-arquitectura-backend`](https://github.com/nanoizax/skill-arquitectura-backend): cómo se estructura el código del servidor.
- [`skill-decisiones-de-arquitectura`](https://github.com/nanoizax/skill-decisiones-de-arquitectura): dejar por escrito el porqué de cada decisión.
- [`skill-pruebas-de-la-actividad`](https://github.com/nanoizax/skill-pruebas-de-la-actividad): pruebas de cada etapa y veredicto antes del commit.
- [`skill-documentacion-viva`](https://github.com/nanoizax/skill-documentacion-viva): la documentación que sirve de memoria del proyecto.
- [`skill-qa`](https://github.com/nanoizax/skill-qa): una revisión independiente antes de dar algo por listo.
- [`skill-commits-limpios`](https://github.com/nanoizax/skill-commits-limpios): para que los commits salgan bien hechos.

## Licencia y autoría

[MIT](LICENSE) · Hecha por Leandro Manuel Perez Montañana.
Más skills y herramientas gratis en **[soytegno.sonholab.com](https://soytegno.sonholab.com)** · TikTok [@soytegno](https://www.tiktok.com/@soytegno)
