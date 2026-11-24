# La entrevista

Objetivo: terminar con un **brief** de una página que la persona reconozca como suyo, y con los datos que decidirán qué checklist aplica. No es un interrogatorio: es una conversación corta y concreta.

## Cómo preguntar

- **Una pregunta por mensaje.** Nunca una lista de diez.
- **Con opciones.** "¿Los clientes agendan solo desde la página, o también por WhatsApp? Te recomiendo empezar por la página y sumar WhatsApp después, porque es más simple y más barato."
- **Con una recomendación**, siempre. Quien no es programador no sabe qué elegir y no debería tener que adivinarlo.
- **Con las palabras de la persona.** Si dijo "turnos", no escribas "reservas".
- **"No sé" es una respuesta válida.** Propón un valor por defecto, di que lo es y anótalo en "Supuestos".
- **Cada cuatro respuestas, refleja lo que entendiste** en dos líneas y pregunta si es correcto.
- **Máximo unas doce preguntas** antes del primer brief. Lo que falte va a "Dudas abiertas" y se resuelve cuando sea necesario.

## Camino rápido

Si la idea es pequeña (una página, un bot sencillo, una herramienta para una sola persona) y **no** maneja pagos, datos personales ni varias personas, usa `iniciar --rapido`: solo tres preguntas (qué quiere lograr, quién lo usa, qué es imprescindible el primer día). Todo lo demás se **propone como supuesto y se dice en voz alta** ("supongo que se usa desde el celular y sin cuentas; corrígeme si no"), y queda en "Supuestos" del brief. Si en cualquier momento aparece dinero, datos de personas o cuentas, se pasa a la entrevista completa. Quien prefiera ir rápido puede recibir hasta tres preguntas por mensaje.

## Dudas que bloquean

Lo que no se pueda suponer sin riesgo se escribe en el brief como `[DUDA: la pregunta]`. El script no deja avanzar a la investigación mientras quede alguna; se quita el marcador cuando la persona contesta.

## Las preguntas, en este orden

1. **¿Qué quieres lograr?** En una frase y con sus palabras. ("Dejar de anotar citas en un cuaderno.")
2. **¿Quién lo va a usar?** Tú, tu equipo, tus clientes, todos. Cuántas personas aproximadamente.
3. **¿Cómo lo haces hoy?** Cuaderno, Excel, WhatsApp, otra aplicación. De ahí salen los datos que quizá haya que migrar.
4. **¿Qué es imprescindible el primer día?** Y separado: ¿qué puede esperar? Esto define la primera versión.
5. **¿Desde dónde se usará?** Celular, computador o ambos.
6. **¿Maneja dinero?** Cobrar, pagos en línea, caja, facturas. (Activa los ítems de pagos.)
7. **¿Guarda datos de personas?** Nombres, teléfonos, correos, historial. (Activa los ítems de datos personales.)
8. **¿Cómo avisa a la gente?** Correo, WhatsApp, mensajes de texto, nada.
9. **¿Cuenta con usuarios y contraseñas?** ¿Cada persona ve solo lo suyo? (Activa autenticación y autorización.)
10. **¿Dónde y en qué idioma?** País, moneda, zona horaria. Cambia lo legal, los impuestos y los formatos.
11. **¿Cuánto puedes gastar al mes** en servicios (alojamiento, mensajes)? Un rango basta. Y **¿quién lo va a mantener** después?
12. **¿Hay un plazo?** Y ¿qué pasaría si falla un día entero?

Después de la 12, pregunta una cosa más según el perfil (ver `perfiles.md`).

## Qué banderas se levantan

Al terminar, declara con `ingeniero.py datos` lo que el proyecto maneja. Cada bandera enciende ítems del checklist:

| Bandera | Se activa si... |
|---|---|
| `pagos` | cobra o maneja dinero |
| `datos-personales` | guarda datos de personas |
| `cuentas` | hay usuarios con contraseña |
| `multiusuario` | cada persona debe ver solo lo suyo |
| `whatsapp` | se comunica por WhatsApp |
| `movil` | incluye una aplicación móvil |
| `base-de-datos` | guarda información que debe persistir (casi siempre sí) |
| `archivos` | la gente sube fotos o documentos |
| `ia` | usa un modelo de lenguaje para responder o decidir |
| `interfaz` | la gente usa pantallas (página o aplicación), no solo un servicio por detrás |

## Respuestas vagas

- "Quiero que sea moderno": pregunta por un ejemplo que le guste. Anota la referencia.
- "Que sirva para todo": pregunta qué haría un martes cualquiera. Anota los tres casos más comunes y deja el resto fuera de alcance.
- "Lo más barato": explica en una línea qué se sacrifica y propón dos niveles.
- "No tengo tiempo para contestar": ofrece un brief con tus supuestos y que corrija solo lo que esté mal.

## Cierre de la entrevista

Escribe el brief (`docs/ingeniero/brief.md`) y léeselo en tres o cuatro líneas: "Esto es lo que entendí. ¿Es correcto? ¿Falta algo importante?". Solo cuando confirme, `avanzar investigacion`.

## Ejemplo (barbería)

> **Persona:** necesito un sistema para llevar la contabilidad de mi barbería y agendar las citas.
> **Ingeniero:** Para empezar, ¿quién va a usarlo? (a) solo tú, (b) tú y tus barberos, (c) tú, tus barberos y tus clientes. Te recomiendo (c) si quieres que los clientes agenden solos.
> **Persona:** tú, yo y dos barberos, y los clientes agendan.
> **Ingeniero:** Perfecto. ¿Cómo agendas hoy? ...

Y así, hasta el brief.
