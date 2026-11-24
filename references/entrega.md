# La salida y la entrega

"Listo para producción" significa **listo para enviar**: el producto está terminado, probado y documentado, y la persona tiene una guía clara para publicarlo. **Publicarlo es decisión suya y lo hace ella**, bajo sus propios criterios. El ingeniero no despliega, no compra, no crea cuentas a su nombre y no le pide claves.

## La salida (etapa 7)

1. `ingeniero.py verificar`: corre todas las comprobaciones automáticas.
2. Completa lo manual con **evidencia real** (`marcar`): el nombre de una prueba que existe, el archivo donde está algo, la librería usada. El script comprueba que lo citado exista. "Está bien" no es evidencia.
3. **Revisión independiente (crítica).** Alguien que no construyó el producto intenta romperlo contra los casos de uso, con la skill `qa` si está instalada, con otra persona o con otra instancia de la herramienta que no vio el código. Toma su veredicto GO o NO-GO como evidencia. No se salta: en la prueba de esta skill, un checklist ya casi completo decía "listo" y la revisión independiente todavía encontró ocho problemas reales (reservas con barberos que no existen, falta de límites de abuso, errores 500 con entradas extremas y una carrera entre cancelar y atender). Si la revisión encuentra algo, se corrige y se vuelve a probar lo corregido.
4. `ingeniero.py puntaje`: puntaje, críticos pendientes y veredicto.
5. Si no está listo, dilo con claridad y di qué falta. No se adelanta la entrega para "quedar bien".

## El paquete de entrega

`docs/ingeniero/entrega.md` es la guía para la persona. Debe estar escrita para alguien que no es técnico e incluir:

- **Qué recibes:** qué hace el producto y dónde está el código.
- **Opciones para publicarlo**, con costo mensual aproximado y la fecha en que se consultó (dos o tres opciones, de la más simple a la más flexible).
- **Pasos para publicarlo** en la opción que ella elija, uno por uno.
- **Cuentas que debes crear tú**, a tu nombre: alojamiento, dominio, correo, pagos, etc. Todo lo que tenga costo o requiera un contrato lo decide y lo paga ella.
- **Variables de entorno:** qué son, cuáles hay, para qué sirve cada una y dónde se ponen. **Sin valores.**
- **Respaldo y restauración:** qué se respalda (la base de datos y los archivos que suban los usuarios), cada cuánto, **en qué otro lugar** y cómo se restaura. Una copia guardada en la misma máquina que los datos no es un respaldo. Y un respaldo que nunca se restauró no está probado.
- **Cómo comprobar que quedó bien** después de publicar (una lista corta de cosas que mirar).
- **Qué hacer si algo sale mal:** cómo volver a la versión anterior.
- **Mantenimiento:** actualizaciones de seguridad, renovación del dominio, revisión de costos.
- **Qué decisiones son tuyas:** la lista de cosas que el ingeniero deliberadamente no hizo.

## Lo que el ingeniero nunca hace en esta etapa

- Desplegar, publicar o poner el producto en internet.
- Comprar dominios, hosting o servicios, ni registrarse en ellos.
- Pedir o guardar contraseñas, tokens o llaves de la persona.
- Entrar a cuentas de la persona.
- Prometer que "no va a fallar".

Si la persona pide ayuda para publicar, se le da la guía paso a paso y se queda a su lado para explicar, pero **cada acción con costo, cuenta o clave la hace ella**.

## Veredicto

| Veredicto | Cuándo |
|---|---|
| No está listo para enviar | Hay un ítem crítico pendiente, o el puntaje es menor de 70. |
| Listo con reservas | Todos los críticos cumplidos y puntaje de 70 a 89, o puntaje alto pero con más de un cuarto declarado sin poder comprobarse. |
| Listo para enviar | Todos los críticos cumplidos, puntaje de 90 o más y como máximo un cuarto declarado sin comprobar. |

Se acompaña siempre de lo que falta, de lo que se declaró sin comprobar y de lo que no se cubrió. No es una garantía: es el mejor resumen honesto del estado del proyecto.

## Cierre con la persona

Entrégale un resumen de cinco líneas en lenguaje llano: qué quedó, cuánto costará mantenerlo cada mes, qué debe hacer ella ahora, qué riesgos quedan y a quién llamar si algo se rompe. Y recuérdale que el envío a producción lo decide ella.
