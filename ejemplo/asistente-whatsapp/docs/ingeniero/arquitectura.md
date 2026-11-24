# Arquitectura: Asistente de WhatsApp del consultorio

## Opción elegida y por qué
Opción A de la investigación: la conexión oficial de WhatsApp con un servicio propio. La persona la eligió porque quiere usar WhatsApp de forma permitida y que los datos de salud queden con ella.

## Tecnología
- Lenguaje y versión: Python 3.12 (verificado el 2026-11-24 que lo soportan las herramientas elegidas).
- Framework: FastAPI para recibir los avisos de WhatsApp, con versiones fijadas en el archivo de dependencias.
- Base de datos: SQLite para el volumen previsto (150 mensajes por día), con migraciones numeradas; PostgreSQL queda como camino de crecimiento.
- Modelo de lenguaje: un proveedor con contrato y límites de gasto, usado solo para redactar respuestas sobre información cargada por el consultorio.
- Servicios externos: la conexión oficial de WhatsApp (Meta) y el proveedor del modelo de lenguaje.

## Estructura del código
Monolito modular con tres módulos bajo app/: conversaciones (recibir, responder, traspasar), citas (agendar y confirmar) y registro (guardar y borrar). Cada módulo tiene dominio (las reglas), casos de uso (una acción por clase), repositorio y api. El modelo de lenguaje y WhatsApp se usan a través de interfaces, para poder probar todo con versiones falsas y sin gastar.

## Decisiones importantes
- El asistente solo contesta con información cargada por el consultorio y nunca da consejos médicos (docs/decisiones/0001-el-asistente-no-opina-de-salud.md).
- Todo acceso a WhatsApp y al modelo de lenguaje va detrás de una interfaz.

## Cómo se comunican las partes
El paciente escribe a WhatsApp, Meta avisa al servicio, el servicio decide la respuesta con sus reglas y el modelo de lenguaje, guarda la conversación y contesta por la misma conexión.

## Despliegue previsto
Un servicio web con un disco persistente para la base, en un proveedor que la doctora elija. La guía completa va en entrega.md. El ingeniero no publica nada.

## Riesgos técnicos principales
- Respuestas inventadas sobre salud: reglas estrictas, lista de temas prohibidos y traspaso a una persona.
- Costo descontrolado del modelo de lenguaje: límite de mensajes por paciente y por día.
- Instrucciones maliciosas escritas por un paciente: el asistente nunca ejecuta acciones por lo que diga un mensaje sin validarlo con reglas fijas.
