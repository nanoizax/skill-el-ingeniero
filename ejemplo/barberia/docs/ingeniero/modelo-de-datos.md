# Modelo de datos: Barbería Don Mario

## Entidades y relaciones
- Persona: quien inicia sesión (dueño, barbero o recepcionista), con su rol.
- Barbero: pertenece a una persona y tiene su horario de trabajo.
- Cliente: nombre y teléfono; puede tener muchas citas.
- Servicio: nombre, duración en minutos y precio en pesos.
- Cita: une cliente, barbero y servicio con un inicio y un fin y un estado (confirmada, cancelada, atendida).
- Cobro: pertenece a una cita atendida, con monto en pesos y medio de pago.

## Tablas
usuarios, citas y cobros, creadas por la migración 001. La migración 002 agrega un índice por barbero e inicio para que las agendas sean rápidas. Un cobro apunta a su cita, y el correo de cada usuario es único.

## Reglas de los datos
- El dinero se guarda en pesos enteros, sin decimales ni números de coma flotante.
- Un barbero no puede tener dos citas confirmadas que se solapen en el tiempo.
- Una cita solo puede cobrarse una vez y solo si fue atendida.
- Las fechas se guardan en hora universal.

## Datos sensibles
Nombre y teléfono de los clientes son datos personales. Solo los ve quien trabaja en la barbería; un cliente ve únicamente sus propias citas. No se guardan datos de tarjetas ni contraseñas en texto legible.

## Retención y borrado
Los datos de un cliente se guardan mientras siga siendo cliente. Si pide su borrado, se anonimizan sus datos personales y se conservan los cobros sin nombre para la contabilidad.

## Migraciones
Los cambios de la base se versionan con migraciones numeradas. Cada migración se prueba en una base vacía y en una con datos de prueba antes de darla por buena.

## Respaldo
Se respalda el archivo completo de la base una vez al día, con la copia segura de SQLite, y se guarda en otra máquina distinta a la del servicio. La guía de restauración va en entrega.md.
