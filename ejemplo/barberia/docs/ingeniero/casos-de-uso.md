# Casos de uso: Barbería Don Mario

Cada caso de uso es algo que una persona hace con el producto. Cada uno lleva su criterio de aceptación y la prueba que lo cubre.

## Caso 1: Agendar una cita
- Actor: cliente o recepcionista
- Objetivo: reservar una hora con un barbero para un servicio
- Camino normal: elige barbero, servicio, día y hora libre; confirma con su nombre y teléfono
- Errores y límites: hora ocupada, hora pasada, fuera del horario de atención, cita que termina después del cierre
- Criterio de aceptación:
  - Dado que el barbero está libre a las 15:00, cuando el cliente agenda a las 15:00, entonces la cita queda confirmada.
  - Dado que el barbero ya tiene una cita de 15:00 a 15:30, cuando alguien agenda a las 15:15 con él, entonces el sistema la rechaza por ocupada.
  - Dado que una cita termina justo cuando empieza otra, cuando se agenda, entonces se permite.
  - Dado que la hora pedida ya pasó, cuando se agenda, entonces se rechaza.
- Prueba que lo cubre: tests/test_agendar_cita.py
- Etapa de construcción: 1

## Caso 2: Cancelar o mover una cita
- Actor: cliente o recepcionista
- Objetivo: liberar o cambiar una hora ya reservada
- Camino normal: busca su cita, la cancela o elige otra hora libre
- Errores y límites: cancelar una cita ajena, mover a una hora ocupada, mover una cita ya atendida
- Criterio de aceptación:
  - Dado una cita confirmada de la persona, cuando la cancela, entonces la hora queda libre.
  - Dado una cita de otra persona, cuando alguien intenta cancelarla, entonces el sistema lo impide.
- Prueba que lo cubre: tests/test_gestion_de_citas.py
- Etapa de construcción: 3

## Caso 3: Ver la agenda del día
- Actor: barbero
- Objetivo: saber qué citas tiene hoy y a qué hora
- Camino normal: abre su agenda y ve sus citas ordenadas por hora
- Errores y límites: un barbero no ve las citas de otro; día sin citas
- Criterio de aceptación:
  - Dado que el barbero tiene tres citas hoy, cuando abre su agenda, entonces ve las tres en orden de hora.
  - Dado otro barbero con citas, cuando el primero abre su agenda, entonces no ve las del otro.
- Prueba que lo cubre: tests/test_agenda.py
- Etapa de construcción: 4

## Caso 4: Registrar el cobro de una cita
- Actor: recepcionista o barbero
- Objetivo: dejar anotado cuánto se cobró y con qué medio
- Camino normal: abre la cita atendida, indica monto y medio de pago, confirma
- Errores y límites: monto cero o negativo, cobrar dos veces la misma cita, medio no válido
- Criterio de aceptación:
  - Dado una cita atendida, cuando se registra un cobro de 12000 pesos en efectivo, entonces queda guardado.
  - Dado una cita ya cobrada, cuando se intenta cobrar otra vez, entonces el sistema lo rechaza.
- Prueba que lo cubre: tests/test_cobros.py
- Etapa de construcción: 5

## Caso 5: Cierre de caja del día
- Actor: dueño
- Objetivo: ver cuánto entró en el día, por medio de pago y por barbero
- Camino normal: abre el cierre del día y ve los totales
- Errores y límites: día sin cobros, suma que no cuadra por redondeo
- Criterio de aceptación:
  - Dado tres cobros de 10000, 12000 y 8000 pesos, cuando se pide el cierre, entonces el total es 30000 pesos.
  - Dado un día sin cobros, cuando se pide el cierre, entonces el total es cero.
- Prueba que lo cubre: tests/test_caja.py
- Etapa de construcción: 6
