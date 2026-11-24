# Arquitectura: Barbería Don Mario

## Opción elegida y por qué
Opción B de la investigación: FastAPI con Python y base de datos PostgreSQL. La persona la eligió porque quien mantendrá el sistema, un sobrino, sabe Python. Se verificó el 2026-11-24 que FastAPI exige Python 3.10 o superior.

Cambio posterior (2026-11-24): la base de datos pasó de PostgreSQL a SQLite, porque la barbería tiene unas 40 citas al día y un solo servicio. Ver la decisión 0003.

## Tecnología
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

## Decisiones importantes
- Monolito modular en lugar de varios servicios: es una sola barbería y un solo mantenedor (docs/decisiones/0001-monolito-modular.md).
- Dinero en pesos enteros, sin decimales, porque el peso chileno no usa centavos (docs/decisiones/0002-dinero-en-enteros.md).

## Cómo se comunican las partes
El cliente usa una página web en el celular, que llama a la API de FastAPI. La API usa los casos de uso, que guardan y leen datos a través del repositorio. En producción el repositorio habla con PostgreSQL.

## Despliegue previsto
Un servicio web con un disco persistente donde vive el archivo de la base, en un proveedor que la persona elija. La guía completa y los costos van en entrega.md. El ingeniero no publica nada.

## Riesgos técnicos principales
- Citas duplicadas por solicitudes simultáneas: se resuelve dentro de una transacción de SQLite que revisa el cruce y guarda en un solo paso, además de la regla de dominio, y se prueba con varios hilos a la vez.
- Zonas horarias: todo se guarda en hora universal y se muestra en hora de Santiago.
- FastAPI sin versión 1.0: se fijan las versiones y se actualiza con las pruebas en verde.
