# Plan de pruebas: Barbería Don Mario

## Estrategia
Pruebas unitarias para las reglas del dominio y los casos de uso, usando un repositorio en memoria. Pruebas de la API con httpx para comprobar los códigos de respuesta y los mensajes de error. Una prueba de punta a punta del flujo principal (agendar, atender, cobrar, cerrar caja) cuando existan las etapas correspondientes. Lo visual se revisa a mano.

## Por caso de uso
- Agendar una cita: camino normal, hora ocupada, hora pasada, fuera de horario, cita que termina justo cuando empieza otra.
- Cancelar o mover: cancelar la propia, intentar cancelar la ajena, mover a hora ocupada.
- Agenda del día: ordenada por hora, sin ver las de otro barbero.
- Cobro: monto válido, doble cobro, monto cero.
- Cierre de caja: suma correcta y día vacío.

## Datos de prueba
Datos ficticios claramente falsos: clientes "Cliente Uno" y teléfono 111111111. Se crean dentro de cada prueba y no se comparten.

## Qué no se prueba y por qué
- La apariencia de la página: se revisa a mano con la persona.
- El rendimiento con miles de citas: la barbería tiene unas 40 al día.

## Cómo se ejecutan
python -m pytest -q para las pruebas y python -m ruff check . para el linter.
