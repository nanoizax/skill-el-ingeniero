# Cuando el proyecto ya existe

Es el caso de quien ya construyó algo, a menudo con una herramienta de inteligencia artificial, y quiere saber si aguanta en producción. No se le hace la entrevista de cero: el proyecto ya contesta casi todo.

## El orden

1. `iniciar --existente --nombre "<proyecto>" --perfil otro`. El script lee las dependencias, los archivos de prueba y los comandos, y propone perfil, banderas (pagos, cuentas, base de datos, WhatsApp, IA, archivos, interfaz) y comandos. Todo es **sugerencia**: se le muestra a la persona en lenguaje llano y se corrige con `datos` y `comandos`.
2. Una entrevista **corta, solo de lo que el código no dice**: qué quiere lograr, quién lo usa, qué pasaría si falla un día, quién lo mantiene. Va al brief.
3. `verificar` y `puntaje`: la foto real de hoy, sin juzgar.
4. `rescate`: lo que falta, agrupado por categoría y de lo más grave a lo menos grave. Con `--crear-etapas` cada grupo pasa a ser una etapa de construcción con su contrato (los ítems que se comprueban solos entran como `item:ID`).
5. Se trabaja como siempre: `siguiente --iniciar`, pruebas primero, `etapa-cerrar`.

## Reglas

- No se reescribe lo que funciona. Se agregan pruebas alrededor de lo que existe antes de cambiarlo.
- No se inventa una aprobación: en este modo el plan es el de rescate y la persona lo aprueba con sus palabras igual que en un proyecto nuevo.
- Los hallazgos graves (claves escritas en el código, datos de personas sin protección) se dicen primero y con calma, con el arreglo al lado.
- Si el historial de Git contiene secretos, se avisa que quitarlos del código no basta: hay que cambiar esas claves por unas nuevas, y eso lo hace la persona.
