# Auditoría inicial — plataforma de simulacros UNMSM

**Fecha:** 2026-10-07  
**Alcance:** inspección estática del repositorio y ejecución de pruebas aisladas. Complementada con `C:\Users\Sergio\Downloads\ESPECIFICACION.md` y `C:\Users\Sergio\Downloads\REGLAS.md`, leídos como referencias de requisitos el 2026-10-07. No se modificó código funcional ni se consultó una base de datos real.

## 1. Resumen ejecutivo

Existe una aplicación Flask funcional en estructura, con PostgreSQL, cinco bancos JSON de preguntas, examen con autoguardado, biometría local en el navegador, resultados, ranking y panel administrativo. La implementación cubre parcialmente la especificación de fase 0, pero hay defectos de autorización y de cierre que impiden considerar confiables los resultados. La afirmación de `docs/informe_final_entrega.md` de que todas las fases están completadas no está demostrada por las pruebas disponibles.

**Referencias:** la matriz de la sección 5 corresponde a `docs/especificacion_fase_0.md` y se conserva como antecedente. La matriz ampliada de la sección 9 compara la especificación nueva y `REGLAS.md` entregados inicialmente desde `Downloads`. El 2026-10-07, durante la preparación autorizada del entorno, se incorporaron sus copias completas a `docs/ESPECIFICACION.md` y `docs/REGLAS.md`, además de `AGENTS.md` en la raíz; se comprobó identidad de contenido con SHA-256. La especificación nueva cambia requisitos de fases anteriores: exige MediaPipe/ONNX, consentimiento, invitaciones y control de sanciones en servidor. No se asume que el código existente deba sustituirse automáticamente.

## 2. Arquitectura, árbol resumido y tecnologías

```text
app.py, config.py               Fábrica Flask, configuración y middleware
routes/                         auth, dashboard, simulacro, api, resultados
models/                         SQL directo con psycopg2 y pool de conexiones
utils/                          puntuación, catálogo, ayudas y descarga de modelos
templates/                      11 vistas Jinja2, JavaScript en línea
static/css/, static/js/          estilos y motor de examen/supervisión
static/models/                  face-api.js, pesos y archivos ONNX/WASM
data/examenes/                  bancos JSON A–E
tests/                          unittest y ensayo HTTP de concurrencia
docs/                           especificación de fase 0 y guías
Dockerfile, docker-compose.yml  despliegue local con PostgreSQL 16
```

Stack observado: Python 3.11, Flask 3, Jinja2, psycopg2, PostgreSQL, JavaScript de navegador, face-api.js, Werkzeug para hash de contraseñas y Gunicorn en `Procfile`. `requirements.txt` usa mínimos sin versiones fijadas. El código usa scripts globales y JavaScript en línea; la recomendación de ES2020+ con módulos nativos de las instrucciones recibidas aún no se cumple. `Dockerfile` inicia el servidor de desarrollo de Flask mientras `Procfile` usa Gunicorn.

## 3. Funcionalidad encontrada

- Registro sin cámara, autenticación con hash Werkzeug, sesiones Flask y áreas/carreras (`routes/auth.py`, `models/usuario.py`).
- Preparación con cámara, enrolamiento/verificación local y examen por área (`routes/simulacro.py`, `templates/preparacion.html`).
- Cinco bancos JSON, sanitización de claves para la vista de examen y puntuación +20/−1.125/0 con piso cero (`utils/preguntas.py`).
- Intentos con vencimiento, guardado incremental en PostgreSQL y recuperación de respuestas (`models/intento.py`, `routes/api.py`).
- Monitor facial, de foco y de captura; telemetría, resultados, ranking y estadísticas de administrador (`static/js/`, `models/resultado.py`, `routes/resultados.py`).
- Archivos locales de face-api.js comprobados por `tests/test_modelos.py`; assets ONNX/WASM presentes, sin integración de producción identificada.

## 4. Funcionalidad parcial, faltante y defectos prioritarios

### Críticos

1. **Cierre falsificable:** `POST /api/guardar-resultado` acepta `area`, `respuestas`, `estado`, `motivo_anulacion` y parte del tiempo del cliente. Si no existe intento, continúa por una ruta alternativa; si existe, no verifica que pertenezca al usuario, coincida con el área, siga abierto ni esté dentro del plazo. Un token conocido permite consultar un resultado ajeno por la respuesta idempotente. Evidencia: `routes/api.py:65-200`. La calificación debe basarse exclusivamente en respuestas y examen vinculados al intento autorizado.
2. **Anulación desde el navegador:** el mismo endpoint admite `estado='ANULADO'` y motivo libre, contradiciendo la revisión humana declarada. No hay acción administrativa para validar o anular con justificación (`routes/api.py`, `routes/resultados.py`).
3. **Inicio sin verificación exigible:** `/examen/<area>` crea un intento con GET y `/api/intento/iniciar` permite iniciarlo directamente, con duración elegida por el cliente. Ninguno comprueba una acreditación biométrica antes de crear el intento (`routes/simulacro.py:79`, `routes/api.py:224`). El reloj puede arrancar antes de la confirmación prevista.
4. **Credenciales y configuración sensibles incorporadas al código:** `config.py` contiene claves de respaldo y URL de base con contraseña; `docker-compose.yml` incorpora contraseñas y secreto. Requiere sustitución controlada y rotación si se usaron fuera de desarrollo. Este informe omite sus valores.

### Altos

5. **Cierre sin transacción única:** `cerrar_intento`, `guardar_resultado` y `asociar_eventos_a_resultado` hacen commits separados. `cerrar_intento` no condiciona `UPDATE` a `EN_CURSO`; un fallo intermedio puede dejar un intento cerrado sin resultado, y una segunda entrega puede modificarlo de nuevo (`models/intento.py:145`, `models/resultado.py`, `routes/api.py`).
6. **Eventos sin vínculo fiable al intento:** `/api/evento-monitoreo` ignora `token_sesion`; los eventos se registran por usuario y luego se asocian todos los pendientes al resultado siguiente. El cliente controla `modulo`, `tipo`, descripción y segundo del examen (`routes/api.py:34`, `models/resultado.py:73-102`).
7. **Banco sin versión efectiva:** `examenes_versiones` existe, pero `crear_intento` recibe `examen_version_id=None`; examen y resultado cargan de nuevo JSON mutable. Cambiar el banco altera la revisión histórica y permite discrepancias entre examen rendido y calificación (`models/database.py`, `routes/simulacro.py`, `routes/resultados.py`).
8. **Autoguardado recuperable solo en parte:** `syncQueue` vive en memoria; tras F5, `localStorage` restaura respuestas visuales, pero no repuebla la cola. Las selecciones no confirmadas pueden perderse o entregarse solo con el payload final. `submitFinalExam` limpia el respaldo antes de confirmar éxito HTTP y redirige al dashboard ante una respuesta de error (`static/js/monitor_engine.js:430-514, 675-707`).
9. **Respuestas fuera de orden:** `numero_revision` se incrementa en el servidor, pero no se exige una revisión esperada del cliente; una petición atrasada puede sobrescribir una selección posterior. Tampoco se valida que `pregunta_id` y opción pertenezcan al banco del intento (`routes/api.py:287`, `models/intento.py:85`).

### Medios y deuda técnica

10. La consulta de intento activo excluye los vencidos; las ramas que intentan cerrarlos mediante `obtener_intento_activo` no pueden encontrarlos. Falta un cierre automático efectivo y resultado para esos intentos (`models/intento.py:37`, `routes/simulacro.py`).
11. No se encontró protección CSRF para formularios ni endpoints con sesión, limitación de intentos de login, ni `SESSION_COOKIE_SECURE` explícito en producción (`routes/auth.py`, `routes/api.py`, `config.py`). El control móvil por `User-Agent` es modificable por el cliente.
12. La tabla `usuarios` conserva `descriptores_faciales` además de `plantillas_faciales`; el enrolamiento acepta una sola muestra y no valida números finitos, rango ni límite de muestras. Las plantillas se envían a la vista y a una API autenticada para verificación local (`models/database.py`, `routes/api.py:343-402`, `templates/preparacion.html`).
13. El panel administrador muestra estadísticas, usuarios y enlaces a informes, pero no ofrece flujo de revisión, validación/anulación ni gestión de versiones y postulantes (`routes/resultados.py:121`, `templates/admin.html`).
14. `init_db()` crea/altera el esquema en cada arranque, sin migraciones numeradas; el pool global no tiene sincronización de inicialización. Hay código de preparación biométrica duplicado entre `templates/preparacion.html` y `static/js/monitor_engine.js`; `app.py` conserva un teardown vacío. Comprobar referencias antes de retirar nada.
15. Los scripts de prueba de base escriben usuarios/resultados reales y dependen de la URL activa; `tests/test_concurrencia_30.py` mide llamadas SQL directas con 30 hilos, no tráfico HTTP. Las ocho pruebas aisladas no verifican permisos, cierres transaccionales ni recuperación offline.

## 5. Matriz frente a `docs/especificacion_fase_0.md`

Leyenda: ✅ implementado; 🟡 parcial; 🔴 ausente; ⚠️ implementado con corrección necesaria; ❓ no verificable con la evidencia disponible.

| ID | Estado | Evidencia / diferencia |
|---|---|---|
| FL-01 | ✅ | Registro y login sin cámara; modelos se cargan en preparación/examen. |
| FL-02 | 🟡 | Enrolamiento y comparación 1:1 existen; se guarda una muestra y la validación es solo de cliente. |
| FL-03 | ⚠️ | Preparación no crea intento, pero GET de examen y API directa arrancan el reloj sin paso validado. |
| FL-04 | 🟡 | Se detienen tracks en flujos previstos; falta prueba de salida/recarga para todos los caminos. |
| UI-01 | ❓ | Hay estilos y prototipo; no se midió contraste ni ergonomía en navegador. |
| UI-02 | 🟡 | Hay estados de guardado y errores; no se hizo auditoría de teclado/lector de pantalla. |
| EX-01 | ⚠️ | Se eliminan claves de la vista; el banco JSON servido como archivo `data/` queda fuera de `static/`, pero no hay snapshot inmutable. |
| EX-02 | 🟡 | PostgreSQL calcula tiempo restante; resultado puede usar tiempo del cliente. |
| EX-03 | 🟡 | Upsert inmediato; falta control de orden y validación de pregunta/opción. |
| EX-04 | ⚠️ | Hay respaldo local y cola en memoria; F5 no reconstruye la cola. |
| EX-05 | ⚠️ | Token único evita duplicar resultado; el cierre no es transacción única y admite entregas inválidas. |
| EX-06 | ⚠️ | Se rechaza guardado tardío; no hay cierre automático completo de intento vencido. |
| AC-01 | ✅ | Fórmula y piso cero en `utils/preguntas.py`; seis pruebas de puntuación pasan. |
| SE-01 | 🟡 | Hash y `HttpOnly`/`SameSite=Lax`; falta endurecimiento de secretos y cookie Secure. |
| SE-02 | ⚠️ | API limita plantillas al usuario de sesión, pero quedan duplicadas y expuestas en HTML del usuario. |
| IA-01 | ✅ | Archivos locales requeridos presentes y verificados por dos pruebas. |
| IA-02 | 🟡 | Hay avisos por ausencia; no hay medición fiable de calidad de iluminación/centrado. |
| IA-03 | 🟡 | Inferencia cada 6 s y bandera contra solapamiento; sin mediciones de CPU/FPS en equipos reales. |
| MO-01 | 🟡 | Debounce y banderas por episodio en cliente; el servidor no deduplica. |
| MO-02 | ⚠️ | Se guardan avisos; la API deja al cliente anular. |
| RA-01 | ✅ | Orden puntaje desc/tiempo asc; DNI enmascarado en vista pública. |
| OP-01 | ❓ | Existe script de 30 usuarios, pero no se ejecutó contra un entorno de prueba. |

Esta matriz histórica queda ampliada por la sección 9. Los documentos se leyeron originalmente desde `Downloads` y se incorporaron después al repositorio durante la preparación autorizada del entorno.

## 6. Seguridad, regresiones y dependencias

La prioridad de seguridad es cerrar la autoridad del servidor sobre intento, tiempo, respuestas, sanción y eventos. La biometría que opera en el navegador debe tratarse como señal manipulable; no acredita identidad por sí sola. No se observó captura o envío de video al servidor, pero los vectores biométricos persisten sin política de retención o borrado documentada.

Riesgos de regresión al corregir: conservar F5 y respuestas confirmadas; no cambiar puntuaciones históricas al versionar preguntas; no asociar eventos de otro intento; mantener la idempotencia de entregas y el ranking; no bloquear usuarios sin cámara sin definir la política de admisión. `requirements.txt` permite actualizaciones mayores sin bloqueo; `pytest`, `pytest-cov` y `locust` no están declarados allí. Antes de cambiar dependencias, comprobar uso e impacto.

## 7. Pruebas y límites de la auditoría

- `python -m unittest tests.test_puntuacion tests.test_modelos -v`: **8 pruebas OK**.
- `python -m compileall -q app.py config.py models routes utils tests`: **sin errores de sintaxis**.
- `python -m pytest -q`: falla al iniciarse porque `pytest` no está instalado.
- `node --version`: Node.js no se encontró en el entorno; no se ejecutaron pruebas `node:test`.
- Pruebas de flujo con PostgreSQL y carga: no ejecutadas porque escriben datos y no se dispone de una base aislada confirmada.
- No hay carpeta `.git` en este directorio y el ejecutable `git` del entorno no arranca; no se pudo revisar un diff o historial Git. Se verificó por lectura que `docs/AUDITORIA_INICIAL.md` y `docs/PROGRESO.md` no existían antes de crearlos.

## 8. Plan recomendado para continuar

1. Las referencias ya están incorporadas a `docs/`; resolver sus diferencias con la especificación de fase 0 antes de cambios arquitectónicos.
2. Preparar una base PostgreSQL aislada y pruebas de autorización para cierre, respuestas y eventos.
3. Corregir primero la autoridad del servidor y el cierre transaccional/idempotente; definir revisión humana de observaciones.
4. Versionar bancos por intento y reparar la recuperación offline sin alterar respuestas históricas.
5. Endurecer secretos, CSRF, sesiones y retención biométrica; después validar carga y despliegue de producción.

## 9. Matriz ampliada de cumplimiento

**Fuente:** `ESPECIFICACION.md` y `REGLAS.md` ubicados en `C:\Users\Sergio\Downloads\` al auditar. Los identificadores de la primera columna son referencias de esta auditoría, no IDs del documento fuente. Estado observado por lectura estática; ✅ significa que hay implementación y prueba aislada cuando se indica, no validación integral en producción. **Prioridad/riesgo** expresa la urgencia de corregir y el riesgo de hacerlo: C/A = crítica/alto, A/A = alta/alto, M/M = media/medio, B/B = baja/bajo. En cada fila se indica código revisado, evidencia y cambio necesario.

### 9.1 Autoridad, arquitectura y stack (secciones 1–3)

| ID y requisito | Estado | Archivo / función; evidencia y problema | Cambio necesario | Prioridad/riesgo |
|---|---|---|---|---|
| P01 Servidor autoridad de tiempo, nota, estado, sanción e identidad | ⚠️ | `routes/api.py:api_guardar_resultado`, `iniciar_o_recuperar_intento`; cliente elige respuestas, área, duración y anulación; identidad se compara en JS. | Vincular cada operación a intento propio y al reloj/banco/sanciones del servidor. | C/A |
| P02 Inferencia local sin procesar video en servidor | 🟡 | `templates/preparacion.html`, `static/js/modulos/facial_presence.js`; face-api.js procesa video local, pero se transmiten descriptores. No hay flujo de evidencia. | Conservar separación de video; decidir runtime y validar/cifrar embeddings. | A/A |
| P03 Evidencia y revisión humana de anulaciones | 🔴 | `routes/resultados.py:admin_panel`; muestra informes, sin decisión/bitácora. `routes/api.py:api_guardar_resultado` acepta anulación del cliente. | Estado provisional, decisión autorizada y auditoría. | C/A |
| P04 Ausencia de señal con heartbeat | 🔴 | `static/js/monitor_engine.js:startTimer` hace GET cada 60 s; no hay POST de heartbeat ni detección de brecha. | Heartbeat de 10 s y cálculo de `sin_senal` en servidor. | A/A |
| P05 Privacidad biométrica, consentimiento, retención y cifrado | 🔴 | `models/database.py:init_db`, `models/usuario.py:guardar_plantilla_facial`; JSONB legible sin fecha de consentimiento ni política de purga. | Consentimiento persistido, cifrado, mínimo acceso y retención. | C/A |
| P06 Clave de respuestas fuera del cliente durante el examen | 🟡 | `utils/preguntas.py:sanitizar_preguntas_para_cliente`, `routes/simulacro.py:rendir_examen`; claves excluidas de la vista, pero no hay versión inmutable ni prueba HTTP integral. | Probar cada respuesta de API y congelar banco por intento. | A/M |
| P07 Límites técnicos honestos | 🟡 | `docs/informe_final_entrega.md` afirma todas las fases terminadas; falta `docs/ARQUITECTURA.md` con límites. | Rectificar afirmaciones y documentar límites reales. | M/B |
| S01 Flask 3, Blueprints y fábrica | ✅ | `app.py:create_app`, `routes/__init__.py`; patrón presente. | Verificar app en entorno aislado. | B/B |
| S02 Gunicorn gthread y pool por worker | 🟡 | `Procfile` usa Gunicorn `-w 4` sin `gthread`; `Dockerfile` ejecuta `app.py` con servidor Flask. `models/database.py` crea pool global por proceso. | Configuración única de producción, capacidad y límites medidos. | A/M |
| S03 PostgreSQL, SQL parametrizado, RealDictCursor, ThreadedConnectionPool, sin ORM | ✅ | `models/database.py:get_db_cursor`; consultas parametrizadas en `models/`. | Mantener y probar concurrencia real. | M/M |
| S04 Migraciones numeradas y tabla `schema_migrations` | 🔴 | `models/database.py:init_db` ejecuta DDL y ALTER en arranque; no existen `migrations/` ni script. | Plan de migración aditiva con respaldo y reversión. | A/A |
| S05 Werkzeug, CSRF, límites y cifrado | 🟡 | Hash en `models/usuario.py:crear_usuario`; no hay Flask-WTF, Flask-Limiter ni Fernet en `requirements.txt`. | Añadir controles por etapas con pruebas. | C/A |
| S06 Jinja/CSS/JS nativo y assets locales | 🟡 | `templates/`, `static/css/`; JS global/en línea, `templates/base.html` carga Google Fonts externo. | Modularizar y autohospedar fuentes; no exige reescritura. | M/M |
| S07 MediaPipe Tasks Vision para presencia/objetos | 🔴 | `static/js/modulos/facial_presence.js` usa face-api.js; no se encontró MediaPipe. | Decisión arquitectónica y prototipo medido antes de migrar. | A/A |
| S08 ONNX Runtime Web con embedding de 512 dimensiones | 🔴 | Hay archivos ONNX/WASM en `static/models/`, pero rutas de identidad usan face-api.js con 128 dimensiones (`routes/api.py:enrolar_plantilla_facial`). | Validar licencia/modelo y transición de plantillas si se aprueba. | A/A |
| S09 Evidencia en objetos S3 con adaptador local | 🔴 | No hay `services/evidencias.py`, tabla/endpoint ni almacenamiento de capturas. | Diseñar interfaz, política de acceso y expiración. | A/A |
| S10 pytest, node:test, locust | 🟡 | `tests/` contiene unittest y script de 30 hilos SQL; no hay suites JS ni Locust. | Añadir pruebas focalizadas y carga HTTP aislada. | M/M |
| S11 Logging JSON, `/health`, Sentry opcional | 🔴 | `app.py` configura formato texto; no hay ruta `/health` ni integración Sentry. | Observabilidad sin datos sensibles. | M/M |
| S12 Versiones exactas de dependencias | 🔴 | `requirements.txt` usa `>=`; no fija versiones. | Bloqueo reproducible tras comprobar compatibilidad/licencias. | M/M |

### 9.2 Registro, examen y modelo de datos (secciones 4–6)

| ID y requisito | Estado | Archivo / función; evidencia y problema | Cambio necesario | Prioridad/riesgo |
|---|---|---|---|---|
| F01 Registro/login/dashboard sin cámara | ✅ | `routes/auth.py`, `routes/dashboard.py`; no solicitan `getUserMedia`; prueba de registro depende de BD. | Mantener y probar por HTTP. | M/B |
| F02 Invitaciones, contraseña ≥10, cambio forzado e importación CSV | 🔴 | `routes/auth.py:register` admite 6 caracteres y no solicita código; no hay importación ni cambio forzado. | Diseño de invitaciones, migración y flujos de cuenta. | A/A |
| F03 Área y horario de simulacros | 🔴 | `routes/dashboard.py:dashboard_view` lista áreas estáticas; no hay `simulacros` ni ventanas `abre_en/cierra_en`. | Catálogo persistido y permisos de horario. | M/A |
| F04 Consentimiento explícito con fecha y versión antes de cámara | 🔴 | `templates/preparacion.html` contiene reglas/checks técnicos, no consentimiento persistido; `models/database.py` carece de campos. | Formulario y registro verificable previo a `getUserMedia`. | C/A |
| F05 Cámara solo en sala de verificación | ⚠️ | `templates/preparacion.html` la usa allí, pero `static/js/monitor_engine.js` también la solicita en modal de `templates/examen.html`. | Unificar flujo y mantener cámara durante monitoreo sin pedir permiso fuera de la sala. | A/M |
| F06 Pruebas de cámara, luz, red y benchmark | 🟡 | `templates/preparacion.html` prueba cámara/detección; no mide red, luz o latencia de inferencia. | Instrumentar indicadores y errores medibles. | M/M |
| F07 Enrolamiento 3–5 poses pendiente de supervisor | ⚠️ | `templates/preparacion.html` envía un descriptor; `routes/api.py:enrolar_plantilla_facial` acepta ≥1 y `models/usuario.py` marca `AUTO_ENROLADO`. | Validar 3–5 muestras, pendiente/aprobación/revocación. | A/A |
| F08 Verificación 1:1 con reto de vida y servidor | ⚠️ | `templates/preparacion.html` compara con face-api.js en cliente; no hay reto de vida ni verificación servidor. | Servicio de similitud calibrado y acreditación de un uso/TTL. | C/A |
| F09 Solo un intento por usuario/simulacro y sesión única | 🔴 | `models/intento.py:crear_intento` no tiene `simulacro_id` ni restricción única; `routes/auth.py:login` no invalida sesiones previas. | Restricciones de BD y sesión actual con prueba concurrente. | C/A |
| F10 Inicio de reloj tras verificación | ⚠️ | `routes/simulacro.py:rendir_examen` crea intento en GET; `routes/api.py:iniciar_o_recuperar_intento` acepta duración del cliente. | Inicio POST autorizado y duración del simulacro del servidor. | C/A |
| F11 Reanudación con respuestas y tiempo oficial | 🟡 | `models/intento.py:obtener_intento_activo`, `routes/simulacro.py:rendir_examen`; restaura confirmadas y tiempo SQL, pero buffer local pendiente se pierde con F5. | Prueba de recuperación con desconexión y reconciliación. | A/M |
| D01 Usuarios con rol, consentimiento, estado y sesión actual | 🟡 | `models/database.py:init_db` crea usuarios y `es_admin` booleano, sin rol supervisor ni demás campos. | Migración aditiva y compatibilidad con cuentas existentes. | A/A |
| D02 `codigos_invitacion` | 🔴 | Ausente en `models/database.py:init_db`. | Tabla y consumo transaccional. | A/A |
| D03 `rostros_enrolados` cifrados y aprobables | ⚠️ | `plantillas_faciales` usa JSONB legible; también `usuarios.descriptores_faciales`. | Migración cuidadosa, cifrado y control de estados. | C/A |
| D04 `simulacros` con ventanas de apertura | 🔴 | `examenes_versiones` existe pero no se usa como catálogo de simulacros. | Modelo aditivo y vinculación a intentos. | A/A |
| D05 Intento con semilla, revisión, heartbeat y nota | 🟡 | `intentos` tiene inicio/vencimiento/token, carece de semilla, revisión y latido; `resultados` está separado. | Estados compatibles y restricciones transaccionales. | C/A |
| D06 Respuestas únicas por intento/pregunta | ⚠️ | `respuestas_intento` tiene UNIQUE y revisión, pero acepta pregunta/opción no válidas y sobrescritura fuera de orden. | Validar contra snapshot y versión de operación. | A/M |
| D07 Eventos por intento e `id_cliente` único | ⚠️ | `eventos_monitoreo` usa `usuario_id`, `resultado_id`; `intento_id` añadido pero `registrar_evento` no lo usa. | Vincular intento antes de insertar y deduplicar en BD. | C/A |
| D08 Evidencias con expiración y auditoría de decisiones | 🔴 | No hay tablas `evidencias` ni `auditoria` en `init_db()`. | Migraciones y acceso mínimo. | A/A |
| Q01 Áreas/carreras en una fuente | ✅ | `utils/preguntas.py:AREAS_UNMSM` centraliza catálogo; estructura de áreas coincide con la referencia. | Mantener; validar carrera/área en registro. | M/B |
| Q02 Fórmula +20/−1.125/0, piso cero y desempate | ✅ | `utils/preguntas.py:calcular_puntaje`, `models/resultado.py:obtener_ranking`; tests unitarios de nota. | Probar desempate con BD aislada. | M/M |
| Q03 Banco versionado, IDs de texto e imágenes | 🔴 | `data/examenes/area_*.json` son listas de 10 preguntas sin `imagen`; IDs numéricos. `utils/preguntas.py` no transporta imágenes. | Esquema versionado, rutas de imagen seguras y snapshot por intento. | A/M |
| Q04 Validador de banco (IDs, cinco opciones, clave, cantidad) | 🔴 | `utils/preguntas.py:cargar_preguntas_area` hace `json.load` sin validación; no hay `scripts/validar_preguntas.py`. | Validador offline y validación al publicar versión. | A/M |
| Q05 Orden aleatorio determinista por semilla | 🔴 | `models/intento.py:crear_intento` no genera semilla; `routes/simulacro.py` conserva orden JSON. | Semilla en intento y orden reproducible de preguntas/opciones. | M/M |
| Q06 Informe histórico consistente | ⚠️ | `routes/resultados.py:ver_resultado` recarga JSON actual; cambiarlo altera revisión de resultados anteriores. | Snapshot inmutable y clave histórica por intento. | A/A |

### 9.3 API, seguridad y proctoring (secciones 7–9 y `REGLAS.md`)

| ID y requisito | Estado | Archivo / función; evidencia y problema | Cambio necesario | Prioridad/riesgo |
|---|---|---|---|---|
| A01 Sesión, CSRF, validación de tipos/rangos en `/api/*` | ⚠️ | `routes/api.py`; `/api/carreras` es público y hay validación parcial en otros endpoints; no CSRF. | Aplicar sesión donde corresponda, CSRF en mutaciones y esquema de entradas. | C/A |
| A02 Auth registro/login/logout/cambio de clave con límites | 🟡 | `routes/auth.py` tiene `/register`, `/login`, GET `/logout`; no cambio de clave ni rate limit. | Rutas seguras, POST logout y controles de abuso. | A/A |
| A03 Dashboard y sala por simulacro | 🟡 | `/dashboard`, `/preparacion/<area>` existen; no `simulacro_id` ni disponibilidad. | Vincular catálogo y ventana temporal. | M/M |
| A04 Consentimiento API | 🔴 | `routes/api.py` no tiene endpoint ni persistencia. | Registrar versión/fecha antes de cámara. | C/A |
| A05 Enrolamiento validado/cifrado | ⚠️ | `/api/intento/enrolar-facial` verifica solo lista de 128 dimensiones; no finitud, rango, cifra ni aprobación. | Validación estricta, cifrado y flujo supervisor. | C/A |
| A06 Identidad servidor + `verificacion_ok` de un uso y 5 min | 🔴 | Solo comparación en `templates/preparacion.html`/`monitor_engine.js`; no token servidor. | Servicio y token ligado al usuario/simulacro. | C/A |
| A07 Inicio autorizado con banco sin clave y duración oficial | ⚠️ | `routes/api.py:iniciar_o_recuperar_intento` admite duración; `rendir_examen` crea con GET; vista sí sanitiza claves. | Comprobar verificación, simulacro, propiedad y duración servidor. | C/A |
| A08 Autoguardado por lote del intento propio | 🟡 | `/api/intento/respuesta` guarda una respuesta y comprueba propietario; no valida banco/opción/orden, lote ni CSRF. | Validación y orden transaccional. | A/M |
| A09 Eventos por lote con `id_cliente` | ⚠️ | `/api/evento-monitoreo` inserta por usuario, no valida intento y no deduplica. | Token/ID de intento propio, idempotencia y tamaño de lote. | C/A |
| A10 Heartbeat con estado/advertencias/tiempo | 🔴 | `GET /api/intento/activo` ofrece tiempo; no registra heartbeat ni devuelve sanciones. | POST de 10 s y resolución perezosa. | A/A |
| A11 Identidad periódica servidor | 🔴 | `facial_presence.js` compara localmente cada 6 s; no hay endpoint de identidad. | Comparación segura y escalonada con controles de abuso. | A/A |
| A12 Evidencia JPEG ≤80 KB, almacenamiento privado | 🔴 | No hay endpoint ni capa de almacenamiento. | Validar formato/tamaño y nombre generado por servidor. | A/A |
| A13 Finalización idempotente y propia | ⚠️ | `/api/guardar-resultado` usa token único, pero no exige dueño, intento activo ni transacción; acepta payload de calificación. | Finalización atómica basada en BD. | C/A |
| A14 Resultado propio/supervisor/admin | 🟡 | `routes/resultados.py:ver_resultado` controla dueño/admin, no existe rol supervisor. | Autorización de tres roles con consulta de propiedad. | A/M |
| A15 Ranking con área/carrera y sin DNI | ⚠️ | `models/resultado.py:obtener_ranking` ordena/filtra; `templates/ranking.html` muestra DNI parcial, mientras nueva especificación exige nunca mostrarlo. | Alias o nombre + inicial; excluir revisión pendiente. | A/M |
| A16 Supervisor en vivo, detalle y decisión | 🔴 | `routes/resultados.py` solo contiene `/admin` de lectura y vistas de resultados. | Panel, API, decisión autenticada y bitácora. | A/A |
| A17 Admin de usuarios, invitaciones, rostros, simulacros, CSV, auditoría | 🟡 | `/admin` muestra estadísticas/lista de usuarios; carece de gestión y exportación. | Endpoints y flujos por módulos, con pruebas de rol. | M/A |
| SEC01 Cookies `Secure`/`HttpOnly`/`SameSite` y secretos por entorno | ⚠️ | `config.py` fija HttpOnly/Lax, sin Secure; contiene valores de respaldo sensibles. | Exigir secretos de entorno y cookie Secure en producción. | C/A |
| SEC02 CSRF, rate limit y controles de sesión | 🔴 | `requirements.txt`, `routes/auth.py`, `routes/api.py`; no extensiones ni tokens; sesión Flask es firmada pero no se revoca en BD. | CSRF y límites con pruebas; sesión única. | C/A |
| SEC03 CSP y cabeceras de seguridad | 🔴 | `app.py` no define cabeceras; JS/CSS en línea y Google Fonts dificultan CSP estricta. | Externalizar recursos y configurar cabeceras compatibles. | A/M |
| SEC04 Autorización por rol y recurso | ⚠️ | `utils/helpers.py` solo distingue sesión y `es_admin`; API de entrega no coteja dueño. | Roles explícitos y autorización por fila. | C/A |
| SEC05 Logs sin datos sensibles | ⚠️ | `routes/api.py:api_guardar_resultado` registra tokens de sesión en advertencias; configuración no es JSON. | No registrar tokens/biometría y enmascarar IDs sensibles. | A/M |
| SEC06 Revisión de dependencias con `pip-audit` | 🔴 | No hay evidencia de ejecución ni versiones fijadas. | Auditoría en entorno aislado y plan de actualización. | M/M |
| R01 Severidad definida por servidor | 🔴 | `models/resultado.py:registrar_evento` guarda tipo/descripcion del cliente sin severidad ni servicio de riesgo. | Tabla de tipos y gravedad servidor. | C/A |
| R02 `rostro_ausente`: 10 s, advertencia y revisión a 60 s | ⚠️ | `facial_presence.js` emite `ausencia_prolongada` tras dos ciclos de 6 s; servidor no acumula ventanas ni revisión. | Ventanas verificadas y contador por intento. | A/A |
| R03 `multiples_rostros`: 5 s, evidencia, anulación provisional a 3/6 | ⚠️ | `facial_presence.js` emite `multiple_rostro` tras 12 s; no valida confianza ≥0.7/80%, no captura ni sanciona en servidor. | Ventanas, evidencia y regla servidor revisable. | A/A |
| R04 `identidad_fallida`: reintento 10 s, 3 fallos, evidencia | ⚠️ | Comparación y umbral 0.55 en JS; sin reintento/contador servidor. | Similitud coseno calibrada, reintentos y revisión. | C/A |
| R05 `salida_foco`: agrupar 3 s, 3.ª anulación provisional | ⚠️ | `focus_monitor.js` usa debounce 2 s y cuenta local; backend acepta episodios sin agrupar. | Agrupación servidor y sanción provisional. | A/A |
| R06 `camara_perdida`: overlay y 60 s | 🔴 | No se detectó `ended` de track ni regla/overlay de restauración completo. | Detección, pausa visible y temporización servidor. | A/A |
| R07 `celular_detectado`: INFO, revisión a 3, nunca anula | 🔴 | No hay detector de objetos ni regla servidor. | Función opcional solo tras decisión de runtime/licencia. | M/A |
| R08 `atajo_bloqueado`: INFO, nunca sanciona | 🟡 | `screenshot_guard.js` registra teclas como eventos; no hay severidad servidor ni garantía de no sanción. | Tipificar como INFO y probar ausencia de anulación. | A/M |
| R09 `sin_senal`: >45 s, revisión a 5 min | 🔴 | No se guarda último heartbeat ni brecha; GET de 60 s no basta. | Generación por servidor al siguiente contacto/consulta. | A/A |
| R10 Anulación provisional, confirmar/reponer con nota y auditoría | 🔴 | `resultados.estado` admite ANULADO; no existe `revision`, `revisado_por` ni tabla de auditoría. | Flujo completo de revisión y reposición de nota. | C/A |
| R11 Heartbeat 10 s con orden de finalizar | 🔴 | `monitor_engine.js:startTimer` hace GET de 60 s; no contiene orden del servidor. | POST y estado autoritativo. | A/M |
| R12 Vencimiento +30 s, finalización perezosa, tiempo servidor | ⚠️ | `obtener_intento_activo` excluye vencidos; `/api/guardar-resultado` permite entregar fuera de plazo y tiempo de cliente. | Cierre perezoso atómico con respuestas persistidas. | C/A |

### 9.4 IA, privacidad, interfaz y operación (secciones 10–16)

| ID y requisito | Estado | Archivo / función; evidencia y problema | Cambio necesario | Prioridad/riesgo |
|---|---|---|---|---|
| AI01 Planificador escalonado: rostros 700 ms, identidad 90±30 s, objetos 5 s | 🔴 | `facial_presence.js` hace rostro+identidad juntos cada 6 s; no hay detector de objetos. | Prototipo con medición antes de adoptar nuevas frecuencias. | M/A |
| AI02 Adaptación por latencia, GPU/CPU y Worker | 🔴 | `facial_presence.js:runCheck` evita solapamiento propio, sin presupuesto/adaptación/delegado/Worker. | Planificador y benchmark por equipo. | M/M |
| AI03 Carga única, caché versionada, video compartido y limpieza | 🟡 | `preparacion.html` y `monitor_engine.js` vuelven a cargar modelos/cámara; `stopAllMonitors` detiene tracks; sin política de cache/versionado. | Consolidar ciclo de vida y medir fugas. | M/M |
| AI04 Reto de vida | 🔴 | No se halló giro/parpadeo validado en preparación. | Prueba básica con límites de falsos positivos. | A/M |
| AI05 Licencia de cada modelo y librería | ❓ | `static/models/` incluye face-api, ONNX/WASM; falta inventario de licencias/uso comercial. | Inventario y verificación legal antes de uso con terceros. | A/M |
| PRIV01 Texto y registro de consentimiento | 🔴 | No hay versión/fecha en `usuarios` ni endpoint. | Consentimiento comprensible y prueba de aceptación previa. | C/A |
| PRIV02 Caducidad, purga y borrado a solicitud | 🔴 | Sin `expira_en` ni script/procedimiento de purga. | Retención configurable, purga verificable y borrado. | A/A |
| PRIV03 Embeddings cifrados y acceso restringido | 🔴 | `plantillas_faciales.descriptores` y `usuarios.descriptores_faciales` en JSONB legible; API devuelve vectores al dueño. | Cifrar, limitar acceso y planificar migración de datos. | C/A |
| PRIV04 Política y registro de tratamiento revisables | 🔴 | No existe `docs/PRIVACIDAD.md`. | Redactar y revisar jurídicamente antes de terceros. | A/M |
| UI01 Tema claro, oscuro, tokens, contraste AA | 🟡 | `static/css/base.css` tiene diseño existente; no `tokens.css` ni preferencia de tema/medición AA. | Añadir temas tras revisión visual; medir contraste. | M/M |
| UI02 Fuentes autohospedadas, iconos SVG, espaciado | 🟡 | `templates/base.html` enlaza Google Fonts; hay emojis como iconos. | Assets locales y sistema consistente si se aprueba fase visual. | B/B |
| UI03 Pantallas/estados y panel supervisor | 🟡 | Plantillas cubren login, registro, dashboard, preparación, examen, resultado, ranking, incompatible y admin; falta supervisor y estados auditados. | Inventario de estados y panel supervisor. | M/M |
| UI04 Examen: reloj, cuadrícula, cámara, marcado, overlays | 🟡 | `templates/examen.html`, `monitor_engine.js` tienen reloj, matriz, webcam y toasts; no overlay completo para cámara/pantalla perdida; marcado revisión no tiene flujo UI verificado. | Revisar estados y accesibilidad. | M/M |
| UI05 Teclado, `aria-live`, foco, movimiento reducido, dos resoluciones | ❓ | CSS/vistas no han sido probados con navegador, lector o capturas. | Auditoría manual y pruebas visuales. | M/B |
| UI06 Portada interactiva ligera | 🔴 | `routes/dashboard.py:index` redirige, no hay portada pública. | Portada HTML/CSS con JS puntual, medios optimizados y métricas. | B/B |
| OP01 Separar desarrollo, pruebas y producción | ⚠️ | `config.py` tiene development/production, pero `Dockerfile` arranca `debug=True` desde `app.py`; pruebas de BD usan URL activa. | Variables obligatorias, BD de test, servidor producción y despliegue reproducible. | C/A |
| OP02 Prueba HTTP de 60 usuarios, p95 y 0 errores | 🔴 | `tests/test_concurrencia_30.py` ejecuta llamadas SQL directas de 30 hilos, no tráfico HTTP ni 60 usuarios. | Locust en entorno aislado y reporte de p95/5xx/BD. | M/M |
| OP03 RUNBOOK, ensayo 8–10 personas y límites documentados | 🔴 | `docs/guia_portabilidad.md` no es runbook de examen; no hay evidencia de ensayo. | Plan de contingencias y ensayo real. | M/B |
| OP04 Definición global de terminado con pruebas/evidencia | ❓ | `docs/informe_final_entrega.md` afirma cierre 0–8, pero faltan pruebas y capacidades de esta especificación. | Reconciliar fases y evidencias antes de declarar terminado. | M/B |

## 10. Diagnóstico profundo de integridad y concurrencia

**Datos que controla el navegador:** `token_sesion`, `area`, mapa completo de `respuestas`, `tiempo_segundos`, `estado`, `motivo_anulacion`, duración solicitada, IDs de intento/pregunta, opción, metadatos de eventos y descriptores biométricos. Los tokens de sesión del examen aparecen en el HTML del dueño y en el payload; deben tratarse como identificadores de recurso, nunca como prueba suficiente de propiedad.

**Vías concretas:** `api_guardar_resultado` devuelve primero un resultado ya existente según token, antes de cotejar dueño. Si no existe intento, continúa con el token arbitrario y guarda un resultado para el usuario de sesión. Si sí existe, no coteja `usuario_id`, `area`, `estado_academico` ni vencimiento; fusiona respuestas del cliente con las persistidas, por lo que el cliente puede sustituir una respuesta confirmada. Si el tiempo cliente cae dentro de ±60 s del tiempo calculado, usa ese valor y puede alterar desempates. El cliente también puede solicitar `ANULADO`; no hay mecanismo administrativo para revertirlo. Estas conclusiones derivan del flujo de código, no de una explotación sobre BD real.

**Carreras y atomicidad:** dos entregas simultáneas pueden leer ausencia de resultado y llamar `cerrar_intento` sin condición de estado; el índice único de token evita dos filas de resultado, pero no asegura que la primera operación de cierre y la inserción se completen juntas. `asociar_eventos_a_resultado` puede anexar eventos de otra sesión del mismo usuario. Deben ser atómicos: bloqueo/validación de intento propio y abierto, lectura de snapshot y respuestas, cálculo, transición de estado, inserción de resultado y vínculo de eventos del mismo intento. La respuesta duplicada debe devolver solo el resultado propio y ya persistido. La sanción/revisión requiere transacción separada, autorizada y auditada.

**Pruebas de corrección propuestas:** sin intento/otro dueño/token ajeno; área/estado/respuestas/tiempo falsos; entrega vencida; respuesta fuera de banco/opción inválida; dos entregas paralelas y fallo forzado entre cierre/resultado; reintento tras fallo; dos intentos del mismo usuario con eventos distintos; cambio del JSON tras iniciar; token de verificación reutilizado/caducado; sanción INFO que nunca anula; supervisor confirma y repone; exclusión de ranking mientras revisión está pendiente. Usar PostgreSQL de pruebas aislada con rollback/fixtures y peticiones HTTP, sin datos reales.

## 11. Evaluación de stack y opciones de arquitectura

**ACTUAL:** Flask/Jinja2, CSS propio, JS global/en línea, face-api.js con descriptores de 128 dimensiones, PostgreSQL con SQL directo; Gunicorn solo en `Procfile`. **ESPECIFICACIÓN NUEVA:** conserva Flask/PostgreSQL/Jinja2 pero exige módulos JS nativos, MediaPipe Tasks Vision y ONNX Runtime Web de 512 dimensiones, evidencias privadas, migraciones y controles de seguridad. **IMPACTO:** la diferencia biométrica afecta compatibilidad de plantillas y rendimiento; la de frontend afecta compilación, despliegue y CSP. **RECOMENDACIÓN:** mantener el frontend actual mientras se cierra la integridad del examen; decidir la migración de IA con una prueba aislada de licencia, precisión y equipos reales. No cambiar stack en esta auditoría.

**Svelte + Vite:** Svelte permite componentes compilados; Vite admite integración incremental con HTML servido por un backend y manifiesto de assets ([Svelte](https://svelte.dev/docs/svelte/overview), [Vite](https://vite.dev/guide/backend-integration.html)). Podría ayudar en pantallas con estado complejo, pero introduciría Node, compilación, manifiestos, pruebas nuevas y dos modelos de renderizado. Contradice el stack cerrado actual; exige decisión explícita antes de usarlo. Un experimento aislado en una vista no crítica sería más reversible que migrar el examen. La seguridad y persistencia del servidor no dependen de Svelte.

**Imágenes en preguntas:** los cinco JSON actuales contienen 10 preguntas por área, sin campo `imagen`; el modelo del documento nuevo prevé rutas de imagen. Proponer `imagen` opcional, validada contra un directorio público de solo lectura y con tamaño/tipo/alt definidos; la ruta se incluye en la versión inmutable y se muestra de forma accesible. Nunca convertir la clave de respuesta o explicación en archivo público. Mantener el banco completo fuera de `static/`.

**Portada interactiva:** la ruta `/` redirige al dashboard. Una portada futura puede servirse con HTML/CSS estático, animación discreta y JavaScript cargado después del contenido, sin cargar modelos de IA. Medir peso, tiempo de carga, teclado y movimiento reducido antes de publicarla.

**Entornos:** separar URL de PostgreSQL, secretos y flags para desarrollo/pruebas/producción; prohibir que los scripts de pruebas usen por defecto la BD activa. Despliegue de producción con Gunicorn `gthread`, pool calculado por proceso y cabeceras de seguridad. El CSS y scripts en línea dificultan una CSP estricta; externalizarlos o usar nonces según el diseño de seguridad ([MDN CSP](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/script-src)).

## 12. Fases originales, plan y primera tarea

**Cobertura de la hoja de ruta nueva:** fase 0 tiene documentación previa parcial y decisiones abiertas; fase 1 tiene núcleo de examen parcial con defectos críticos; fase 2 tiene pantallas y CSS existentes, sin sistema visual/AA probado; fase 3 tiene cámara y enrolamiento parciales, sin consentimiento/acreditación servidor; fase 4 tiene monitores básicos, sin transporte/heartbeat/evidencias previstos; fase 5 tiene panel admin de lectura y telemetría, sin motor de sanción ni supervisor; fase 6 carece de cifrado/retención/cabeceras; fase 7 tiene un ensayo SQL de 30 hilos sin prueba HTTP de 60 ni runbook. La numeración anterior 0–8 en `docs/especificacion_fase_0.md` y `docs/informe_final_entrega.md` describe hitos distintos; no equiparar fases solo por número.

**Secuencia sugerida, en cambios pequeños y reversibles:**

1. Aislar una BD de pruebas y escribir pruebas de abuso para `/api/guardar-resultado` y propiedad de recursos; documentar contrato de cierre. Sin tocar datos reales.
2. Hacer que la finalización lea intento propio, versión de examen, respuestas y reloj servidor; cierre y nota en una transacción; conservar idempotencia y probar concurrencia.
3. Validar IDs/opciones, orden de respuestas, un intento por simulacro y recuperación de cola tras F5; fijar snapshot de preguntas con migración aditiva.
4. Añadir CSRF, límites, secretos obligatorios y sesiones revocables; resolver migraciones, entornos y observabilidad básica.
5. Añadir consentimiento, identidad servidor y aprobación humana; después heartbeat, eventos por intento, evidencia y sanciones provisionales, cada regla con pruebas.
6. Completar invitaciones, administración, soporte de imágenes, accesibilidad y portada; decidir Svelte/IA solo tras pruebas y licencia.
7. Ensayar carga HTTP de 60 usuarios, rendimiento de modelos en equipos reales, despliegue y runbook. No usar el informe anterior de entrega como aceptación de esta especificación.

**Primera tarea concreta recomendada:** crear, en una fase autorizada, una suite de integración aislada que demuestre que el cierre rechaza token ajeno, intento inexistente, respuestas y tiempo falsos, anulación del cliente y entregas paralelas. Fijar el comportamiento esperado antes de modificar `routes/api.py`, `models/intento.py` y `models/resultado.py`; luego hacer el cambio transaccional mínimo necesario.

La fase −1 fue aprobada por el usuario. Las referencias se incorporaron durante la preparación autorizada del entorno, registrada en `docs/PROGRESO.md`. No se ejecutó la fase 0 ni se implementaron correcciones. La Subfase 1A sigue pendiente de su autorización específica.
