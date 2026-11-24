# Pre-mortem: Barbería Don Mario

## Qué pasaría si fracasa en seis meses

Seis meses después, Don Mario volvió al cuaderno. Un sábado dos clientes llegaron a la misma hora con el mismo barbero porque el sistema dejó agendar dos citas encimadas, y desde ese día los barberos dejaron de mirar la pantalla. Además, el servidor se apagó una noche, no había una copia reciente de las citas y hubo que reconstruir la semana de memoria. El sobrino que lo mantiene no pudo arreglarlo porque nadie le explicó cómo se restaura.

## Los riesgos que sobrevivieron

### Riesgo 1: dos citas a la misma hora
- Por qué podría pasar: dos personas agendan a la vez y ambas ven la hora libre.
- Qué haremos: la regla de hora ocupada se comprueba al guardar, dentro de la misma operación, y hay una prueba de carreras de estado que lo intenta en paralelo.

### Riesgo 2: pérdida de las citas y los cobros
- Por qué podría pasar: falla el disco o se borra la base sin una copia aparte.
- Qué haremos: respaldo diario en otra máquina, y una prueba que respalda, borra y restaura comparando el resultado.

### Riesgo 3: datos de clientes a la vista de quien no debe
- Por qué podría pasar: un barbero ve las citas o los teléfonos de otro, o una clave queda escrita en el código.
- Qué haremos: cada barbero solo ve su agenda (con prueba), las claves salen del entorno y el escáner de secretos corre en cada verificación.

### Riesgo 4: nadie sabe mantenerlo
- Por qué podría pasar: el sobrino se va o se olvida de cómo funciona.
- Qué haremos: README con instalar y ejecutar, guía de entrega para Don Mario y estructura por módulos con nombres en español.

## Los ocho ángulos revisados

- Personas: los barberos usan solo la agenda del día, con una pantalla corta y sin menús escondidos.
- Datos: nombre y teléfono del cliente son los únicos datos personales, hay borrado a pedido y no se registran en los logs.
- Dinero: el cobro registra el monto y el medio de pago, sin pasarela en línea en la primera versión, así que no hay tarjetas guardadas.
- Seguridad: contraseñas con hash, cada rol solo accede a lo suyo y las entradas se validan en el servidor.
- Crecimiento: una barbería con cuatro sillas cabe de sobra en SQLite, y el límite está anotado en la arquitectura.
- Mantenimiento: el sobrino conoce Python, las dependencias van con versión fija y hay CI con pruebas y linter.
- Dependencias: ningún servicio externo es imprescindible el primer día, no hay mensajes ni pagos en línea.
- Alcance: recordatorios por WhatsApp y pagos en línea quedaron fuera de la primera versión y están dichos en el brief.
