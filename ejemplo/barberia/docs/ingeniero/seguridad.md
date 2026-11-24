# Seguridad: Barbería Don Mario

## Datos personales
- Qué se guarda: nombre y teléfono de los clientes, y el historial de sus citas.
- Para qué: agendar las citas y avisar si hay un cambio.
- Cuánto tiempo: mientras la persona siga siendo cliente de la barbería.
- Cómo se borra: a pedido de la persona se anonimizan sus datos personales; los cobros se conservan sin nombre.
- Normativa aplicable: Ley 21.719 de Chile, que según las fuentes entra en vigencia el 2026-12-01, aunque hay un proyecto para postergarla (consultado el 2026-11-24). Se deja pendiente confirmar el estado del proyecto con un asesor legal.

## Cuentas y permisos
Cada persona del equipo inicia sesión con correo y contraseña. Las contraseñas se guardan con un algoritmo de hash recomendado. Cada barbero ve solo sus citas y el dueño ve todo. Los clientes ven únicamente sus citas. Hay límite de intentos de inicio de sesión.

## Secretos
Las claves viven en variables de entorno, nunca en el código ni en Git. El archivo .env no se versiona y el repositorio trae un .env.example solo con los nombres.

## Pagos
El sistema solo registra monto y medio de pago. No procesa pagos ni guarda datos de tarjetas.

## Riesgos principales y cómo se reducen
- Ver citas de otra persona: autorización por objeto con pruebas que lo intentan y fallan.
- Pérdida de datos: respaldo diario en otra máquina y restauración probada.
- Abuso del formulario de agendar: límite de solicitudes por dirección.
