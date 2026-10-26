# Progreso

## Navegación al inicio desde la pregunta 11 — 2026-10-25

- El examen y las vistas de revisión A/B–E suben al inicio del contenido al navegar a una pregunta con ID 11 o superior, tanto con la matriz como con Anterior/Siguiente. El margen superior evita ocultar el inicio bajo la cabecera. Las preguntas 1–10 mantienen su posición; seleccionar o limpiar una respuesta no dispara el desplazamiento.
- Archivos: motor del examen, scripts de las dos vistas, sus referencias versionadas en HTML y plantilla del examen. No se cambian preguntas, tiempo ni supervisión; se conservan los cambios pendientes de ausencia facial.
- Navegador en A: clic en 10 sin desplazamiento; Siguiente a 11 y 12 con desplazamiento; seleccionar/limpiar en 12 sin llamadas adicionales; clic en 50 vuelve al inicio. Diagnósticos JS sin errores. Sin acceso a PostgreSQL.

## Foto y duración de episodios de ausencia facial — 2026-10-25

ESTADO: Implementado y probado con PostgreSQL aislado y entradas controladas en navegador; pendiente de ensayo con webcam real.

- Solicitud del usuario: fotografía cuando no haya una persona visible y duración de la ausencia en la revisión. El detector existente trabaja con rostros, no con cuerpos ni distancia física. Ya reconoce dos o más rostros visibles y registra una alerta tras observaciones consecutivas; no garantiza reconocer a una persona fuera del encuadre, de espaldas o con el rostro cubierto.
- Ahora congela un fotograma antes de inferir, de modo que foto y detección utilizan la misma imagen. Inicia un episodio al no detectar rostros, comunica su continuidad y lo termina al detectar un rostro nuevamente. Una foto por episodio, con envíos ordenados y secuencias idempotentes. Errores de análisis, video pausado/desconectado y detención del monitor se distinguen de una ausencia. Se descartan inferencias pendientes después de detener la cámara.
- El servidor calcula duración estimada entre recepciones sin aceptar los segundos del cliente, excluye huecos de más de 30 s y señala registros incompletos. El cierre del examen termina episodios abiertos sin añadir segundos sin observación. La ausencia deja el resultado pendiente de revisión humana, sin anularlo automáticamente. Límites: análisis periódico y latencia impiden medir la salida exacta; un fallo de comunicación puede omitir observaciones pese a un reintento y se muestra un aviso al alumno.
- Consentimiento independiente `ausencia-v1-foto` en preparación y comprobado en servidor; no se revelan intervalos técnicos en ese texto. Nuevas columnas de consentimiento y tabla `episodios_ausencia` mediante adiciones no destructivas del arranque. Archivos normalizados y cifrados con dominio de clave separado en `instance/evidencias_ausencia/`, fuera de la web pública y Git. Máximo 60 episodios por intento; caducidad de fotos a 30 días, purga integrada conservando el registro sin imagen.
- El administrador ve fotos, segundos por episodio y acumulados, inicio/fin y aviso de medición incompleta. El alumno no recibe las fotos y la ruta de imágenes exige administrador; respuestas sin caché. La preparación vuelve a solicitar aceptación si falta el consentimiento nuevo y conserva el vencimiento de intentos en curso. Se versionaron las URL de los dos scripts modificados para evitar reutilizar código antiguo.
- Archivos: `models/ausencia.py`, esquema y consulta de usuario, cierre de supervisión; endpoints de consentimiento/observaciones y acceso administrativo; rutas y plantillas de preparación, examen y resultado; monitor facial y motor JS; purga, pruebas y documentación de reglas/evidencias.
- Validación: 49 pruebas OK (`tests.test_ausencias`, `tests.test_supervision`, `tests.test_puntuacion`, `tests.test_importacion_area_a`, `tests.test_areas_bcde`, `tests.test_bancos_activos`) usando exclusivamente `unmsm_proctor_test` en `127.0.0.1:5432`, cuya identidad valida la suite antes de importar `app.py`. Se probaron duración calculada desde BD, rechazo de segundos arbitrarios, cifrado/descifrado, acceso de admin, consentimiento/CSRF/propiedad/JPEG inválido, concurrencia y reintentos sin duplicar, cierre y caducidad. No se probaron personas reales ni se accedió a la base de desarrollo/producción.
- Navegador: secuencia controlada ausente:1 → ausente:2 → presente:3, nuevo episodio ausente:1 → interrumpido:2; alerta `multiple_rostro` única tras dos observaciones de dos rostros. El primer ensayo cargó un módulo antiguo desde caché; tras versionar la URL se repitió correctamente. Imagen roja preservada aunque la fuente cambió a azul durante la inferencia y antes del envío; una foto y tres mensajes ordenados. Diagnósticos y `git diff --check` sin errores. Sin commits ni push.

## Simplificación de textos de preparación — 2026-10-25

- A petición del usuario, retirado el anuncio «Nuevo simulacro: 100 preguntas · 3 horas…» de `templates/preparacion.html`. El consentimiento ya no expone segundos de captura ni el umbral temporal de detección, y se retiró la frase sobre métricas de MediaPipe a Google.
- Se conservan el consentimiento para fotografías, cifrado, acceso administrativo, retención y revisión humana. Solo cambia el texto visible; no se modifican detector, capturas ni reloj. Validación de sintaxis Jinja y diagnósticos sin errores; sin importar Flask ni acceder a PostgreSQL.

## Retirada de anuncios de vista previa del panel — 2026-10-25

- Retirados de `templates/dashboard.html` los dos bloques de vista previa A/B–E, sus botones y la etiqueta superior de 100 preguntas/tres horas que aparecen en la captura del usuario. El panel comienza con el contenido habitual de intentos y usuario.
- Cambio exclusivamente de presentación; bancos, figuras, duración y flujo de simulacros conservados. Validación: sintaxis Jinja y `git diff --check` sin errores, sin importar Flask ni acceder a PostgreSQL.

## Integración de 100 preguntas y tres horas en A–E — 2026-10-25

ESTADO: Implementada y verificada en PostgreSQL de pruebas y navegador.

- Alcance autorizado por el usuario: sustituir los bancos de diez preguntas por los bancos revisados de 100 preguntas en las cinco áreas y fijar tres horas para nuevos intentos. `scripts/activar_bancos_100.py` valida las cinco áreas, incorpora sus lecturas y conserva las diez preguntas originales de cada área en `data/examenes/anteriores/`. A incluye las correcciones de 47/71; B–E mantienen HV sin imágenes.
- Se reutiliza la tabla existente `examenes_versiones`: cada nuevo intento guarda una versión inmutable de sus preguntas dentro de la transacción de inicio. Recarga, entrega, anulación/revisión y reposición del administrador leen esa versión. Los intentos y resultados antiguos sin versión consultan el banco histórico, sin recalificar ni ampliar su vencimiento. No se añaden tablas ni columnas. La configuración del servidor fija 180 minutos; valores heredados de `.env` no reducen el plazo. No se modificó `.env`.
- La lista pública de campos incorpora lecturas, fórmulas y figuras sin claves. Nuevo renderer DOM/MathML en `static/js/contenido_academico.js` y estilos en `static/css/contenido_academico.css`, usados por examen y revisión académica. El navegador del examen agrupa los 19 cursos y las tres lecturas; tiene desplazamiento para las 100 preguntas. Se sustituyó el texto estático de 60 minutos por el tiempo real del intento; cero segundos ya no reinicia el contador por un fallback.
- Archivos funcionales: cinco bancos activos y archivos históricos; `models/examen.py`, `models/intento.py`, `models/supervision.py`, `utils/preguntas.py`, `routes/api.py`, `routes/simulacro.py`, `routes/resultados.py`, `config.py`, referencia DDL de duración en `models/database.py`, motor JS, plantillas de examen, resultado, preparación y dashboard. Documentación y ejemplo de configuración actualizados. Se preservan los cambios previos de contenido y vistas.
- Pruebas: 43 casos OK con `unittest` (`tests.test_supervision`, `tests.test_puntuacion`, `tests.test_importacion_area_a`, `tests.test_areas_bcde`, `tests.test_bancos_activos`). Antes de importar `app.py` se confirmó por SQL la identidad exclusiva de `unmsm_proctor_test` en `127.0.0.1:5432`; credenciales no registradas. Incluyen inicio en A–E con 100 preguntas y 10 800 segundos, rechazo de duración/área del cliente, recarga sin cambiar banco/vencimiento, 100 aciertos = 2000 puntos, 100 blancos, archivo histórico con diez preguntas y una hora, y calificación independiente de cambios del banco activo. La primera ejecución del ensayo A–E reutilizó un CSRF anterior a la recarga: falló la prueba y se corrigió el ensayo para usar el token renovado por el GET; no se relajó la validación de producción.
- Navegador sobre plantillas reales renderizadas con datos sanitizados: recorrido de 500 preguntas, cinco opciones por pregunta, 100 botones y 19 cursos en cada área, cero errores JS; imágenes decodificadas. En A se verificaron ocho subrayados de 49, dos fracciones de 38 y seis filas de la tabla de 90. Reloj inicial 03:00:00, siguiente segundo 02:59:59 y entrada cero conservada. El HUD fijo desbordaba la pestaña estrecha; se ajustó la cuadrícula sin desbordamiento a 543 px en 11, 24, 38, 39, 49, 84, 90 y 91. Diagnósticos sin errores y `git diff --check` OK.
- Las plantillas temporales de comprobación omitieron exclusivamente la activación de cámara/intento y se retiraron al terminar; no se probó webcam ni se dejó una ruta de acceso alternativa en la aplicación. No se accedió a la base de desarrollo/producción, no se alteraron resultados existentes, no se hicieron commits ni push.

## Fondo institucional en ingreso y registro — 2026-10-20

ESTADO: Cambio visual implementado; pendiente de revisión manual en el navegador.

- Se incorporó la fotografía del campus proporcionada por el usuario como fondo de ingreso y registro, con una capa oscura para conservar el contraste de las tarjetas blancas. Se mantuvo la paleta vino, blanco y gris y se retiró el monograma «UN» de ambas tarjetas.
- Archivos: `static/campus-unmsm.png`, `static/css/auth.css`, `templates/base.html`, `templates/login.html` y `templates/register.html`. No se alteraron formularios, rutas, esquema ni lógica de autenticación.
- Verificación: la imagen existe (1 217 395 bytes) y los diagnósticos del editor no reportaron errores en plantillas ni CSS. No se importó `app.py`, no se arrancó Flask y no se accedió a PostgreSQL.
- Pendiente: inspección visual de ingreso y registro en navegador, también en pantallas de menor ancho.

## Cuenta administradora local — 2026-10-11

- Creada la cuenta administradora solicitada por el usuario en `simulacro_local`, con contraseña aleatoria almacenada como hash de Werkzeug. Credenciales y datos de identificación omitidos en esta documentación.
- Verificada la identidad de la conexión local antes de insertar. Inserción parametrizada y transaccional; rechazo si el identificador solicitado ya existía. No se modificó la cuenta previa.
- Comprobación después del commit: cuenta persistida, `es_admin = true` y contraseña compatible con el hash almacenado. Ejecución con código 0.
- La tabla de usuarios ya existía y contenía una cuenta antes de esta operación; el estado de base vacía documentado más abajo corresponde al cierre anterior de instalación.
- Sin importación de la aplicación, cambios de esquema ni pruebas HTTP. Sin cambios de código funcional, commits o push.
- Para entrar con la cuenta nueva, cerrar cualquier sesión anterior e iniciar sesión con las credenciales entregadas al propietario.

## Instalación desde cero en Windows — 2026-10-11

ESTADO: Instalación local completada y base vacía verificada; aplicación aún sin arrancar.

- El usuario autorizó preparar una base nueva sin datos anteriores y documentar el proceso para un compañero que clone GitHub.
- Estado inicial de Git limpio. No se encontraron `.env`, `.venv` ni `backup_simulacro.sql` en esta copia; tampoco servicio PostgreSQL.
- Python 3.12.10 instalado mediante `winget install --id Python.Python.3.12 --exact --source winget --scope user --silent --accept-package-agreements --accept-source-agreements`: `Instalado correctamente`.
- Entorno `.venv` creado con el ejecutable de Python 3.12.10 e instalación de `requirements.txt` completada. La herramienta de configuración informó 3.15 por metadatos inconsistentes; el ejecutable real (`.venv/Scripts/python.exe --version`) y `pyvenv.cfg` confirman 3.12.10.
- `.venv/Scripts/python.exe -m pip check`: `No broken requirements found.` Paquetes principales: Flask 3.1.3, psycopg2-binary 2.9.13, python-dotenv 1.2.4, Werkzeug 3.1.9 y gunicorn 26.2.0. No se fijaron nuevas versiones en los requisitos.
- Instalador PostgreSQL 17.11-5 descargado por WinGet, hash verificado y asistente abierto. Requiere intervención local para contraseña y finalización. No se afirmó que el servicio estuviera instalado.
- `README.md` enlaza la guía ampliada `docs/guia_portabilidad.md`: herramientas, clonación, entorno, rol restringido, base vacía, configuración, esquema, arranque y diferencia frente a restauración.
- Discrepancia observada: `crear_bd.py` no decodifica la contraseña obtenida con `urlparse`; puede fallar con contraseñas codificadas. Impacto: primer paso de conexión. Propuesta documentada: crear la base con `psql` y usar `init_db` con el DSN existente; no se corrigió el script. Una corrección futura requiere aprobar el cambio y probar contraseñas especiales contra una base aislada.
- `git diff --check`: sin errores de espacios; avisos LF/CRLF. `git check-ignore .env .venv/pyvenv.cfg`: ambas rutas excluidas. Diagnósticos del editor: sin errores en los dos documentos revisados.
- No se importó la aplicación, no se ejecutaron pruebas de integración ni se creó/modificó esquema. No hubo commits, ramas ni push. No se modificó el script de restauración.

COMPROBACIÓN POSTERIOR: el usuario terminó el instalador. `Get-Service '*postgres*'` confirmó `postgresql-x64-17 Running`; `pg_isready -h 127.0.0.1 -p 5432` respondió `accepting connections`. Esto confirma disponibilidad del servidor, no autenticación ni existencia de la base del proyecto.

CIERRE DE CONFIGURACIÓN:
- Autenticación local completada con autorización del usuario. Antes de crear recursos se comprobó la identidad `127.0.0.1:5432/postgres` y la ausencia del rol y base de destino.
- Creados `unmsm_local` (sin superusuario, creación de bases, creación de roles ni replicación) y `simulacro_local`, propiedad de ese rol.
- Creado `.env` mediante apertura exclusiva, sin sobrescribir archivos. Contraseña propia aleatoria para el rol y `SECRET_KEY` aleatoria; la contraseña administrativa no se guardó en el proyecto.
- Verificación con psycopg2 usando la nueva conexión: `simulacro_local / unmsm_local / 127.0.0.1:5432`, cero tablas fuera de los esquemas internos y privilegios del rol comprobados. Proceso finalizado con código 0.
- Criterios cumplidos: Python y dependencias disponibles, PostgreSQL activo, base nueva vacía, conexión privada funcional y guía de instalación para el compañero.

PENDIENTE: preparar tablas y arrancar la aplicación cuando se vaya a utilizar; deliberadamente se conserva la base con cero tablas. No se probó el arranque ni se importó la aplicación. Subfases 1A/1B no autorizadas.

FASE: −1 — Auditoría inicial  
ESTADO: Auditoría ampliada aprobada por el usuario  
FECHA: 2026-10-07

IMPLEMENTADO:
- Revisión estática de aplicación, datos, vistas, JavaScript, pruebas y despliegue.
- Matriz de trazabilidad contra la especificación de fase 0 disponible.
- Matriz ampliada frente a `ESPECIFICACION.md` y `REGLAS.md` leídos desde `C:\Users\Sergio\Downloads\`.
- Diagnóstico de seguridad, diferencias de stack y plan de continuación por cambios verificables.

MODIFICADO:
- Ningún archivo funcional.

PRUEBAS:
- `python -m unittest tests.test_puntuacion tests.test_modelos -v`: 8 OK.
- `python -m compileall -q app.py config.py models routes utils tests`: sin errores.
- `python -m pytest -q`: no disponible; falta `pytest`.
- `node --version`: Node.js no se encontró; no se ejecutaron pruebas `node:test`.

PENDIENTE:
- Referencias incorporadas posteriormente durante la preparación autorizada del entorno, registrada más abajo.
- Ejecutar pruebas de integración y carga en entorno aislado.
- Preparar y ejecutar las pruebas de seguridad únicamente tras `OK SUBFASE 1A`; la Subfase 1B requiere autorización independiente.

RIESGOS:
- Cierre y calificación controlables en parte por el cliente; resultados sin transacción única.
- Secretos de respaldo en archivos de configuración; protección CSRF ausente.
- No se dispone de historial Git en este directorio.
- La nueva especificación exige un runtime biométrico distinto del implementado; cualquier migración requiere decisión explícita y evaluación de plantillas/licencias.

## Preparación autorizada del entorno

FASE: Preparación del entorno, previa a Subfase 1A  
ESTADO: Instancia aislada preparada; Git pendiente de instalación o reparación oficial  
FECHA: 2026-10-07

IMPLEMENTADO:
- Copias completas de `AGENTS.md`, `docs/ESPECIFICACION.md` y `docs/REGLAS.md` desde Downloads. Destinos ausentes antes de copiar y contenido idéntico comprobado con SHA-256.
- Instancia independiente PostgreSQL 17.10 en `127.0.0.1:55432`, con datos en `D:\PROYECTO\UNMSM\.test-postgres\data`.
- Base vacía `unmsm_seguridad_test`, propiedad de `unmsm_test` (sin superusuario, creación de bases ni creación de roles).
- Credenciales aleatorias nuevas dentro del directorio ignorado, con acceso restringido a Sergio, SYSTEM y la cuenta del sandbox. No se modificó `.env` ni se imprimieron contraseñas.
- Registro local de identidad de la instancia y script de preparación que verifica dirección, puerto y directorio antes de crear el usuario/base; rechaza reutilizar destinos existentes.

MODIFICADO:
- `.gitignore`: reglas `/.test-postgres/`, `.env.*` y excepción `!.env.example`.
- `docs/AUDITORIA_INICIAL.md`: ubicación actual de las referencias.
- Este documento: aprobación de auditoría y estado de preparación.
- Ningún archivo funcional, endpoint, modelo, banco, plantilla o configuración privada.

COMPROBACIONES:
- Bind TCP de `127.0.0.1:55432`: puerto libre antes de inicializar y arrancar.
- `.test-postgres` no existía; ruta distinta de `C:\Program Files\PostgreSQL\17\data`, directorio del servicio principal según el registro de Windows.
- Exclusión explícita comprobada por lectura de `.gitignore` antes de `initdb`; `git check-ignore` queda pendiente hasta disponer de Git funcional.
- `initdb` finalizó con código 0. El arranque dentro del sandbox falló por creación de token restringido; se inició fuera del sandbox con autorización, en ventana oculta.
- Ajustes de ACL con PowerShell fallaron por restricciones de permisos; `icacls` añadió correctamente el acceso autorizado de Sergio y se verificaron permisos del archivo local de credenciales.
- Primera comprobación SQL rechazó la representación textual `127.0.0.1/32`; una consulta de solo lectura confirmó host/puerto/directorio correctos. Se normalizó con `host(inet_server_addr())` antes de crear usuario/base.
- `python .test-postgres/bootstrap_database.py`: creación y verificación correctas; identidad local por directorio y `system_identifier`; 0 tablas de aplicación.
- `pg_isready -h 127.0.0.1 -p 55432`: accepting connections.
- Servicio principal `postgresql-x64-17`: Running antes y después. No se abrió conexión ni se ejecutó SQL contra la instancia principal.
- 54 archivos protegidos comparados con SHA-256 antes/después: ningún cambio, incluido `.env`.
- Búsqueda de Git alternativo en rutas habituales, GitHub Desktop, WinGet, Scoop y Chocolatey: no se encontró otra instalación. Los binarios de `D:\Git` no arrancan; el registro señala esa misma instalación. No se inicializó `.git`, no hubo commits ni ramas.

PRUEBAS:
- No se ejecutaron pruebas de integración, migraciones ni inicialización del esquema de la aplicación.
- No se importó `app.py`.

PENDIENTE:
- Instalar o reparar Git mediante su instalador oficial y comprobar las exclusiones antes de añadir archivos.
- `OK SUBFASE 1A` para implementar el ejecutor seguro y las pruebas `unittest` con fixtures aislados.
- El ejecutor futuro debe verificar esta identidad, fijar `DATABASE_URL` y rechazar destinos ambiguos antes de importar la aplicación. La base está vacía: el esquema de pruebas aún no está preparado.
- La instancia de pruebas corre como proceso independiente, no como servicio automático; tras reiniciar Windows deberá arrancarse de nuevo usando su propio directorio/puerto.

RIESGOS:
- El problema de inicialización al importar `app.py` sigue vigente y la lógica del examen conserva los hallazgos de la auditoría.
- La Subfase 1B y los cambios de lógica siguen sin autorización.

## Copia limpia para GitHub - 2026-10-08

ESTADO: Preparada; pendiente de publicar.

- El usuario aprobo publicar una copia limpia y explicar los cambios.
- Archivos: config.py, docker-compose.yml, .env.example, README.md, docs/guia_portabilidad.md, docs/PUBLICACION_GITHUB.md y este documento.
- Secretos de respaldo sustituidos por variables de entorno obligatorias. Configurar .env antes del arranque.
- No se importo app.py, no hubo migraciones ni conexiones a PostgreSQL.
- Primera prueba: 8 casos; 5 OK, 2 errores UTF-8 y 1 fallo de integridad del modelo. Se reconstruyeron copias por bytes verificados.
- Prueba posterior: python -m unittest tests.test_puntuacion tests.test_modelos -v: Ran 8 tests ... OK.
- Sintaxis Python por AST: OK. Variables de entorno: cuatro casos OK, con dotenv desactivado durante la prueba.
- Revision de siete secretos de respaldo conocidos: ninguno presente. Docker no disponible; arranque no probado.
- MinGit oficial descargado y verificado con SHA-256 del proveedor. Version 2.56.0.windows.2.
- Se detecto ausencia de .git/HEAD en la carpeta original; no se modifico ni reconstruyo su historial.
- Pendientes: publicar, verificar remoto e invitar al companero por el propietario. Subfases 1A/1B no autorizadas.

COMPROBACION ADICIONAL:
- La revisión final encontró 81 archivos publicables; sintaxis Python y exclusión de valores sensibles conocidos: OK.
- git diff --cached --check detectó espacios finales y líneas vacías heredados del código original. No se reformateó el proyecto para mantener el cambio mínimo.

## Publicación completada — 2026-10-08

ESTADO: Código publicado en https://github.com/AtreuhANT/unmsm-simulacros, rama main.

- Primer commit limpio: 18e33de94e7d3f48290dc033473e2cb002aa8921, con 81 archivos.
- `git push -u origin main`: `[new branch] main -> main`; seguimiento de origin/main configurado.
- `git ls-remote origin refs/heads/main`: coincide exactamente con el primer commit publicado.
- `git fsck --full`: código 0; un blob no referenciado por la actualización previa de documentación, sin fallos de integridad.
- La primera subida falló por propiedad de la copia bajo la cuenta del sandbox. Se utilizó una excepción safe.directory únicamente en cada comando, sin cambiar la configuración global.
- El administrador de credenciales habitual falló con BadImageFormatException. La publicación funcionó usando el auxiliar wincred de MinGit y las credenciales de Windows; no se mostraron credenciales ni se guardaron en el repositorio.
- Criterios cumplidos: publicación real, commit remoto verificado, secretos de respaldo retirados, documentación para colaborar y 8 pruebas unitarias OK.
- Limitaciones: arranque de la aplicación y Docker no ejecutados; no se completaron fases funcionales ni pruebas de integración. La revisión de espacios finales detectó formato heredado y se dejó documentada.
- Pendientes: el propietario debe invitar al compañero desde GitHub; continuar desde un clon nuevo o revisar la ausencia de .git/HEAD en la carpeta original antes de trabajar con ese historial.

## Supervisión y revisión humana — 2026-10-11

### Corrección del rechazo de parpadeo

INCIDENCIA DE ARRANQUE POSTERIOR:
- `app.py` no iniciaba por `SyntaxError` en la primera línea de `models/usuario.py` (`kimport json`). Se corrigió únicamente ese carácter extra; se mantuvieron los demás cambios del archivo.
- Verificación sin importar `app.py` ni tocar PostgreSQL: análisis AST correcto en 14 archivos Python de aplicación, modelos y rutas; diagnósticos del editor sin errores y `git diff --check` correcto para el archivo. Falta confirmar el arranque con la instancia local del usuario.

INCIDENCIA DE CÁMARA NEGRA DURANTE EXAMEN:
- Captura del usuario en `/examen/A`: video negro y estado `Error de cámara`. La ruta de recuperación del intento hacía una sola llamada a `getUserMedia`, descartaba la causa concreta y no ofrecía reconexión. La captura no permite afirmar si el dispositivo estaba ocupado, el permiso fue denegado u ocurrió otro fallo.
- `static/js/monitor_engine.js` y `templates/examen.html`: hasta tres intentos para `NotReadableError`/`AbortError` transitorios; mensaje específico de permiso, cámara ocupada o no encontrada; botón manual de reconexión sin crear otro intento ni reiniciar cronómetro. Si el flujo de video termina, muestra `SIN CÁMARA` y habilita el botón. Al reconectar, el monitor facial usa el video existente y se reinicia el detector opcional de celular.
- Verificación aislada en navegador con `getUserMedia` simulado: reintentos transitorios, permiso denegado y pista terminada, 3/3 OK. Sintaxis JS del motor comprobada en navegador, diagnósticos del editor sin errores. No se importó `app.py` ni se accedió a PostgreSQL.
- Pendiente: repetir el flujo completo preparación → examen con la cámara real del usuario y comprobar el mensaje exacto si el dispositivo vuelve a fallar. No se afirma que el dispositivo real ya quedó reparado.

INCIDENCIA DE AVISOS FACIALES Y CELULAR:
- En el intento compartido por el usuario, la consola registró `TinyYolov2 - load model before inference`: la ruta de examen recuperado saltaba la carga de los modelos de face-api antes de iniciar `facial_presence`. Por ello no se procesaba la ausencia. Se carga el modelo antes de iniciar el monitor, y un fallo de inferencia ahora genera estado visible en vez de quedar solo en la consola.
- El resultado de ese intento muestra dos eventos `celular_detectado` separados aproximadamente diez segundos. El detector sí generó observaciones, pero sin aviso al primer positivo ni continuidad suficiente para la revisión automática de diez segundos. Se muestra aviso inmediato de **posible** celular y estado persistente del detector; se reduce el umbral de confianza de 0.65 a 0.50. La revisión humana sigue exigiendo observación sostenida por el servidor; no se anula por una sola detección.
- La pantalla distingue el aviso facial del estado de celular. Una primera lectura sin rostro se muestra como alerta; tras dos lecturas consecutivas (~12 s) el monitor registra la observación. Los fallos de cámara/modelo se muestran como tales para no confundirlos con ausencia voluntaria.
- Si se interrumpe la pista de video, se detienen los monitores de rostro y celular; se reactivan al reconectar. La pantalla indica que el detector de celular está detenido, en vez de dejar un estado anterior de «activo».
- Prueba adicional aislada en navegador: corte de pista detiene ambos monitores y reconexión los reactiva, 2/2 OK.
- Pruebas aisladas en navegador: sintaxis de motor y detector correcta; modelos cargados una vez; arranque de los tres monitores; avisos persistentes facial/celular; detección simulada de celular, aviso de revisión y cierre del detector: todos OK. Diagnósticos del editor sin errores. Falta prueba real con persona fuera de cuadro y celular sostenido; no se cambió el estado del intento cerrado observado.

ACTUALIZACIÓN TRAS SEGUNDO RECHAZO DEL USUARIO:
- El ajuste de tiempos y calibración no resolvió el caso real. Se sustituye exclusivamente la medición ocular de contornos de face-api Tiny por Face Landmarker local y sus señales de cierre de ambos ojos. Se conserva la verificación de identidad y sus plantillas existentes.
- `static/js/modulos/blink_challenge.mjs`: secuencia abiertos → cerrados → abiertos, ambos ojos, estabilidad mínima y reinicio de secuencia incompleta ante pérdida del rostro o intervalos largos. Solo analiza fotogramas nuevos. Muestra estado ocular, instrucciones por paso y contador; libera el detector al finalizar o fallar.
- Se añadieron porcentajes de cierre de cada ojo solo en la pantalla, sin enviarlos al servidor, para distinguir falta de lectura de umbrales inadecuados durante la prueba con cámara real.
- `templates/preparacion.html`: integración del módulo; desactiva reinicio de cámara durante el reto. Modelo versionado y procedencia/hash en `static/models/mediapipe/FACE_LANDMARKER.md`.
- Verificación real en navegador: carga del modelo local, inferencia sobre imagen vacía (0 rostros) y liberación correctas. Ocho casos de lógica con señales simuladas OK: dos ciclos, imagen fija abierta/cerrada, guiño, sin reapertura, pérdida de rostro, ruido breve y pausa larga. No equivalen a una prueba de precisión con personas.
- Diagnósticos del editor: sin errores en plantilla y módulo. `git diff --check` sin errores. Servidor HTTP temporal solo para archivos estáticos; no se importó `app.py` ni se accedió a PostgreSQL.
- Pendiente: validar con cámara del usuario, ojos abiertos/cerrados y fotografía fija. No se afirma resuelto el falso rechazo hasta esta comprobación. Continúa la limitación frente a videos y la verificación pendiente de licencia exacta del modelo antes de publicación.

ANTECEDENTE DEL PRIMER AJUSTE:

- Se observó rechazo del reto pese a detectar el rostro. El código usaba una sola muestra de referencia y una espera adicional de 180 ms entre análisis; podía perder cierres rápidos. No se midió el rendimiento de la cámara del usuario.
- Ajuste mínimo en `templates/preparacion.html`: calibración con varias muestras, eliminación de la espera fija, instrucciones de cerrar los ojos un segundo y abrirlos dos veces, 30 segundos y contador visible. Se mantienen los umbrales relativos de cierre/apertura y se reinicia la detección incluso ante errores. El rechazo ya no sugiere uso de una foto.
- El navegador también reportó `NotReadableError: Device in use`; se distingue ese fallo de un permiso denegado y se indica liberar la cámara en otras pestañas/aplicaciones.
- Prueba aislada en navegador con observaciones simuladas: 5/5 casos OK (dos cierres, imagen inmóvil, un cierre, ausencia de reapertura, pérdida de rostro). El primer intento del ejecutor falló por `Illegal return statement`; corregido el ejecutor, los cinco casos pasaron. No prueba precisión biométrica ni cámara real.
- No se importó la aplicación ni se ejecutaron migraciones para esta corrección. Pendiente: repetir la verificación con cámara real y comprobar falsos rechazos.

ESTADO: Implementada y verificada en base aislada; pendiente de prueba manual con cámara y celular reales.

IMPLEMENTADO:
- En la tercera salida de foco, cierre provisional y revisión humana; advertencias y motivo visibles para el alumno. El servidor cuenta episodios únicos y controla el cierre.
- Detección opcional de celular mediante MediaPipe ObjectDetector y EfficientDet Lite0 cargados desde archivos locales. Diez segundos de observaciones continuas recibidas por el servidor abren revisión, sin anulación automática.
- Reto de parpadeo en preparación para advertir sobre posible foto inmóvil; consentimiento específico para detector de celular.
- Panel de administrador para confirmar anulación o reponer resultado con nota y auditoría. Resultados pendientes fuera del ranking.
- Cierre y calificación desde respuestas, área y tiempo del servidor en una transacción, con control de intentos concurrentes y repetidos. Respuestas rechazadas tras cierre.

ARCHIVOS:
- Backend: `models/database.py`, `models/supervision.py`, `models/intento.py`, `models/resultado.py`, `models/usuario.py`, `routes/api.py`, `routes/resultados.py`, `routes/simulacro.py`, `config.py`.
- Interfaz y detector: `templates/admin.html`, `templates/examen.html`, `templates/preparacion.html`, `templates/resultado.html`, `static/js/monitor_engine.js`, `static/js/modulos/focus_monitor.js`, `static/js/modulos/phone_monitor.js`, `static/models/mediapipe/`.
- Pruebas y documentación: `tests/test_supervision.py`, `.env.example`, `docs/REGLAS.md`, este documento.

VERIFICACIÓN:
- `tests.test_supervision` en `unmsm_proctor_test` de `127.0.0.1:5432`, con identidad de base comprobada antes de importar `app.py`: 8 pruebas, todas OK. Incluyen tercer cambio, duplicados, CSRF, alteración de datos de cliente, concurrencia, autorización y revisión humana.
- En navegador de pruebas, el modelo local de celular cargó y cerró correctamente; los tres módulos JavaScript compilaron.
- `git diff --check`: sin errores de espacio; Git anunció conversión futura LF/CRLF.

LÍMITES Y PENDIENTES:
- Falta prueba manual con webcam, fotografía y celular reales, y medir falsos positivos/negativos. El parpadeo no es una prueba de vida infalible; una detección desde el navegador tampoco constituye prueba irrefutable.
- Una web no puede enumerar otras pestañas o navegadores; solo se cuentan pérdidas de foco/visibilidad observadas.
- Verificar política de privacidad y licencia del modelo exacto antes de un despliegue público. La biblioteca MediaPipe puede enviar métricas técnicas según su documentación; el consentimiento lo informa.
- No se creó commit ni se hizo push. Se preservaron modificaciones previas del usuario en `README.md`, `docs/PROGRESO.md` y `docs/guia_portabilidad.md`.

## Fotografías para la revisión de celular — 2026-10-11

ESTADO: Implementado y probado con imágenes simuladas; pendiente de comprobación con webcam y celular reales.

- El detector intenta capturar cuatro imágenes por episodio sostenido, aproximadamente en los segundos 1, 3, 7 y 10. El administrador las ve en el informe de resultado del caso pendiente. El alumno ve el motivo de revisión, pero no puede consultar las fotografías por la ruta administrativa.
- Se exige consentimiento nuevo `celular-v2-fotos`. El servidor valida sesión, CSRF, intento abierto, propietario y observaciones recientes del mismo episodio. Normaliza JPEG, elimina metadatos, cifra los archivos en `instance/evidencias/` y conserva registros con caducidad de 30 días. Hay límite de tamaño, cantidad e idempotencia por episodio y momento. El esquema se amplió de forma aditiva con `evidencias_celular`.
- Se añadió `scripts/purgar_evidencias.py` para purga programada, dependencias Pillow/cryptography, volumen Docker y exclusión de Git. El procedimiento de operación y la limitación probatoria se documentan en `docs/EVIDENCIAS.md`; la tarea diaria debe configurarse en cada instalación.
- Archivos de esta ampliación: `models/evidencia_celular.py`, `models/database.py`, `routes/api.py`, `routes/resultados.py`, `routes/simulacro.py`, `templates/preparacion.html`, `templates/resultado.html`, `templates/admin.html`, `static/js/monitor_engine.js`, `static/js/modulos/phone_monitor.js`, `scripts/purgar_evidencias.py`, `tests/test_supervision.py`, `requirements.txt`, `docker-compose.yml`, `.gitignore`, `README.md`, `docs/REGLAS.md` y `docs/EVIDENCIAS.md`.
- Verificación: `tests.test_supervision` en `unmsm_proctor_test` de `127.0.0.1:5432`, cuya identidad se comprobó antes de importar `app.py`: 9 pruebas OK. Incluyen cifrado, carga repetida, acceso exclusivo de admin, CSRF, JPEG inválido y rechazo de una captura de 10 s prematura. Pruebas aisladas en navegador: secuencia 1/3/7/10 y envío multipart JPEG OK. La primera ejecución de la prueba de navegador requirió simular `crypto.randomUUID` por ejecutarse en `about:blank`; con ese entorno corregido pasó.
- Pendientes: medir con cámara real si las capturas y la revisión se ven como se espera; programar la purga diaria; validar política de privacidad antes de uso público. Las imágenes proceden del navegador y pueden alterarse; son indicios para revisión humana, no prueba concluyente. No se creó commit ni se hizo push.

## Ajuste visual de preparación e informe — 2026-10-11

ESTADO: Cambios de presentación implementados; pendiente de inspección manual en navegador.

- El encabezado muestra “UNMSM” y “Simulacro tipo admisión” sin el monograma anterior. Se ajustó la tipografía del encabezado sin cambiar navegación ni rutas.
- La declaración conserva dos aceptaciones separadas y los textos completos de entorno y detección de celular, ahora en un panel desplegable de lectura. No cambian las condiciones, el consentimiento registrado ni los controles del examen.
- Las fotografías y observaciones de supervisión aparecen antes de la revisión académica en el informe. La galería sigue siendo exclusiva del administrador.
- Archivos: `templates/base.html`, `static/css/base.css`, `templates/preparacion.html` y `templates/resultado.html`. Verificación: tres plantillas Jinja compiladas, diagnósticos del editor sin errores y `git diff --check` sin errores. Falta revisar la presentación con diferentes tamaños de pantalla y el flujo con cámara real.

## Inicio justo del tiempo y comprobación de presencia — 2026-10-11

ESTADO: Implementado; pruebas automatizadas en base aislada, pendiente de ensayo con cámara y teléfono reales.

- Antes, la preparación o el GET del examen creaban el intento y fijaban su vencimiento mientras cámara/modelos y preguntas aún cargaban. Ahora el GET sin intento activo solo muestra verificación; no crea intento ni entrega preguntas. La API protegida con CSRF fija el reloj y entrega preguntas sanitizadas cuando la preparación está lista; ignora la duración enviada por el cliente. Se bloquea el usuario en PostgreSQL para que peticiones simultáneas recuperen el mismo intento. Una recarga de un intento activo conserva su vencimiento.
- Una foto estática del rostro puede coincidir biométricamente. El monitor ahora distingue coincidencia de presencia y propone retos oculares variables durante el examen. Un reto no confirmado registra un evento idempotente y deja el resultado para revisión humana, sin anulación automática. El informe muestra el motivo correcto.
- Archivos funcionales: `models/intento.py`, `models/supervision.py`, `routes/api.py`, `routes/simulacro.py`, `templates/preparacion.html`, `templates/examen.html`, `static/js/monitor_engine.js`, `static/js/modulos/blink_challenge.mjs`, `static/js/modulos/facial_presence.js`, `static/css/examen.css`, `tests/test_supervision.py`. Reglas en `docs/REGLAS.md`.
- Pruebas: `tests.test_supervision` con identidad verificada de `unmsm_proctor_test`: 12 pruebas OK, incluidas activación simultánea, CSRF, ausencia de preguntas antes del inicio y motivo de revisión ocular. Plantillas Jinja `examen.html` y `preparacion.html` compilaron. Node no está instalado en este equipo, así que no se ejecutó `node --check`; se revisaron diagnósticos del editor.
- Pendientes: validar webcam, tiempos de carga, recarga y falsos rechazos del reto con usuarios reales. La prueba ocular no es un sistema PAD certificado y no garantiza detectar video o una cámara virtual. No se hizo commit ni push.

## Justificación visible al alumno tras revisión — 2026-10-11

ESTADO: Implementado y probado con base aislada.

- El alumno puede ver en su propio resultado la decisión definitiva del administrador y la justificación escrita, tanto al confirmar una anulación como al reponer el examen. La consulta se hace después del control de propiedad del resultado y no expone identificadores del administrador. El texto se escapa en la plantilla.
- El título de una anulación confirmada ya no dice «provisionalmente»; un examen repuesto se identifica expresamente. Durante una revisión pendiente no se muestra una nota que aún no existe.
- Archivos: `models/resultado.py`, `routes/resultados.py`, `templates/resultado.html`, `tests/test_supervision.py`. Pruebas: `tests.test_supervision` en `unmsm_proctor_test`, 12 casos OK, incluida la comprobación de escape HTML. No se hizo commit ni push.

## Primera foto al detectar celular — 2026-10-11

ESTADO: Captura adelantada al fotograma positivo; pendiente de prueba con teléfono real.

- Antes, el monitor esperaba la respuesta de `/api/intento/celular` y solo entonces tomaba la foto; el teléfono podía salir del cuadro durante esa espera. Ahora congela el fotograma de la primera detección antes de esperar a la red y sube la imagen después de confirmar el evento. La alerta, la evidencia y el conteo parten de la misma observación. Conserva las otras tres capturas y el consentimiento actual.
- Archivos: `static/js/modulos/phone_monitor.js`, `static/js/monitor_engine.js`, `templates/resultado.html`, `docs/EVIDENCIAS.md`, `docs/REGLAS.md`. El informe identifica la primera imagen como «Primera detección». No se modificaron esquema ni permisos.
- Verificación aislada en navegador: el callback de captura se ejecutó entre el envío del evento y su confirmación (`event`, `snapshot-1`, `confirmed`, `upload-1`). En una prueba con un lienzo rojo cambiado a azul antes de la confirmación, el JPEG enviado conservó el fotograma rojo inicial y no se envió antes de confirmar. No se usó la webcam real.
- Pendiente: comprobar con webcam y teléfono reales si el detector reconoce el dispositivo y si el fotograma inicial lo muestra. La inferencia ocurre aproximadamente cada segundo y puede omitir detecciones breves; una captura nunca demuestra por sí sola una infracción. No se hizo commit ni push.
## Cien preguntas originales por área B, C, D y E — 2026-10-25

ESTADO: Cuatro bancos y vista de revisión implementados y comprobados; integración al examen supervisado pendiente.

- Alcance confirmado: 100 preguntas por área siguiendo la organización del área A. Cada banco contiene 10 actitudinales, 10 de HV y 80 de los demás cursos, organizados en 19 cursos. HV utiliza tres lecturas originales por área, doce textos distintos en total, sin imágenes. Preguntas con cinco opciones, clave y explicación; 15 figuras SVG de apoyo en Geometría entre las cuatro áreas.
- El material se identifica como práctica original. Las cuotas son editoriales, sin atribución oficial. Hay contenidos generales compartidos entre áreas y problemas numéricos con datos diferentes; no se afirma que sean 400 enunciados independientes ni un instrumento psicométrico validado.
- Archivos nuevos: `scripts/generar_areas_bcde.py`, `data/examenes/lecturas_originales_bcde.json`, cuatro bancos privados `area_*_practica.json`, cuatro JSON públicos en `static/practica/`, `static/vista_previa_areas.html`, `static/js/vista_previa_areas.js`, `tests/test_areas_bcde.py` y `docs/PRACTICA_AREAS_BCDE.md`. Accesos añadidos al dashboard y guía enlazada en README. Se preservaron los cambios anteriores del área A.
- Validación: `python -m unittest tests.test_areas_bcde tests.test_importacion_area_a -v`: 19 casos OK. Cobertura 1–100, 19 cursos, opciones únicas, claves privadas, lecturas distintas sin imágenes y cálculos independientes de los problemas numéricos. Regeneración determinista: ocho JSON idénticos por SHA-256. Dashboard analizado con Jinja; diagnósticos de Python, HTML y JS sin errores; `git diff --check` sin errores.
- Navegador: recorrido programático de las 400 preguntas, cinco opciones y enunciado en todas; 100 botones/19 cursos por área; 4/5/3/3 figuras respectivamente y cero imágenes en HV; sin errores JavaScript durante el recorrido. Selección C conservada al avanzar/volver y cambiar E→B→E. A 390 px no hay desbordamiento en 1, 11, 14, 17, 34, 35 y 100 del área E (ancho útil/scroll: 383/383). El primer acceso ocurrió antes de iniciar el servidor; se reutilizó la tarea estática existente. Un recorrido con clic físico y una espera basada en animación agotaron el tiempo en la pestaña no visible; se repitió con clic DOM y sondeo temporal, sin alterar el producto por ese fallo de prueba.
- La vista no califica ni crea intentos. Los bancos activos antiguos siguen intactos: el examen califica actualmente por área sin versión, y sustituirlos podría reinterpretar respuestas de intentos en curso. No se importó Flask ni se accedió a PostgreSQL; sin cambios de esquema, supervisión, resultados, commit ni push.

## Correcciones autorizadas de 47 y 71 — 2026-10-25

- Corregidas D de 47 a «sé - mas - sí - mí» (clave D) y B de 71 a «El efecto invernadero» (clave B). Ambas dejan de figurar como pendientes. Se conserva el material extraído original como referencia.
- Actualizados edición, banco privado, JSON/JS públicos, generadores, aviso de la vista y documentación. El banco activo del simulacro todavía no se sustituye; continúa pendiente su integración con la versión nueva sin reinterpretar intentos históricos.
- Validación: 14 pruebas de `tests.test_importacion_area_a` OK, incluidos valores exactos de opciones, claves y exclusión de claves públicas; diagnósticos Python sin errores. La primera ejecución detectó pérdida de tildes en la entrada estándar de PowerShell; corregida mediante escapes Unicode antes de repetir las pruebas. Sin importar Flask ni acceder a PostgreSQL.

# Vista previa del PDF del área A — 2026-10-25

ESTADO: Incorporada al proyecto y comprobada en navegador; pendiente de valoración visual del usuario y de recibir claves para una futura versión calificada.

- Alcance autorizado: insertar primero el documento del área A para revisar cómo queda antes de incorporar otras áreas. Se añadió una vista estática del proyecto enlazada desde el dashboard, con 90 preguntas (11–100), numeración original, imágenes de enunciados/fórmulas/alternativas, selección A–E, navegación y 22 páginas académicas de referencia. La portada excluye Medicina Humana. El PDF no contiene preguntas 1–10 ni claves; se corrigió la suposición inicial de que contenía las 100 preguntas.
- Las preguntas 37, 57, 67, 83, 90 y 91 tienen un recorte adicional de continuación. Los márgenes de páginas pares e impares se calculan desde los encabezados reales. Se conserva el texto extraído en los datos para consulta y el hash del original.
- Archivos: `scripts/importar_pdf_area_a.py`, `static/vista_previa_area_a.html`, `static/js/vista_previa_area_a.js`, `static/css/importacion.css`, `static/importaciones/unmsm-2026-i-a/`, `templates/dashboard.html`, `docs/IMPORTACION_AREA_A.md` y este seguimiento.
- Comprobaciones: ejecución real del importador; validación de IDs únicos 11–100, existencia de todas las imágenes y alternativa E en cada texto completo; sintaxis Python OK; diagnósticos del editor sin errores; plantilla Jinja del dashboard compilada; `git diff --check` OK. En navegador: marcar B en 11 y C en 29, recuperar B al volver, limpiar selección, límite de navegación en 100; cargar continuación de 37 y recuperar D tras navegar; pantalla de 390 px sin desbordamiento horizontal (ancho útil y scroll: 383 px).
- La primera comprobación de alternativas detectó cortes por los márgenes y continuaciones entre columnas; se corrigieron y se repitieron las verificaciones. El texto de la alternativa A de la pregunta 50 carece de paréntesis en la capa de texto original; se conserva la imagen original.
- Se inició una vista estática local en `http://127.0.0.1:8765/vista_previa_area_a.html` usando una tarea de VS Code en el workspace padre. No se importó `app.py`, no se accedió a PostgreSQL y no se modificó el banco calificado, esquema ni supervisión. No se hicieron commits ni push. No se ejecutó el flujo Flask autenticado completo; se comprobó el enlace por compilación de plantilla y la vista mediante servidor estático.

## Diez preguntas actitudinales y PDF de respuestas — 2026-10-25

ESTADO: 100 preguntas visibles; claves transcritas en banco privado de revisión. Calificación del banco nuevo pendiente por ambigüedades del material recibido.

- Se crearon diez situaciones originales de práctica, con cinco opciones, clave y justificación, sobre inteligencia emocional, ética, empatía, liderazgo y vocación. Identificadas como creación original, sin atribución oficial ni validación psicométrica. Contenido y claves en `data/examenes/actitudinales_area_a.json`; documento legible en `docs/PREGUNTAS_ACTITUDINALES_AREA_A.md`.
- El PDF de respuestas tiene seis páginas. Se extrajo el texto y se inspeccionaron visualmente las tres páginas académicas. Aparece una entrada 21 vacía y las respuestas posteriores están desplazadas: respuesta publicada 22 = pregunta 21, hasta publicada 101 = pregunta 100. Las letras se cotejaron con el contenido de las alternativas, conservando número de procedencia y SHA-256 del PDF en `data/examenes/area_a_2026_i_revision.json`.
- Pendientes expresos: pregunta 47 tiene alternativas A y D idénticas que coinciden con el texto de la respuesta; se deja clave única nula y se registran ambas coincidencias. En la 71 se transcribe B, pero el solucionario repite el texto de la respuesta anterior; requiere revisión académica. Las demás claves reflejan el documento, sin auditoría independiente de su corrección científica.
- `scripts/completar_area_a.py` regenera el banco de revisión y la vista pública de 100 preguntas. No es un extractor genérico de solucionarios. Las claves y justificaciones no aparecen en los datos públicos. Se actualizó el aviso de la vista y el acceso del dashboard; la interfaz distingue preguntas textuales originales y recortes del PDF.
- Pruebas: `python -m unittest tests.test_importacion_area_a -v`: 5 pruebas OK, sin importar Flask ni acceder a bases de datos. Comprueban IDs 1–100, sanitización de JSON/JS, opciones y justificaciones originales, archivos de imágenes y desfase/ambigüedades. Diagnósticos del editor sin errores; dashboard compilado con Jinja. En navegador: 100 botones; selección C conservada al volver; transición 10→11 y alternancia entre texto e imagen correctas; referencias ocultas en originales; pantalla de 390 px sin desbordamiento. `git diff --check` sin errores.
- No se modificó el banco activo `area_a.json`, la puntuación, los intentos, los resultados ni la base de datos. El banco de revisión no está habilitado para calificar; evita reinterpretar resultados históricos o escoger una clave ambigua. Se preservaron los cambios de la vista previa del turno anterior. Sin commits ni push.

## Navegador por cursos y primera transcripción textual (HV) — 2026-10-25

ESTADO: Navegador organizado y HV en texto para revisión por bloques. Las preguntas 21–100 conservan imágenes mientras se transcriben sus respectivos cursos.

- Se atendió la referencia visual del usuario: 19 grupos de cursos, subgrupos Texto N.º 1 (11–13), Texto N.º 2 (14–17) y Texto N.º 3 (18–20), con 100 botones únicos y estados de pregunta actual/respondida. Incluye Actitudinales 1–10. Los rangos posteriores a HV se ajustaron al examen real: H.L.M. 21–30 y Biología 93–100, entre otros; no se propagó el desfase del solucionario a los botones. La decisión se comunicó durante el trabajo.
- HV muestra párrafos de lectura compartida, enunciados y cinco alternativas como texto. Texto 2 conserva A y B; Texto 3 conserva el inglés. La infografía del Texto 1 se recortó completa como figura independiente. Se restituyó la última línea de la alternativa E de la pregunta 18 y se separaron I, II y III en la 16. Las páginas de referencia solo cargan bajo demanda.
- Fuente de edición en `data/examenes/edicion_area_a.json`, extracción específica en `scripts/preparar_textos_area_a.py`; el completador reaplica la edición al regenerar los datos. Actualizados JSON/JS público, banco privado de revisión, HTML/CSS/JS de la vista, pruebas y documentación. Se preservan los cambios anteriores y las claves privadas.
- Verificación: `python -m unittest tests.test_importacion_area_a -v`: ocho pruebas OK, incluidos cobertura única por cursos, tres lecturas y figura existente. Regeneración por `completar_area_a.py` conserva la edición. Diagnósticos de los archivos editados sin errores. En navegador: 19 cursos/100 botones, lectura compartida 11→13, Texto A/B en 14 y Texto 3 en 18, alternativas textuales, selección A conservada al volver a 11, estado marcado, pregunta 100 actual, recorte de 21 cargado y página original de referencia cargada al abrir el panel. Sin desbordamiento a 390 px.
- Una comprobación inicial de navegador consultó la visibilidad antes de terminar la carga y llamó a `decode()` antes de que el evento `toggle` asignara la imagen; falló por sincronización. Al esperar las imágenes reales, se confirmaron tanto el recorte pendiente como la referencia. No se cambió el producto por ese fallo de prueba.
- Pendiente: continuar la transcripción revisada de los demás cursos, conservando solo figuras necesarias. No se modificó el banco activo, calificación, esquema ni base de datos; no se hizo commit ni push.

## Enunciado destacado y alternativas agrupadas — 2026-10-25

- Se destacó la pregunta en un bloque con fondo suave, borde lateral vino, título dinámico «Pregunta N», instrucción breve y enunciado de mayor tamaño y peso. Las alternativas y el estado de selección quedan dentro del mismo bloque. La referencia al PDF se movió después de las respuestas para no interrumpir lo que debe contestarse.
- Archivos: `static/vista_previa_area_a.html`, `static/css/importacion.css`, `static/js/vista_previa_area_a.js` y este seguimiento. Cambio de presentación; sin modificación del contenido ni de la calificación.
- Verificación en navegador: pregunta 11 con cinco alternativas agrupadas, enunciado destacado con peso 650 (17 px en la ventana inicial; CSS de escritorio: 19 px), referencia posterior al bloque, selección B conservada y título actualizado al pasar a 12. Pantalla de 390 px sin desbordamiento horizontal. Diagnósticos del editor sin errores. Sin acceso a base de datos ni importación de Flask.

## Transcripción completa, figuras separadas y clics dentro de la página — 2026-10-25

ESTADO: 100 preguntas con enunciados y alternativas textuales en la vista previa. Solo figuras necesarias, una cuadrícula SVG y una tabla HTML.

- Se convirtieron 21–100 a texto, conservando 14 figuras recortadas del PDF para 21, 26, 27, 28, 29, 30, 35, 36, 37, 41, 81, 83, 84 y 91. La repetición de 83 se tomó una sola vez; se añadió la 84 por requerir esquema. En la 24 se reconstruyó la cuadrícula de borde mediante SVG con 16 casillas, cotejada con la original. Se inspeccionaron los recortes en conjunto y se corrigió el margen superior de la 81 para conservar la etiqueta B.
- Se cotejaron visualmente los símbolos complejos de las preguntas 34–42, 83 y 84; se normalizaron raíces, potencias, π, conjugados, vectores, fracciones y fórmulas químicas. Se conserva el cm³ impreso en el dato de área de la 36, sin corregir el contenido académico. Tabla HTML en 90; proposiciones de 91 después de las moléculas; ocho palabras subrayadas en 49. Claves y pendientes 47/71 intactos.
- Se eliminaron enlaces de imágenes y navegación externa de citas en la vista; la referencia al PDF se abre en un panel de la misma página. No se cambió el detector de supervisión. El dashboard describe ahora textos y figuras.
- Archivos: `scripts/convertir_area_a_texto.py`, `scripts/preparar_textos_area_a.py`, `data/examenes/edicion_area_a.json`, banco privado de revisión y datos públicos regenerados, 14 PNG de figuras, HTML/CSS/JS de la vista, dashboard, pruebas y documentación. El preparador de HV preserva la edición de otros cursos.
- Pruebas: `python -m unittest tests.test_importacion_area_a -v`: 11 pruebas OK. En navegador se recorrieron las 100 preguntas, todas con enunciado textual visible y cinco alternativas; 14 figuras decodificadas, SVG de 16 casillas, tabla de seis filas, continuación de vitaminas, selección C conservada al volver a 29 y sin desbordamiento a 390 px. Clic en SVG y figura: una pestaña antes y después; cero enlaces que contengan imágenes. Prueba adicional: 49 conserva lisa/lisa, peón/peón, raya/raya y servía/servía subrayados. Dashboard compilado con Jinja; diagnósticos sin errores; diff sin errores de espacios.
- No se importó Flask ni se accedió a PostgreSQL. La comprobación no ejecuta un examen con cámara real ni certifica el detector. Banco activo y resultados históricos intactos; sin commits ni push. Pendiente de revisión visual del usuario y resolución de las claves académicas ya señaladas.

## Esquemas vectoriales limpios y fórmulas legibles — 2026-10-25

ESTADO: Figuras de preguntas reconstruidas en SVG; notación matemática estructurada y fechas de la 64 corregidas. Listo para revisión visual del usuario.

- Se reconstruyeron las 14 figuras antes rasterizadas con trazos y etiquetas SVG basados en las coordenadas del PDF, omitiendo la capa editorial de fondo. No hay raster incrustado en los SVG. Las marcas de la fuente original siguen intactas en las páginas de referencia. La cuadrícula 24 permanece como SVG nativo y la infografía de HV se muestra como ocho pasos HTML accesibles con su atribución.
- La primera exportación omitió segmentos de bbox de área cero y puntos inline del dominó. Se corrigió la selección de trazos expandiendo su bbox y se reconstruyeron 26 puntos como círculos. Los detalles inline de latas y movimiento se trazaron en superficies vectoriales; el agua de 83 usa un contorno y gradiente. Se cotejaron láminas de los 14 gráficos con las figuras fuente. No se afirma que todo haya sido dibujado manualmente desde cero.
- Se añadió `static/js/formato_academico.js`, un renderer local limitado a la notación anotada de este banco, con MathML nativo: fracciones, subíndices, potencias, raíces, conjugados y vectores. Se anotaron las expresiones complejas de 23, 29, 34–39, 41–42 y 81–85. La 38 conserva los valores y proposiciones originales, no se resuelve ni se cambia su clave. La 64 no tenía una ecuación: se corrigieron saltos artificiales en «a. C.» y «d. C.». Las unidades µT de las opciones de 84 y el exponente −5 se conservan.
- La pregunta 39 desbordaba en pantalla estrecha con su fórmula completa; se añadió desplazamiento horizontal dentro de la expresión, sin ensanchar la página. Algunas comprobaciones iniciales de clic/estabilidad en la pestaña integrada agotaron el tiempo; la navegación programática y el recorrido posterior de las 100 preguntas completaron la verificación. La primera ejecución mediante `runpy` necesitó añadir `scripts` al path de esa invocación para localizar el importador.
- Archivos: `scripts/refinar_graficos_area_a.py`, renderer de matemáticas, HTML/CSS/JS de vista, edición estructurada y datos regenerados, 14 SVG, pruebas y documentación. No se borraron los recortes originales ni se modificó el banco activo, claves, esquema, supervisión o resultados.
- Pruebas: `python -m unittest tests.test_importacion_area_a -v`: 13 casos OK. Incluyen SVG sin `image`/`data:image`/color editorial, 26 puntos, etiquetas de moléculas, fórmulas anotadas y fecha de 64. Navegador: 100 preguntas con cinco opciones, sin errores JavaScript; 38 con dos fracciones/dos barras de conjugado y subíndices; 84 con seis exponentes y dos acentos vectoriales. Sin desbordamiento a 390 px en 23, 34, 36, 38, 39, 42, 83, 84 y 85. Captura local de 38 inspeccionada. Sin acceso a PostgreSQL, importación de Flask, commit ni push.
## Infografía de HV y correcciones de las preguntas 34 y 41 — 2026-10-25

- Se restauró la infografía aportada por el usuario como imagen compartida por las preguntas 11–13, sustituyendo las ocho tarjetas HTML. El texto de las preguntas y alternativas permanece seleccionable.
- La 34 presenta el numeral aa0b5 unido y con una barra continua sobre todas sus cifras. Se usa texto matemático con decoración superior porque el acento MathML no se estiraba en el navegador integrado; comprobado con captura visual.
- La 41 conserva el precio literal $10 y muestra únicamente radio y π como fórmulas. El renderer distingue dólares escapados de delimitadores matemáticos, evitando convertir la prosa en una ecuación.
- Generador y datos públicos/privados actualizados para conservar estos cambios al regenerar. Verificación: 14 pruebas unitarias; comprobaciones de navegador en 11–13, 34 y 41, cinco alternativas por pregunta. Sin importar Flask ni acceder a PostgreSQL.

## Sustitución de infografía borrosa — 2026-10-25

- La imagen JFIF suministrada antes ya contenía dos párrafos borrosos; la comprobación anterior no verificó esa legibilidad. Se sustituyó por el PNG legible adjuntado en este turno, compartido por 11–13. Referencias públicas, privadas y generador actualizadas. Se conserva el archivo anterior sin usarlo. Sin cambios de preguntas, claves ni base de datos.
- Verificación: SHA-256 idéntico entre adjunto y copia; navegador confirma PNG de 732 × 1024 cargado en 11, 12 y 13, sin enlace externo.
