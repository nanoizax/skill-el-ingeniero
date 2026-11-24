# Guía de entrega: Barbería Don Mario

Esta guía es para ti, que eres quien decide cuándo y cómo publicar. El ingeniero dejó el sistema listo para enviar; el envío lo haces tú, con tus propios criterios. Nadie publicó nada ni creó cuentas a tu nombre.

## Qué recibes
Un sistema para que tus clientes agenden su hora, para que cada barbero vea su agenda del día, para anotar cuánto se cobró en cada cita y para que tú veas el cierre de caja. Funciona sin avisos por WhatsApp ni pagos con tarjeta, que quedaron para una segunda versión. El código está en la carpeta del proyecto, junto con las pruebas. Para verlo funcionar en tu computador, sigue el README: instalas Python, instalas las dependencias y arrancas el servidor.

## Opciones para publicarlo
- Un servicio de publicación en internet con disco propio (por ejemplo Render): el servicio web parte en unos 7 dólares al mes, consultado el 2026-11-24. El precio del disco donde vive la base no se pudo confirmar.
- Un servidor propio pequeño (por ejemplo Hetzner): unos 5,49 euros más IVA al mes, consultado el 2026-11-24, aunque ese plan puede no estar disponible para pedir. Es más barato, pero tienes que cuidar tú el servidor.

## Pasos para publicarlo
1. Elige una de las dos opciones y crea tu cuenta (ver más abajo).
2. Sube el código a ese servicio siguiendo sus instrucciones.
3. Define las variables de entorno que se explican más abajo.
4. Crea la cuenta del dueño con el comando del README (python -m scripts.crear_dueno).
5. Programa el respaldo diario (ver la sección de respaldo).
6. Haz las comprobaciones de la sección "Cómo comprobar que quedó bien".

## Cuentas que debes crear tú
- La cuenta del servicio de publicación, a tu nombre y con tu tarjeta. Tú la pagas.
- La cuenta de un lugar distinto donde guardar los respaldos (otro servidor, otro disco o un almacenamiento en la nube).
- Un dominio con el nombre de tu barbería, si quieres una dirección propia.

## Variables de entorno
Son datos de configuración que se escriben en el servicio de publicación y no en el código. Sin valores en esta guía, porque son secretos.
- SECRET_KEY: la clave con la que se firman las sesiones. Debe tener al menos 32 caracteres, ser al azar y distinta en cada instalación; con menos, el sistema no arranca. Si se filtra, hay que cambiarla.
- DATABASE_URL: dice dónde está el archivo de la base de datos, por ejemplo sqlite:///barberia.db. Tiene que apuntar al disco que no se borra.
- RESPALDO_DESTINO: la carpeta donde el script guarda las copias de seguridad.
- ZONA_HORARIA: la zona horaria de tu barbería. Si la dejas vacía, se usa la de Santiago de Chile.
- DOCS_ACTIVAS: si vale si, el sistema muestra la página de documentación técnica de la API. Déjala vacía al publicar, para no exponerla a todo el mundo.

## Costos mensuales estimados
Entre 7 y 10 dólares aproximadamente por el servicio y el disco, más lo que cueste el lugar de los respaldos (puede ser gratis si usas un disco que ya tienes). Son precios de internet consultados el 2026-11-24 y pueden cambiar. Revisa los precios oficiales antes de pagar.

## Respaldo y restauración
Se respalda el archivo completo de la base una vez al día. El comando python -m scripts.respaldo hace una copia segura y comprueba que quedó bien. Prográmalo para que corra todos los días y guarda las copias en OTRO lugar distinto al del sistema: una copia en la misma máquina no sirve si esa máquina falla. Para restaurar, detén la aplicación y usa python -m scripts.restaurar con la copia y el destino. Prueba la restauración una vez antes de confiar en ella.

## Textos legales: antes de abrirlo al público
El sistema guarda el nombre y el correo de tus clientes, y eso exige un aviso de privacidad y unos términos de uso. No los redactó el ingeniero, porque tienen que ser de un profesional. Don Mario decidió (respuesta simulada para la prueba): su asesor legal le entregará esos textos antes de abrir el sistema a los clientes, y hasta entonces solo lo usará el personal. Confirma con tu asesor qué exige la ley chilena de datos personales en la fecha en que publiques.

## Cómo comprobar que quedó bien después de publicar
- Abre la dirección /health: tiene que responder que el servicio está vivo.
- Inicia sesión con la cuenta del dueño.
- Agenda una cita de prueba, cancélala y mira que la hora quede libre.
- Ejecuta un respaldo y revisa que el archivo aparezca en el otro lugar.

## Cómo enterarte si algo falla
Un sistema que se cae sin que nadie lo note es peor que uno que avisa. Usa un servicio de vigilancia gratuito que visite la dirección /health cada cinco minutos y te escriba al correo si deja de responder. Revisa los precios y los límites de ese servicio antes de elegirlo. Además, el sistema deja un registro de cada error inesperado, sin guardar contraseñas ni el contenido de lo que escribieron las personas; pídele a quien lo mantiene que lo revise cada semana.

## Si algo sale mal
Vuelve a la versión anterior desde tu servicio de publicación. Si se dañó la base, detén la aplicación y restaura el último respaldo. Anota qué pasó y avisa a quien mantiene el sistema.

## Mantenimiento
Si un cliente pide que borres sus datos, ejecuta python -m scripts.anonimizar_cliente con su correo: quita su nombre y su correo y conserva las citas y los cobros sin datos personales. Los límites contra abusos (intentos de entrada y registros) se reinician cada vez que reinicias el sistema.
Actualiza las dependencias cada algunos meses y vuelve a correr las pruebas. Revisa los costos cada mes y renueva el dominio antes de que venza. Cambia la clave SECRET_KEY si alguien que la conocía deja de trabajar contigo.

## Decisiones que son tuyas
- Cuándo y dónde publicar, y cuánto pagar por ello.
- Qué cuentas crear y a nombre de quién.
- Dónde se guardan los respaldos y quién los revisa.
- Si más adelante agregas avisos por WhatsApp o pagos con tarjeta.
