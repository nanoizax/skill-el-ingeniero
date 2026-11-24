# Nuestras skills

Todas son de Soy Tegno, públicas y gratuitas, en `https://github.com/nanoizax/<nombre>`. El ingeniero **las prioriza**: si están instaladas, las usa en la etapa que corresponde. Si falta alguna, lo dice, da el enlace para instalarla (la persona decide) y sigue con una versión mínima de lo que esa skill haría.

Para ver cuáles hay instaladas: `ingeniero.py skills`. No instala nada.

## Qué skill entra en cada etapa

| Etapa | Skill | Repositorio | Para qué | Versión mínima si falta |
|---|---|---|---|---|
| Plan | `arquitectura-backend` | `skill-arquitectura-backend` | Estructura del código del servidor: capas, módulos, contrato de la API, errores, paginación, autenticación. | Monolito modular; cada módulo con su carpeta; controladores delgados, lógica en casos de uso, acceso a datos aparte; errores con un formato único. |
| Plan | `decisiones-de-arquitectura` | `skill-decisiones-de-arquitectura` | Una nota corta por cada decisión importante (qué se eligió, qué se descartó y por qué). | Un archivo por decisión en `docs/decisiones/` con contexto, decisión y consecuencias. |
| Construcción | `pruebas-de-la-actividad` | `skill-pruebas-de-la-actividad` | Pruebas de cada etapa, comprobar que no se rompió lo anterior y veredicto. | Pruebas unitarias antes del código, correr toda la suite, y no pasar de etapa si algo falla. |
| Construcción | `commits-limpios` | `skill-commits-limpios` | Commits con título claro y autor persona, sin marcas de herramienta. | Un commit por etapa, con título que diga qué se hizo. Solo si la persona lo pide. |
| Construcción y salida | `documentacion-viva` | `skill-documentacion-viva` | **La memoria del proyecto**: documentación al día en una rama aparte, para retomar sin releer el código. | Mantener `docs/ingeniero/estado.json` y un resumen al cerrar cada etapa. |
| Salida | `qa` | `skill-qa` | QA independiente y veredicto de salida GO o NO-GO. | Recorrer los casos de uso a mano contra sus criterios de aceptación. |
| Salida | `documentacion` | `skill-documentacion` | Manual de usuario y documentación técnica completa. | Una guía corta para la persona dueña. |
| Cualquier texto | `limpieza-de-texto` | `skill-limpieza-de-texto` | Limpiar el texto que produjo un modelo antes de entregarlo. | Releer sin rayas largas, comillas raras ni marcadores sin rellenar. |
| Al cerrar | `repaso-tecnico` | `skill-repaso-tecnico` | Repaso corto de lo que se usó y dónde puede fallar. | Tres líneas al final de cada etapa. |

## Reglas de uso

- **La skill propia manda sobre una de terceros** que haga lo mismo.
- **La memoria del proyecto es `documentacion-viva`** cuando está instalada: al cerrar cada etapa se le pide que actualice. Si no está, `estado.json` y el historial de `docs/ingeniero/` son la memoria.
- Las skills propias que son de este equipo y no son públicas (por ejemplo las de base de datos) no se asumen: se usa la guía de este repositorio.
- Si el proyecto es de otra área (video, redes, diseño), existen otras skills nuestras en la misma organización; se mencionan a la persona como opcionales, no se asumen.
