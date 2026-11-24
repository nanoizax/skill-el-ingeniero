# Seguridad: Asistente de WhatsApp del consultorio

## Datos personales
- Qué se guarda: nombre, teléfono y conversaciones de los pacientes, que pueden incluir datos de salud.
- Para qué: responder preguntas, agendar horas y poder revisar lo que se dijo.
- Cuánto tiempo: el plazo se confirmará con asesoría legal antes de publicar; mientras tanto no se guarda más de lo necesario.
- Cómo se borra: a pedido del paciente se anonimizan su nombre y su teléfono; las conversaciones viejas se borran con una limpieza programada.
- Normativa aplicable: Ley 21.719 de Chile, que según las fuentes entra en vigencia el 2026-12-01 y trata los datos de salud como sensibles (consultado el 2026-11-24).

## Cuentas y permisos
Solo la secretaria y la doctora acceden a las conversaciones, con usuario y contraseña. Los pacientes no tienen cuenta: hablan por WhatsApp.

## Secretos
Las claves de WhatsApp y del modelo de lenguaje viven en variables de entorno, nunca en el código ni en Git.

## Pagos
No se manejan pagos en esta versión.

## Riesgos principales y cómo se reducen
- Que el asistente diga algo falso sobre salud: solo cita información cargada y deriva a una persona.
- Gasto descontrolado: límite de mensajes por paciente y por día, y alerta de consumo.
- Instrucciones maliciosas: el asistente no ejecuta acciones por lo que diga un mensaje; las acciones pasan por reglas fijas.
- Exposición de datos de salud: acceso restringido, registros sin datos sensibles y respaldo cifrado.
