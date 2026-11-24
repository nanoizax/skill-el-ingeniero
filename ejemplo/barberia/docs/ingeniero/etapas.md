# Etapas de construcción: Barbería Don Mario

Cada etapa deja algo que ya sirve de punta a punta. El estado real de cada una está en `estado.json`; este archivo explica el orden.

## Etapa 0: esqueleto
Estructura por módulos y capas, marco de pruebas, revisor de estilo, ejemplo de variables de entorno, punto de salud y automatización de pruebas.

## Etapa 1: agendar una cita
El cliente reserva una hora libre; no se aceptan horas ocupadas, pasadas ni fuera del horario.

## Etapa 2: cuentas y roles
Dueño, recepción, barbero y cliente, con contraseñas guardadas de forma segura, sesiones que vencen y bloqueo tras varios intentos fallidos.

## Etapa 3: cancelar y mover una cita
Cada persona opera solo lo que le corresponde; cancelar libera la hora.

## Etapa 4: agenda del día del barbero
Cada barbero ve solo su agenda; recepción y dueño ven todas; el cliente ve sus propias citas.

## Etapa 5: registrar cobros
Solo sobre citas atendidas, en pesos enteros, con un solo cobro por cita.

## Etapa 6: cierre de caja del día
El dueño ve el total, por medio de pago y por barbero.

## Etapa 7: base de datos SQLite, migraciones y respaldo
Los datos se guardan en un archivo, con cambios versionados, reserva segura aunque lleguen solicitudes a la vez, y respaldo y restauración probados.

## Orden y por qué
Primero lo que sostiene el resto (estructura y cuentas), luego lo que se usa todos los días (citas, agenda), después el dinero (cobros y caja) y al final la persistencia, que se puso detrás de interfaces desde el principio para no rehacer nada.
