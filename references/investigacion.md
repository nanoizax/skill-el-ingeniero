# La investigación

Se hace **después** de la entrevista y **antes** del plan. Sirve para que la recomendación sea de este mes y no de lo que el modelo recuerda de hace un año. Sin internet no se hace, y sin investigación no se recomienda: se para y se le dice a la persona.

## Qué se investiga

1. **Versiones soportadas hoy** del lenguaje y del framework candidatos (la versión con soporte de largo plazo, si existe) y si alguna está por perder el soporte.
2. **Seguridad vigente** para ese tipo de proyecto: las prácticas actuales de autenticación, contraseñas y manejo de sesiones. No se copian ejemplos viejos.
3. **Costos y límites reales** de lo que se vaya a usar: alojamiento, base de datos, correo, mensajes, WhatsApp, pagos, modelos de lenguaje. Con la fecha de consulta.
4. **Normativa del país** sobre datos personales y, si hay pagos, sobre facturación.
5. **Proyectos de referencia** en GitHub parecidos al que se quiere hacer (para aprender su estructura, no para copiarlos).
6. **Skills y herramientas de terceros** que ayuden (ver `terceros.md`).
7. **Soluciones ya hechas** que cubran la necesidad sin construir nada.

## Qué no va en una búsqueda

Lo que se escribe en un buscador sale de tu equipo. Por eso las búsquedas llevan **términos genéricos** ("software de agenda para barbería", "precios de WhatsApp Business") y nunca el nombre de la persona o del negocio, correos, teléfonos, claves ni datos del proyecto que no sean públicos. Si para investigar necesitas pegar algo privado, no lo pegues: describe la situación en general.

## Cómo

- Usa la búsqueda web de la herramienta. Unas 8 a 12 búsquedas bien dirigidas bastan; no es una tesis.
- **Jerarquía de fuentes:** documentación oficial, luego notas de versión, luego repositorios con actividad reciente (último commit de los últimos seis meses, mantenedores, licencia clara, incidencias atendidas; las estrellas solas no prueban nada), y al final artículos. Un artículo sin fecha o de más de 18 meses no sirve para decidir versiones ni precios.
- **Cada hallazgo se anota con fecha, enlace y tipo de fuente:** `[fuente: oficial]` (la página o la documentación de quien lo hace), `[fuente: secundaria]` (un artículo, una comparación, un blog) o `[fuente: opinión]` (una experiencia personal). Tiene que haber al menos uno oficial: sin ninguno, todo es de segunda mano. Un dato que solo aparece en fuentes secundarias se dice así y se pone en "no verificado" si cambia una decisión.
- **Cada hallazgo se anota con fecha y enlace.** Lo que no pudiste confirmar se anota como **no verificado**. Nunca se rellena con lo que "debería ser".
- Si dos fuentes se contradicen, gana la oficial y se anota la contradicción.
- **Las versiones que se van a fijar se leen del registro de paquetes, no de un artículo.** Un artículo o una página resumen se queda atrás: en una prueba real, una búsqueda dio una versión de FastAPI de hacía meses y el registro (`pip index versions`, `npm view <paquete> version`) daba una bastante más nueva. La búsqueda sirve para saber qué línea está vigente; el número exacto sale del registro y se anota con la fecha.

## Las tres opciones

Siempre tres, comparables, en `docs/ingeniero/investigacion.md`:

| | Opción A | Opción B | Opción C |
|---|---|---|---|
| Qué es | | | |
| Para quién es buena | | | |
| Costo mensual aproximado y fecha de consulta | | | |
| Qué tan bien la conoce la herramienta (menos errores) | | | |
| Riesgos | | | |
| Cuándo **no** elegirla | | | |

Después, **una recomendación con su razón** en dos o tres líneas y lo que se sacrifica. La persona elige. Si pide una cuarta o una mezcla, se evalúa con el mismo rigor.

La opción de partida suele ser Node con NestJS, PostgreSQL y arquitectura limpia (o Python cuando el proyecto es de datos o de inteligencia artificial), pero solo si la investigación no dice lo contrario. Si no se elige esa, se dice por qué.

## Cuando no hay internet o la búsqueda falla

Se para. Se le dice a la persona: "No puedo investigar lo vigente ahora; sin eso no te recomiendo una tecnología. ¿Probamos de nuevo cuando haya conexión?". No se avanza con valores de memoria.

## Registro

`docs/ingeniero/investigacion.md` lleva la fecha de la investigación en el encabezado, los hallazgos con enlace, las tres opciones, la recomendación, la elección de la persona (cuando la haga) y la lista de lo no verificado. El script comprueba que esos elementos existan.
