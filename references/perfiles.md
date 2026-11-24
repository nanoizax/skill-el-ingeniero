# Perfiles de proyecto

Un perfil es un punto de partida: preguntas extra, riesgos típicos y tres opciones de tecnología que **hay que confirmar con la investigación** del momento. Nada de esto es una receta fija. Si el proyecto no encaja, usa `otro`.

La tendencia del equipo es Node con NestJS, PostgreSQL, arquitectura limpia (monolito modular) y Python cuando el proyecto es de datos o de inteligencia artificial. Es un punto de partida, no una obligación: la investigación manda.

## agenda (citas y reservas: barbería, clínica, canchas)

- **Pregunta extra:** ¿qué pasa si dos personas piden la misma hora? ¿Se puede cancelar y hasta cuándo? ¿Hay recordatorios?
- **Riesgos:** doble reserva, zonas horarias, recordatorios que no llegan, datos de clientes.
- **Opciones de partida:** (A) web con NestJS y PostgreSQL, (B) web con Python y FastAPI, (C) solución ya hecha configurable. Ofrece siempre la opción "no construir", si ya existe algo que sirve.
- **Casos de uso típicos:** agendar, cancelar, mover, ver la agenda del día, registrar un cobro, recordar una cita.

## tienda (venta en línea)

- **Pregunta extra:** ¿cuántos productos? ¿Envíos? ¿Qué medios de pago?
- **Riesgos:** pagos, inventario que no cuadra, impuestos, devoluciones.
- **Opciones de partida:** (A) tienda con plataforma existente, (B) web a medida con NestJS y PostgreSQL, (C) web a medida con Python.
- **Regla:** jamás se guardan datos de tarjetas; se usa un proveedor de pagos certificado.

## bot (WhatsApp o agente con inteligencia artificial)

- **Pregunta extra:** ¿qué debe responder solo y qué debe pasar a una persona? ¿Qué no debe decir nunca?
- **Riesgos:** la vía de WhatsApp (la oficial tiene reglas y costo por conversación; las no oficiales arriesgan el bloqueo del número), respuestas inventadas, costo por uso del modelo, datos personales, abuso.
- **Opciones de partida:** (A) API oficial de WhatsApp más un servicio propio, (B) un servicio propio con otro canal (web o Telegram), (C) una plataforma de bots existente.
- **Regla:** el bot nunca decide solo cobros ni borrados. Siempre hay un registro de lo que dijo.

## api (servicio o producto para otros programas)

- **Pregunta extra:** ¿quién lo consume? ¿Con qué volumen? ¿Se cobra por uso?
- **Riesgos:** versionado, límites de uso, autenticación, compatibilidad hacia atrás.
- **Opciones de partida:** (A) NestJS con PostgreSQL, (B) FastAPI con PostgreSQL, (C) un servicio gestionado.

## sitio (informativo o página de presentación)

- **Pregunta extra:** ¿cambia el contenido seguido? ¿Quién lo edita?
- **Riesgos:** velocidad, SEO, formularios con spam, textos legales.
- **Opciones de partida:** (A) sitio estático, (B) estático con un gestor de contenido, (C) web con framework. Un sitio informativo rara vez necesita base de datos.

## gestion (contabilidad, inventario y herramientas internas)

- **Pregunta extra:** ¿hoy está en Excel? ¿Quién puede ver las cifras?
- **Riesgos:** cálculos que no cuadran (redondeo, monedas), permisos por rol, respaldo, auditoría de cambios.
- **Opciones de partida:** (A) NestJS con PostgreSQL, (B) Python con PostgreSQL, (C) una hoja compartida bien estructurada, si el volumen es pequeño.
- **Regla:** el dinero se guarda en enteros (centavos) o con tipos decimales exactos, nunca en números de coma flotante.

## movil (aplicación en celular)

- **Pregunta extra:** ¿Android, iPhone o ambos? ¿Funciona sin conexión?
- **Riesgos:** publicación en las tiendas, firma de la aplicación (si se pierde la llave, no se puede actualizar nunca más), permisos.
- **Opciones de partida:** (A) Flutter, (B) React Native, (C) aplicación web instalable.
- **Regla:** la llave de firma se respalda en el mismo momento en que se crea.

## otro

Usa las preguntas universales y deja que la investigación proponga las opciones.

## Siempre, en cualquier perfil

- Pregunta por el país: define impuestos, moneda y la ley de datos personales aplicable.
- Pregunta qué pasaría si falla un día entero: eso decide cuánto esfuerzo merecen los respaldos y las alertas.
- Ofrece la opción de **no construir** si existe una herramienta que ya resuelve el problema. Es honesto y a veces es lo mejor.
