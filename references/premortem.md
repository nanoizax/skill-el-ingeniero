# El pre-mortem

Antes de pedir la aprobación del plan se imagina que **pasaron seis meses y el proyecto fracasó**, y se escribe por qué. Es más fácil ver los riesgos mirando hacia atrás desde un fracaso inventado que preguntándose qué podría salir mal.

## Qué se escribe en `docs/ingeniero/premortem.md`

1. **Qué pasó** (mínimo 30 palabras): la historia del fracaso, con las palabras de la persona.
2. **Los riesgos que sobrevivieron** (mínimo 3). Cada uno con: por qué podría pasar y **qué haremos** para evitarlo, algo concreto, no "estar atentos".
3. **Los ocho ángulos revisados**, una línea cada uno con una respuesta real:
   1. Personas: ¿alguien que debía usarlo no lo usó, o lo usó mal?
   2. Datos: ¿se pierden, se mezclan o se ven por quien no debe?
   3. Dinero: ¿cuesta más de lo previsto o cobra mal?
   4. Seguridad: ¿qué pasa si alguien malintencionado lo prueba?
   5. Crecimiento: ¿qué se rompe con diez veces más uso?
   6. Mantenimiento: ¿quién lo arregla cuando yo no esté?
   7. Dependencias: ¿qué pasa si un servicio externo cambia, sube de precio o cae?
   8. Alcance: ¿qué se prometió que no está en la primera versión?

## Reglas

- Una respuesta como "nada" o "no aplica" sin razón no cuenta.
- Lo que surja y cambie el plan se anota en el plan antes de pedir la aprobación.
- El script lo exige: sin pre-mortem completo no se pasa al resumen.
