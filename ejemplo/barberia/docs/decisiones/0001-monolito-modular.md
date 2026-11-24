# 0001: Monolito modular en lugar de varios servicios

Estado: aceptada, 2026-11-24.

## Contexto
Una sola barbería, unas 40 citas por día y una persona que mantendrá el sistema.

## Decisión
Una sola aplicación dividida en módulos (citas, cobros, cuentas), cada uno con sus capas.

## Alternativas descartadas
- Varios servicios separados: más piezas que operar y fallar para un volumen pequeño.

## Consecuencias
Más simple de publicar y respaldar. Si algún día crece, un módulo puede separarse.
