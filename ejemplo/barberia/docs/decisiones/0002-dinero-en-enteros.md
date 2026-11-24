# 0002: El dinero se guarda en pesos enteros

Estado: aceptada, 2026-11-24.

## Contexto
La moneda es el peso chileno, que no usa centavos. Los números de coma flotante producen errores de redondeo al sumar.

## Decisión
Todos los montos son enteros en pesos. Nunca se usan decimales ni números de coma flotante para dinero.

## Alternativas descartadas
- Tipos decimales: necesarios solo para monedas con centavos.

## Consecuencias
El cierre de caja siempre cuadra. Si el negocio cambia de moneda, habrá que migrar a centavos.
