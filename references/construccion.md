# La construcción

Solo empieza cuando la persona aprobó el plan (`avanzar aprobado` con sus palabras). Se construye por **etapas verticales**: cada una deja algo que ya sirve de punta a punta, aunque sea pequeño. No se construye "primero toda la base de datos y luego toda la pantalla".

## La etapa 0: el esqueleto

Antes de la primera función útil, el proyecto tiene que poder **crecer sin romperse**:

- Repositorio con la estructura del plan (módulos, capas) y un archivo `README` con cómo instalar y ejecutar.
- El marco de pruebas funcionando, con **una** prueba que pasa.
- Linter y formateo configurados.
- Archivo `.env.example` (sin valores reales) y `.env` fuera de Git.
- Un endpoint o página de **salud** que responde "ok".
- Migraciones de base de datos versionadas, si hay base de datos.
- El archivo de dependencias con versiones fijas (lockfile).
- Una automatización simple que corre pruebas y linter en cada cambio (CI), si la persona usa un repositorio en línea.

## Etapas siguientes

Ordénalas por **valor y riesgo**: primero lo que sostiene el resto (cuentas de usuario, datos centrales), luego lo que la persona usa todos los días. Una etapa no debería pasar de medio día de trabajo: si es más grande, se parte. Se registran con `etapa-agregar`.

Ejemplo (barbería): 0 esqueleto, 1 cuentas y roles, 2 servicios y precios, 3 agendar una cita, 4 cancelar y mover, 5 registrar el cobro, 6 cierre de caja del día, 7 recordatorios.

## El contrato de cada etapa

Antes de construir una etapa se fija su contrato, y el script no la deja cerrar sin cumplirlo:

- **Hecho cuando:** criterios concretos que alguien pueda comprobar ("el cliente recibe un 409 si la hora ya está ocupada"). Frases como "funciona bien" o "se ve profesional" se rechazan.
- **Cómo se verifica:** uno o más comandos (`etapa-contrato --verificar "<comando>"`). Puede ser `item:P2`, un ítem del checklist que se comprueba solo. Si de verdad no hay comando, se escribe por qué (`--sin-verificacion`) y la evidencia la da una persona.
- **Punto de retorno:** al cerrarse la etapa, el script sugiere `git tag etapa-NN-nombre`. Solo se crea si la persona usa Git y lo pide.

Si una sesión se corta con una etapa a medias, `siguiente` la retoma: muestra el contrato y corre la verificación para saber cómo quedó, y se continúa desde ahí en vez de empezar de cero.

## El ciclo de cada etapa

0. `siguiente --iniciar` muestra la etapa que toca y la deja en curso.
1. **Casos de uso de la etapa** (de `casos-de-uso.md`), con su criterio de aceptación: "Dado / Cuando / Entonces".
2. **Pruebas primero:** escribe las pruebas de esos casos (el camino normal, un error y un límite) y míralas fallar.
3. **Código mínimo** que las hace pasar, en la estructura del plan. Nada de funciones "por si acaso".
4. **Toda la suite.** Si algo que ya funcionaba se rompió, se arregla antes de seguir. Con `pruebas-de-la-actividad`, si está instalada, se hace además la prueba de sensibilidad y el veredicto.
5. **Revisión de seguridad de la etapa:** entradas validadas, cada persona ve solo lo suyo, ningún secreto en el código, nada sensible en los registros.
6. **Documentar:** actualiza `docs/ingeniero/` y, si hay `documentacion-viva`, pídele que ponga al día la documentación.
7. **Cerrar la etapa:** `etapa-cerrar --id N`. Corre los comandos del contrato y la cierra solo si pasan; la evidencia queda escrita por el script. Si la etapa no tiene comandos, se agrega `--evidencia "<qué se vio, concreto>"`.
8. **Decírselo a la persona en dos líneas**, sin jerga: qué ya puede hacer y qué viene.
9. **Commit solo si la persona lo pide**, y con `commits-limpios` si está.

## Reglas

- **No se salta una prueba para avanzar.** Si una prueba falla, se arregla el código o se discute la prueba con la persona; no se borra.
- **No se agrega nada fuera del plan** sin decirlo: un cambio de alcance se anota en el brief y se avisa.
- **No se inventan datos reales** en las pruebas: datos ficticios y claramente falsos. Si un dato de prueba parece una clave (por ejemplo una contraseña de ejemplo), se marca esa línea con el comentario `pragma: allowlist secret` para que el escáner la ignore; no se desactiva la revisión de nada más.
- **Una decisión importante nueva** (cambiar una librería, el esquema de la base) se anota con `decisiones-de-arquitectura`.
- Si algo no se puede probar con una prueba automática, se anota **cómo se verificó** a mano.
- **Al terminar todas las etapas**, `avanzar salida`.
