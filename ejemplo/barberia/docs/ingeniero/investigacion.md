# Investigación: Barbería Don Mario

Fecha de la investigación: 2026-11-24

## Qué se investigó
Versiones soportadas del lenguaje, framework y base de datos; costos de alojamiento y de soluciones ya hechas; normativa de datos personales de Chile; skills de terceros para el backend elegido.

## Hallazgos (cada uno con fecha de consulta, enlace y tipo de fuente)
- Node.js 24 es la línea de soporte largo activa; entró en mantenimiento el 2026-10-20 según el calendario, y Node 20 ya terminó su vida el 2026-04-30 (consultado el 2026-11-24) [fuente: oficial]: https://nodejs.org/en/about/releases/
- NestJS 12 es la versión mayor actual (publicada el 2026-08-27, con módulos ESM); las fuentes dan la última 12.x entre 12.1.1 y 12.5.0 (consultado el 2026-11-24) [fuente: secundaria]: https://endoflife.date/nestjs
- PostgreSQL 18 es la versión mayor actual; la política comunitaria da cinco años de soporte por versión (consultado el 2026-11-24) [fuente: oficial]: https://www.postgresql.org/support/versioning
- FastAPI publicó la 0.139.0 el 2026-07-01 según una fuente y exige Python 3.10 o superior (consultado el 2026-11-24) [fuente: oficial]: https://fastapi.tiangolo.com/deployment/versions/
- Soluciones ya hechas: Square Appointments tiene plan gratis para un local (con comisión por cobro con tarjeta); Setmore, gratis hasta cuatro usuarios; Fresha ya no es gratis; Booksy parte en 29,99 dólares al mes (consultado el 2026-11-24) [fuente: oficial]: https://squareup.com/gb/en/solutions/barbershop
- Alojamiento: Render cobra unos 7 dólares al mes por un servicio web y entre 7 y 15 por una base PostgreSQL (consultado el 2026-11-24) [fuente: oficial]: https://render.com/pricing.md
- Alojamiento: Hetzner subió sus precios el 2026-06-15; el plan más pequeño ronda 5,49 euros más IVA, pero puede no estar disponible para pedir (consultado el 2026-11-24) [fuente: oficial]: https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/
- Normativa de Chile: la Ley 21.719 de protección de datos personales entra en vigencia el 2026-12-01, aunque hay un proyecto que la posterga a 2027 (consultado el 2026-11-24) [fuente: secundaria]: https://www.diarioconstitucional.cl/2026/06/12/la-ley-21-719-entra-en-vigor-el-1-de-diciembre-y-expone-vacios-en-regulacion-de-pequenas-empresas/
## Las tres opciones

### Opción A: NestJS con PostgreSQL
- Qué es: una aplicación web hecha con Node.js y NestJS, con base de datos PostgreSQL. Es la combinación que el equipo usa por defecto.
- Para quién es buena: para quien tiene a alguien que sepa JavaScript o TypeScript y quiere un proyecto que crezca con orden.
- Costo mensual aproximado: entre 14 y 22 dólares con Render, o unos 6 euros más IVA en un servidor propio (consultado el 2026-11-24).
- Riesgos: NestJS 12 es muy reciente y cambió a módulos ESM, así que algunas guías antiguas ya no sirven.
- Cuándo no elegirla: si quien mantiene el sistema solo sabe Python.

### Opción B: FastAPI (Python) con PostgreSQL
- Qué es: una aplicación web hecha con Python y FastAPI, con base de datos PostgreSQL.
- Para quién es buena: para quien mantiene el sistema con Python y quiere pruebas y estructura claras.
- Costo mensual aproximado: el mismo rango que la opción A, entre 14 y 22 dólares con Render (consultado el 2026-11-24).
- Riesgos: FastAPI aún no tiene versión 1.0 y puede traer cambios entre versiones menores.
- Cuándo no elegirla: si el equipo prefiere un solo lenguaje para pantalla y servidor.

### Opción C: no construir, usar una solución ya hecha
- Qué es: agendar con Square Appointments o Setmore (planes gratis) y llevar la caja en una hoja de cálculo bien ordenada.
- Para quién es buena: para quien quiere resolver ya, sin mantener código.
- Costo mensual aproximado: de 0 a 30 dólares, más la comisión por cobro con tarjeta (consultado el 2026-11-24).
- Riesgos: los datos de los clientes quedan en una empresa extranjera, el cierre de caja no se integra con la agenda y los planes gratis pueden cambiar.
- Cuándo no elegirla: si Don Mario quiere los datos en su poder y un cierre de caja hecho a su medida.

## Recomendación
Se recomienda la opción A por ser la combinación de uso común del equipo, con un ecosistema maduro para pruebas y estructura. Lo que se sacrifica es que NestJS 12 es muy nuevo. Si quien mantiene el sistema es un sobrino que sabe Python, la opción B es igual de sólida y puede ser mejor. La opción C es honesta y barata si Don Mario no necesita el cierre de caja propio.

## Elección de la persona
Eligió la opción B el 2026-11-24: "El sobrino sabe Python, prefiero esa".

## Skills y repositorios revisados
- Se encontraron varias skills de terceros para FastAPI (por ejemplo las de Jeffallan, GNSubrahmanyam y qredence), listadas en skills.sh y repositorios de GitHub (consultado el 2026-11-24). No se instaló ninguna: no se leyeron enteras y las skills propias de arquitectura, pruebas y decisiones cubren las etapas del plan. Quedan como referencia para consulta futura, sin ejecutarlas.

## No verificado
- La versión exacta actual de NestJS (las fuentes se contradicen entre 12.1.1 y 12.5.0).
- Si Node 26 ya es LTS (las fuentes se contradicen).
- El precio actual exacto de PostgreSQL en Render y la disponibilidad del plan pequeño de Hetzner.
- Si el proyecto que posterga la Ley 21.719 ya fue aprobado.
- La versión de FastAPI: una búsqueda dio la 0.139.0 y el registro de paquetes entregó la 0.165.0. Se fijó la del registro.
