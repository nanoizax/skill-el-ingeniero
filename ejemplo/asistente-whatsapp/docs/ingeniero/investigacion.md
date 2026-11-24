# Investigación: Asistente de WhatsApp del consultorio

Fecha de la investigación: 2026-11-24

## Qué se investigó
La vía oficial y las no oficiales para conectar WhatsApp, sus costos, el riesgo de bloqueo del número, el costo de usar un modelo de lenguaje y la normativa chilena de datos personales.

## Hallazgos (cada uno con fecha de consulta, enlace y tipo de fuente)
- WhatsApp cobra por mensaje desde el 2025-07-01 y no cobra los mensajes que envía el paciente al negocio; los mensajes de plantilla son los únicos que se pueden enviar fuera de la ventana de atención (consultado el 2026-11-24) [fuente: oficial]: https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing
- Fuentes secundarias indican que desde 2026-10-01 las respuestas de servicio se cobran después de un cupo gratis mensual (cerca de mil por número); no se encontró confirmado en la página de Meta (consultado el 2026-11-24) [fuente: secundaria]: https://www.eesel.ai/blog/whatsapp-business-api-pricing
- Las bibliotecas no oficiales violan los términos de WhatsApp, y el riesgo de bloqueo del número es real e impredecible; varias fuentes las recomiendan solo para uso de prueba con un número que se pueda perder (consultado el 2026-11-24) [fuente: opinión]: https://dev.to/achiya-automation/ive-deployed-50-whatsapp-bots-heres-how-the-spam-detection-algorithm-actually-works-in-2026-69a
- La Ley 21.719 de Chile entra en vigencia el 2026-12-01 salvo que se apruebe el proyecto que la posterga; los datos de salud son datos sensibles (consultado el 2026-11-24) [fuente: secundaria]: https://www.diarioconstitucional.cl/2026/06/12/la-ley-21-719-entra-en-vigor-el-1-de-diciembre-y-expone-vacios-en-regulacion-de-pequenas-empresas/
## Las tres opciones

### Opción A: la conexión oficial de WhatsApp con un servicio propio
- Qué es: un servicio propio que recibe los mensajes por la conexión oficial de Meta, usa un modelo de lenguaje con reglas estrictas y guarda las citas.
- Para quién es buena: para quien quiere usar WhatsApp de forma permitida y mantener el control de los datos.
- Costo mensual aproximado: entre 20 y 45 dólares entre servicio, modelo de lenguaje y mensajes (consultado el 2026-11-24); depende del volumen y del cupo gratis.
- Riesgos: hay que verificar el negocio con Meta y la calidad de las plantillas afecta los límites.
- Cuándo no elegirla: si el consultorio no puede completar la verificación de negocio.

### Opción B: una plataforma de bots ya hecha
- Qué es: contratar un servicio que ya trae el asistente y la conexión a WhatsApp, y configurarlo.
- Para quién es buena: para quien quiere empezar en días y no mantener código.
- Costo mensual aproximado: entre 30 y 100 dólares según el proveedor (consultado el 2026-11-24, sin confirmar precios exactos).
- Riesgos: los datos de salud de los pacientes quedan en una empresa externa y el consultorio depende de sus cambios de precio.
- Cuándo no elegirla: si la ley o el criterio de la doctora exigen tener los datos en su poder.

### Opción C: empezar por otro canal propio
- Qué es: un chat en la página web del consultorio, sin WhatsApp, para validar el asistente antes de conectarlo.
- Para quien es buena: para probar con pocos pacientes sin riesgo de bloqueo ni verificación.
- Costo mensual aproximado: entre 10 y 25 dólares (consultado el 2026-11-24).
- Riesgos: los pacientes ya usan WhatsApp y pocos entrarán a la página.
- Cuándo no elegirla: si lo que importa es que los pacientes escriban donde ya escriben.

## Recomendación
Se recomienda la opción A, porque es la única que combina la vía permitida de WhatsApp con el control de los datos de salud. Se sacrifica rapidez: la verificación del negocio con Meta puede tardar. Mientras se espera, la opción C permite probar las reglas del asistente sin riesgo.

## Elección de la persona
Eligió la opción A el 2026-11-24: "Quiero WhatsApp de verdad y que los datos queden conmigo".

## Skills y repositorios revisados
- No se buscaron skills de terceros para esta prueba: el plan se apoya en las skills propias de arquitectura, pruebas y decisiones (consultado el 2026-11-24). Queda anotado para quien lo repita.

## No verificado
- El cupo gratis exacto de respuestas de servicio desde octubre de 2026 y el precio actual por mensaje en Chile.
- El costo exacto de las plataformas de la opción B.
- Si el proyecto que posterga la Ley 21.719 ya fue aprobado.
