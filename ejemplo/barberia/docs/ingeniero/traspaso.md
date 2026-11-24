# Traspaso: Barbería Don Mario

Este documento es autosuficiente: una instancia nueva, sin ningún contexto, puede construir el proyecto leyéndolo. Todo lo que sigue sale de `docs/ingeniero/` y de `estado.json`; si algo no coincide, manda lo que diga ese estado.

## Reglas que no se negocian

1. Pruebas primero: escribe las pruebas de la etapa, míralas fallar y recién después escribe el código mínimo que las hace pasar.
2. Una etapa se cierra solo cuando sus comandos de verificación pasan (`ingeniero.py etapa-cerrar`), nunca porque se diga que terminó.
3. Ningún secreto escrito en el código: las claves salen de variables de entorno, y `.env` no se sube a Git. Los datos de prueba que parezcan claves llevan en su línea el comentario `pragma: allowlist secret`.
4. No se agrega nada fuera de la lista de etapas ni de "Qué se construye". Un cambio de alcance se avisa a la persona.
5. Si una prueba falla, se arregla el código o se discute la prueba con la persona. No se borra ni se desactiva para avanzar.
6. No se despliega, no se compra, no se crean cuentas a nombre de la persona y no se piden claves. El envío a producción lo hace ella.
7. Commit y push solo si la persona lo pide.
8. Si falta algo para decidir, se pregunta. No se inventa.

## Qué se construye

"Dejar de anotar las citas en un cuaderno y saber cuánta plata entró cada día sin sumar a mano." Don Mario quiere un sistema para agendar las citas de su barbería y llevar la contabilidad diaria de lo que se cobra.

**Primera versión, imprescindible:**

- Que un cliente pueda agendar una cita con un barbero en un horario libre.
- Que no se pueda agendar dos veces la misma hora con el mismo barbero.
- Que cada barbero vea su agenda del día.
- Que se registre el cobro de cada cita atendida (efectivo, tarjeta o transferencia).
- Que Don Mario vea el cierre de caja del día.

**Fuera de alcance (no se construye):**

- Pagos en línea con tarjeta dentro de la página.
- Aplicación móvil propia.
- Inventario de productos y facturación electrónica.

## Pila elegida

Opción B: El sobrino que lo mantendrá sabe Python.

- Lenguaje y versión: Python 3.12 (FastAPI exige 3.10 o más; verificado el 2026-11-24)
- Framework: FastAPI, con versiones fijadas en requirements.txt
- Base de datos: SQLite, que viene incluida en Python y guarda todo en un solo archivo. Los cambios de la base se versionan en archivos SQL numerados. El acceso a los datos va detrás de interfaces, con un adaptador en memoria para las pruebas y uno de SQLite para producción. PostgreSQL queda como camino de crecimiento si el negocio se multiplica.
- Pruebas y calidad: pytest, httpx para probar la API, ruff como linter
- Servicios externos: ninguno en la primera versión (sin pagos en línea ni WhatsApp)

## Estructura del código

Monolito modular. Cada módulo es una carpeta bajo app/ con sus propias capas:
- app/citas: agendar, cancelar, mover y ver la agenda.
- app/cobros: registrar cobros y cierre de caja.
- app/cuentas: personas que inician sesión y sus permisos.
- app/compartido: configuración, errores comunes y reloj.
Dentro de cada módulo: dominio (reglas y errores, sin depender de nada), casos de uso (una acción por clase), repositorio (la interfaz y sus adaptadores) y api (las rutas HTTP). Las dependencias van hacia adentro: la api conoce los casos de uso, los casos de uso conocen el dominio, el dominio no conoce a nadie.

## Reglas de los datos y de la seguridad

- El dinero se guarda en pesos enteros, sin decimales ni números de coma flotante.
- Un barbero no puede tener dos citas confirmadas que se solapen en el tiempo.
- Una cita solo puede cobrarse una vez y solo si fue atendida.
- Las fechas se guardan en hora universal.

- Ver citas de otra persona: autorización por objeto con pruebas que lo intentan y fallan.
- Pérdida de datos: respaldo diario en otra máquina y restauración probada.
- Abuso del formulario de agendar: límite de solicitudes por dirección.

## Etapas

### Etapa 0: Esqueleto (cerrada)

**Hecho cuando:**
- La prueba de salud responde ok y el linter no encuentra errores

**Cómo se verifica:**
- `python -m pytest -q tests/test_salud.py`
- `python -m ruff check .`

### Etapa 1: Agendar una cita (cerrada)

**Hecho cuando:**
- El cliente recibe la cita confirmada con su hora y su barbero
- El cliente recibe un rechazo si la hora ya está ocupada, pasó o cae fuera del horario

**Cómo se verifica:**
- `python -m pytest -q tests/test_agendar_cita.py tests/test_api_citas.py`

### Etapa 2: Cuentas y roles (cerrada)

**Hecho cuando:**
- Cada rol ve y cambia solo lo que le corresponde
- La contraseña se guarda con hash y nunca aparece en una respuesta

**Cómo se verifica:**
- `python -m pytest -q tests/test_cuentas_casos_de_uso.py tests/test_cuentas_seguridad.py tests/test_api_cuentas.py`

### Etapa 3: Cancelar y mover una cita (cerrada)

**Hecho cuando:**
- La persona cancela su cita y la hora queda libre
- Nadie puede cancelar ni mover la cita de otra persona

**Cómo se verifica:**
- `python -m pytest -q tests/test_gestion_de_citas.py tests/test_carreras_de_estado.py`

### Etapa 4: Agenda del día del barbero (cerrada)

**Hecho cuando:**
- Cada barbero ve su agenda del día ordenada por hora y sin las citas de otro

**Cómo se verifica:**
- `python -m pytest -q tests/test_agenda.py`

### Etapa 5: Registrar cobros (cerrada)

**Hecho cuando:**
- El cobro de una cita atendida queda registrado con su monto y su medio de pago
- No se puede cobrar dos veces la misma cita

**Cómo se verifica:**
- `python -m pytest -q tests/test_cobros.py`

### Etapa 6: Cierre de caja del día (cerrada)

**Hecho cuando:**
- El cierre de caja del día suma los cobros y coincide con el detalle

**Cómo se verifica:**
- `python -m pytest -q tests/test_caja.py`

### Etapa 7: Base de datos PostgreSQL, migraciones y respaldo (cerrada)

**Hecho cuando:**
- El respaldo se restaura y los datos coinciden con los originales
- Las migraciones corren de cero y se pueden repetir sin romper nada

**Cómo se verifica:**
- `python -m pytest -q tests/test_respaldo.py tests/test_migraciones.py`

## Cómo trabajar una etapa

1. `ingeniero.py --repo <proyecto> siguiente --iniciar` muestra la etapa que sigue y la deja en curso.
2. Escribe las pruebas, míralas fallar, escribe el código mínimo, corre toda la suite.
3. `ingeniero.py --repo <proyecto> etapa-verificar --id N` corre los comandos del contrato sin cerrar la etapa.
4. `ingeniero.py --repo <proyecto> etapa-cerrar --id N` la cierra si la verificación pasa.
5. Si la sesión se corta, `siguiente` retoma la etapa en curso y comprueba cómo quedó.
6. Al terminar todas: `verificar`, `puntaje` y una revisión independiente (la hace alguien que no construyó).

## Comandos del proyecto

- pruebas: `python -m pytest -q`
- lint: `python -m ruff check .`
- build: `python -m compileall -q app`
- auditoria: `python -m pip_audit -r requirements.txt`

## Dónde leer más

- `docs/ingeniero/casos-de-uso.md`: los casos de uso con su criterio de aceptación.
- `docs/ingeniero/arquitectura.md` y `modelo-de-datos.md`: el diseño completo.
- `docs/ingeniero/seguridad.md` y `premortem.md`: los riesgos y qué se hará con cada uno.
- `docs/ingeniero/entrega.md`: la guía de entrega para la persona.
