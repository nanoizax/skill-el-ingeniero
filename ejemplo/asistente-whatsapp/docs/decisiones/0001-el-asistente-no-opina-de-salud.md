# 0001: El asistente no opina de salud

Estado: aceptada, 2026-11-24.

## Contexto
Un asistente que redacta respuestas con un modelo de lenguaje puede inventar información. En un consultorio, un consejo médico inventado es un riesgo para el paciente.

## Decisión
El asistente solo contesta con información cargada por el consultorio. Ante cualquier pregunta médica, no responde y ofrece pasar con una persona.

## Alternativas descartadas
- Dejar que el modelo responda libremente: más natural, pero con riesgo inaceptable en salud.

## Consecuencias
Las respuestas son menos flexibles. A cambio, lo que dice el asistente siempre se puede rastrear a algo que el consultorio escribió.
