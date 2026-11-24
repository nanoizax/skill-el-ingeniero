# Etapas de construcción: Asistente de WhatsApp del consultorio

Cada etapa deja algo que ya sirve de punta a punta. El estado real de cada una está en `estado.json`; este archivo explica el orden.

## Etapa 0: esqueleto
Estructura por módulos, marco de pruebas con una prueba que pasa, linter, archivo de ejemplo de variables de entorno, endpoint de salud y registro mínimo.

## Etapa 1: responder preguntas frecuentes
Cubre el caso de uso 1. Al terminarla, el asistente contesta horarios, ubicación y precios desde el archivo de preguntas, y dice que no sabe cuando no sabe.

## Etapa 2: agendar una hora
Cubre el caso de uso 2. Al terminarla, un paciente puede pedir una hora libre y recibir la confirmación.

## Etapa 3: pasar la conversación a la secretaria
Cubre el caso de uso 3. Al terminarla, las urgencias y las peticiones de una persona cortan al asistente y avisan a la secretaria.

## Etapa 4: registro y borrado de conversaciones
Cubre el caso de uso 4. Al terminarla, cada conversación se guarda con lo mínimo y se puede borrar a pedido.

## Orden y por qué
Primero lo que sostiene el resto (esqueleto) y lo que más seguridad exige (pasar a una persona), luego lo que el paciente usa todos los días. El registro va al final porque depende de lo que las demás etapas guardan.