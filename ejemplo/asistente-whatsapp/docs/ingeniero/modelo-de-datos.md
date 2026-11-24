# Modelo de datos: Asistente de WhatsApp del consultorio

## Entidades y relaciones
- Paciente: nombre y teléfono; tiene muchas conversaciones y muchas citas.
- Conversación: pertenece a un paciente y tiene un estado (con el asistente o con la secretaria).
- Mensaje: pertenece a una conversación, con quién lo escribió (paciente, asistente o secretaria), el texto y la fecha.
- Cita: une un paciente con una hora y un estado (confirmada, cancelada, atendida).
- Información del consultorio: horarios, precios, dirección y tratamientos que el asistente puede citar.

## Reglas de los datos
- Una hora no puede tener dos citas confirmadas.
- Las fechas se guardan en hora universal.
- El teléfono se guarda en un formato único con el código del país.

## Datos sensibles
Las conversaciones pueden contener datos de salud, que son datos sensibles. Solo la secretaria y la doctora pueden leerlas. No se envían a servicios externos más de lo necesario para redactar la respuesta.

## Retención y borrado
Las conversaciones se guardan por un plazo que se confirmará con asesoría legal. A pedido de un paciente se anonimizan su nombre y su teléfono.

## Migraciones
Los cambios de la base se versionan en archivos numerados y se prueban en una base vacía y en una con datos.

## Respaldo
Se respalda el archivo de la base cada día en otra máquina distinta a la del servicio.
