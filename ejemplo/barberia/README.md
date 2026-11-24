# Barbería Don Mario

Sistema para agendar las citas de una barbería y llevar el cierre de caja del día. Hecho con Python y FastAPI, con una base SQLite.

## Qué hace
- **Cuentas y roles:** dueño, recepción, barbero y cliente. Los clientes se registran solos; el personal lo crea el dueño. La sesión se inicia con correo y contraseña y dura 8 horas. Tras 5 intentos fallidos con un correo, queda bloqueado 15 minutos. Además hay un límite por dirección: 10 registros por hora y 30 intentos de inicio de sesión cada 15 minutos.
- **Citas:** el cliente agenda para sí mismo (con un máximo de 3 citas confirmadas por venir; recepción y dueño no tienen ese tope); recepción y dueño agendan para cualquier cliente; el barbero no agenda. El barbero y el cliente indicados deben existir con su rol. Las citas duran entre 1 y 480 minutos y se agendan con hasta un año de anticipación. Se pueden cancelar, mover y marcar como atendidas (esto último solo desde la hora de inicio de la cita), según el rol. No deja agendar dos veces la misma hora con el mismo barbero (ni aunque dos solicitudes lleguen a la vez), ni fuera del horario (lunes a sábado de 10:00 a 20:00), ni en el pasado.
- **Agenda:** cada barbero ve solo la suya; recepción y dueño ven la de un barbero o la de todos. Cada cliente ve sus propias citas. Las horas se guardan en UTC y se muestran en la zona del negocio (America/Santiago).
- **Cobros:** solo sobre citas atendidas, en pesos enteros, con efectivo, tarjeta o transferencia, y un solo cobro por cita.
- **Cierre de caja:** el dueño ve el total del día, por medio de pago y por barbero.
- `GET /health` responde si el servicio está vivo.

## Cómo instalarlo
1. Instala Python 3.10 o superior.
2. Crea un entorno virtual: `python -m venv .venv` y actívalo.
3. Instala las dependencias: `pip install -r requirements.txt`.
4. Define las variables de entorno que aparecen en `.env.example` (`SECRET_KEY`, `DATABASE_URL`, `RESPALDO_DESTINO`, `ZONA_HORARIA`, `DOCS_ACTIVAS`). `SECRET_KEY` debe tener al menos 32 caracteres; con una más corta la aplicación no arranca. Por ejemplo, en PowerShell: `$env:SECRET_KEY = "<una-clave-larga-y-al-azar>"` y `$env:DATABASE_URL = "sqlite:///barberia.db"`.

## Cómo ejecutarlo
1. Crea la cuenta del dueño (la primera, porque solo el dueño puede crear al resto del personal): `python -m scripts.crear_dueno "Nombre Apellido" correo@ejemplo.cl`. La contraseña se toma de la variable `DUENO_CONTRASENA` o se pide por teclado (mínimo 10 caracteres).
2. Arranca el servidor: `python -m uvicorn app.main:crear_app --factory`.
3. La documentación interactiva (`/docs`, `/redoc` y `/openapi.json`) viene apagada. Para probar la API en tu equipo, arranca con la variable `DOCS_ACTIVAS=si` y abre `http://127.0.0.1:8000/docs`. No la actives en producción.

Si falta `SECRET_KEY` o `DATABASE_URL`, la aplicación no arranca y dice cuál falta. Las migraciones de `migrations/` se aplican solas al arrancar.

## Cómo probarlo
Ejecuta las pruebas con `python -m pytest -q`, el revisor de estilo con `python -m ruff check .` y la compilación con `python -m compileall -q app`.

## Cómo respaldar
`python -m scripts.respaldo` copia la base a `RESPALDO_DESTINO/barberia-AAAAMMDD-HHMMSS.db`. Usa la copia segura de SQLite (se puede hacer con la aplicación en marcha), revisa `PRAGMA integrity_check` y compara la cantidad de filas de la copia con las del original. Si algo no cuadra, no deja el archivo.

Conviene programarlo todos los días y guardar los respaldos en otro disco o equipo.

## Cómo restaurar
1. Detén la aplicación.
2. Ejecuta `python -m scripts.restaurar RUTA/barberia-AAAAMMDD-HHMMSS.db RUTA/barberia.db`.
3. Si el destino ya existe, el script se niega para no pisar datos. Si de verdad quieres reemplazarlo, agrega `--forzar`.
4. Vuelve a arrancar la aplicación.

## Borrar a pedido (anonimizar a un cliente)
Cuando un cliente pide que borren sus datos: `python -m scripts.anonimizar_cliente correo@ejemplo.cl` (usa `DATABASE_URL`).
- El nombre pasa a "Cliente anonimizado" y el correo a `anon-<id>@anonimo.invalid`.
- La contraseña queda inutilizable y las sesiones que tuviera abiertas dejan de servir.
- Sus citas y cobros se conservan, sin datos personales. El correo original queda libre para registrarse otra vez.
- Al final el script compacta el archivo de la base (VACUUM y vaciado del archivo `-wal`) para que no queden restos del nombre dentro del `.db`. Se puede hacer con la aplicación en marcha; si otra conexión está escribiendo en ese momento, el script lo dice con claridad (termina con código 2: la cuenta ya quedó anonimizada, pero falta compactar) y hay que ejecutar `VACUUM` más tarde, con la aplicación detenida.
- Solo funciona con cuentas de clientes y no se puede deshacer.
- **Los respaldos hechos antes de anonimizar conservan el dato.** Bórralos o rehazlos (haz un respaldo nuevo después de anonimizar y elimina los anteriores que contengan a esa persona).

## Detrás de un proxy
Los límites por dirección usan la dirección de la conexión (`request.client.host`). La aplicación no lee `X-Forwarded-For`, porque cualquiera puede escribir esa cabecera. Si la pones detrás de un proxy inverso, todas las solicitudes parecerán venir de la dirección del proxy y compartirán el mismo límite. Configura con cuidado las direcciones de confianza del servidor ASGI (por ejemplo `--forwarded-allow-ips` en uvicorn, solo con la dirección de tu proxy) antes de depender de esos límites.

## Límites conocidos
- El tope de 3 citas confirmadas por venir cuenta todas las citas del cliente, también las que agenda recepción por él. Recepción y dueño pueden agendar más allá del tope, pero esas citas igual ocupan cupo del cliente cuando él mismo intenta agendar.
- El bloqueo del inicio de sesión por correo se puede usar para molestar a una persona concreta: quien escriba mal su contraseña 5 veces la deja sin poder entrar hasta que pasen 15 minutos.
- Detrás de un proxy mal configurado, el límite por dirección agrupa a todas las personas bajo una misma dirección (la del proxy) y se bloquean entre sí.
- Los bloqueos por intentos fallidos y por dirección viven en la memoria del proceso: al reiniciar la aplicación se reinician, y si corres varios procesos cada uno cuenta por separado.
