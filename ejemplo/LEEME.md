# Ejemplos: dos proyectos de prueba

Esta carpeta tiene el resultado real de probar la skill con dos proyectos inventados. Léelos como lo que son: pruebas, con personas simuladas.

## Qué es real y qué no

- **Las respuestas de las personas son simuladas.** Don Mario (la barbería) y la doctora Carolina (el consultorio) no existen. Las respuestas a la entrevista y sus aprobaciones las escribí yo para la prueba.
- **La investigación sí es real**, hecha con búsquedas web el 24 de noviembre de 2026. Las contradicciones entre fuentes quedaron anotadas como "no verificado", que es lo que la skill pide.
- **El código de la barbería es real y sus pruebas pasan.** Lo escribió una herramienta con una especificación cerrada, no una persona sin experiencia.
- **La revisión independiente fue real:** una revisora que no construyó nada probó la barbería en dos rondas y encontró ocho problemas que luego se corrigieron.

## `barberia/`: de la entrevista a listo para enviar

"Un sistema para llevar la contabilidad de mi barbería y agendar las citas". Puntaje final: **100 de 100, listo para enviar**, con las 8 etapas construidas, cada una cerrada con su contrato verificado por el script, 656 pruebas y el linter limpio. También trae el `premortem.md` y el `traspaso.md` que genera la orden `traspaso`. Está en `barberia/puntaje.json`.

Qué mirar:

1. `barberia/docs/ingeniero/`: el plan completo, la investigación con tres opciones, los casos de uso, la guía de entrega para la persona, `estado.json` (la memoria del proyecto) y `informe.md`, el resumen en lenguaje llano que genera la orden `informe`.
2. `barberia/docs/decisiones/`: tres decisiones registradas. La tercera, el cambio de PostgreSQL a SQLite, se hizo con `retroceder`, y obligó a que la persona aprobara de nuevo.
3. `barberia/app/`, `barberia/tests/` y `barberia/scripts/`: la estructura por módulos y capas, las pruebas que se escribieron antes que el código y los scripts de respaldo, restauración y borrado de datos a pedido.

Para ejecutar sus pruebas, instala `requirements.txt` en un entorno virtual y corre `python -m pytest -q`.

## `asistente-whatsapp/`: un bot, hasta el inicio de la construcción

Un asistente de WhatsApp para un consultorio (perfil bot). Llega hasta la aprobación del plan y la etapa de construcción, sin código todavía, con el pre-mortem hecho y el contrato de cada etapa escrito (qué debe ser cierto y qué comando lo demuestra). Su puntaje es **27 de 100, no está listo**, que es lo correcto. Sirve para ver los puntos propios de un bot (costo por uso, instrucciones maliciosas, registro de conversaciones y traspaso a una persona).

## Lo que estos ejemplos no prueban

No prueban que la skill funcione con una persona real que no programa, ni con tiendas, aplicaciones móviles, sitios o APIs, ni con otras tecnologías. Un puntaje alto tampoco es un certificado: la revisión independiente encontró problemas con el checklist casi completo.
