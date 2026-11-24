# Plan de pruebas: Asistente de WhatsApp del consultorio

## Estrategia
Pruebas unitarias de las reglas y de cada caso de uso, usando versiones falsas de WhatsApp y del modelo de lenguaje, de modo que ninguna prueba envíe mensajes reales ni gaste dinero. Pruebas de la conexión con datos de ejemplo de los avisos de Meta. Antes de publicar, una revisión a mano con una lista de mensajes difíciles: preguntas médicas, insultos, intentos de engañar al asistente.

## Por caso de uso
- Preguntas frecuentes: respuesta con información cargada, pregunta fuera de lo cargado, pregunta médica.
- Agendar: hora libre, hora ocupada, fuera de horario.
- Traspaso: asistente que no sabe, fuera del horario de la secretaria.
- Registro: guardar un mensaje, borrar por solicitud, limpieza por plazo.

## Datos de prueba
Pacientes ficticios claramente falsos, con teléfonos de ejemplo. Nunca conversaciones reales.

## Qué no se prueba y por qué
- La calidad de redacción del modelo de lenguaje: se revisa a mano con la doctora.
- El comportamiento real de WhatsApp en producción: depende de Meta.

## Cómo se ejecutan
python -m pytest -q para las pruebas y python -m ruff check . para el estilo.
