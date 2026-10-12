# Progreso

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
