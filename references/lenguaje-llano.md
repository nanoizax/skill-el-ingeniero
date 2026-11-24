# Cómo escribir para quien no programa

El resumen (`resumen-para-la-persona.md`) y la guía de entrega son para una persona que sabe de su negocio y no de programación. Si no los entiende, no puede aprobar el plan ni publicar el producto. El script revisa dos cosas: que no queden palabras técnicas sin explicar y que las frases no sean enormes.

## Reglas

1. **Frases de 15 a 20 palabras.** Ninguna pasa de 40. Si una frase lleva dos "y", son dos frases.
2. **Habla de lo que la persona podrá hacer**, no de cómo está hecho. "Podrás ver la caja del día", no "se implementa un módulo de cobros".
3. **Una palabra técnica, solo si es necesaria, y explicada en la misma línea**, entre paréntesis o con "o sea".
4. **Números y fechas concretos.** "Entre 7 y 10 dólares al mes (consultado hoy)", no "un costo bajo".
5. **Di qué decide ella o él.** La persona tiene que saber qué le toca hacer y qué no.
6. **Di lo que NO incluye.** Es la parte que evita malentendidos.
7. **Su idioma y su país.** Tuteo y vocabulario de donde vive. Sin comillas angulares, sin rayas largas, sin frases de afiche.

## Reemplazos de uso común

| En vez de | Escribe |
|---|---|
| API | la forma en que dos programas se hablan (API) |
| endpoint | una dirección del sistema a la que se le pide algo |
| backend | la parte del sistema que trabaja por detrás |
| frontend | la parte que ves en la pantalla |
| servidor, hosting | el computador en internet donde vive tu sistema |
| despliegue | publicar el sistema para que otras personas lo usen |
| repositorio, Git | la carpeta donde se guarda la historia del código |
| migración | un cambio ordenado en la base de datos |
| token | una llave temporal que prueba quién eres |
| hash | una forma de guardar contraseñas sin que nadie pueda leerlas |
| dependencias | los programas de otras personas que tu sistema usa |
| webhook | un aviso automático que otro servicio le manda a tu sistema |
| modelo de lenguaje | el programa que redacta las respuestas |
| base de datos | el lugar donde el sistema guarda la información |

## Ejemplo

Mal: "Implementaremos un backend en FastAPI con un endpoint REST que persiste las citas en la base de datos."

Bien: "Haremos la parte del sistema que trabaja por detrás. Cuando un cliente pida una hora, el sistema la guardará en la base de datos, que es el lugar donde se guarda la información."

## Antes de entregarlo

Léelo en voz alta como si se lo dijeras a la persona en un café. Si te trabas, la frase es demasiado larga. Si ella tendría que preguntar "¿y eso qué es?", falta una explicación.
