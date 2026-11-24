# 0003: SQLite en lugar de PostgreSQL

Estado: aceptada, 2026-11-24. Reemplaza lo previsto en el plan original.

## Contexto
La barbería tiene unas 40 citas al día, un solo servicio y una persona que lo mantiene. Un servidor de base de datos aparte es una pieza más que operar, respaldar y pagar.

## Decisión
Se usa SQLite, que viene con Python y guarda todo en un archivo. Las reglas que garantizan que no haya citas cruzadas se aplican dentro de una transacción.

## Alternativas descartadas
- PostgreSQL: más potente, pero innecesario para este volumen y con un costo mensual extra.

## Consecuencias
Publicar y respaldar es más simple: un servicio y un archivo. Si el negocio crece a muchas sedes o a mucho tráfico, habrá que migrar a PostgreSQL; por eso el acceso a datos va detrás de una interfaz.
