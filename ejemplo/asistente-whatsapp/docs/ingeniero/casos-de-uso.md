# Casos de uso: Asistente de WhatsApp del consultorio

## Caso 1: Responder una pregunta frecuente
- Actor: paciente
- Objetivo: saber horarios, precios, dirección o tratamientos sin esperar a la secretaria
- Camino normal: escribe su pregunta, el asistente responde con la información cargada por el consultorio
- Errores y límites: pregunta fuera de lo cargado, pregunta médica, mensaje sin sentido
- Criterio de aceptación:
  - Dado que el consultorio cargó el horario, cuando el paciente pregunta a qué hora atienden, entonces el asistente responde con ese horario.
  - Dado una pregunta médica, cuando el paciente la escribe, entonces el asistente no da consejos y ofrece pasar con una persona.
- Prueba que lo cubre: tests/test_preguntas_frecuentes.py
- Etapa de construcción: 1

## Caso 2: Agendar una hora
- Actor: paciente
- Objetivo: reservar una hora libre con la doctora
- Camino normal: pide una hora, el asistente ofrece opciones libres, elige una y recibe la confirmación
- Errores y límites: hora ocupada, hora fuera del horario, paciente que cambia de idea a mitad
- Criterio de aceptación:
  - Dado que la hora de las 11:00 está libre, cuando el paciente la elige, entonces queda reservada y se le confirma.
  - Dado que la hora ya está ocupada, cuando otro paciente la elige, entonces el asistente le ofrece otras horas.
- Prueba que lo cubre: tests/test_agendar_hora.py
- Etapa de construcción: 2

## Caso 3: Pasar la conversación a la secretaria
- Actor: paciente y secretaria
- Objetivo: que una persona tome la conversación cuando el asistente no sabe
- Camino normal: el asistente avisa que pasa la conversación, la secretaria la ve en su lista y responde
- Errores y límites: fuera del horario de la secretaria, conversación que vuelve al asistente
- Criterio de aceptación:
  - Dado que el asistente no sabe responder, cuando el paciente insiste, entonces la conversación se marca para la secretaria y el asistente deja de responder.
  - Dado que es fuera de horario, cuando se pasa la conversación, entonces se le dice al paciente cuándo lo atenderán.
- Prueba que lo cubre: tests/test_traspaso.py
- Etapa de construcción: 3

## Caso 4: Guardar el registro de cada conversación
- Actor: consultorio
- Objetivo: poder revisar qué se dijo y borrarlo cuando corresponde
- Camino normal: cada mensaje queda guardado con fecha; pasado el plazo se borra
- Errores y límites: un paciente pide que borren su historial
- Criterio de aceptación:
  - Dado un paciente que pide borrar sus datos, cuando se procesa la solicitud, entonces su nombre y teléfono se anonimizan.
  - Dado el plazo de retención cumplido, cuando corre la limpieza, entonces las conversaciones viejas se borran.
- Prueba que lo cubre: tests/test_registro.py
- Etapa de construcción: 4
