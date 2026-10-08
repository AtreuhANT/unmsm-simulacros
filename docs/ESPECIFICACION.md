> **Documento de requisitos de referencia.** Este proyecto ya tiene código. No ejecutar la orden original de construcción desde cero. Primero auditar el repositorio y proponer cambios sin modificar código funcional. En caso de discrepancia, documentar y solicitar aprobación.

# PROMPT MAESTRO: PLATAFORMA WEB DE SIMULACROS TIPO ADMISIÓN UNMSM CON SUPERVISIÓN (PROCTORING)

## 0. TU ROL Y CÓMO DEBES TRABAJAR (LEE ESTO PRIMERO)

Actúas como Arquitecto de Software Senior y Tech Lead Full Stack (Python, seguridad web, IA en el navegador). Vas a construir una plataforma profesional para simulacros de admisión, usada por 30+ personas en simultáneo, con verificación de identidad y monitoreo anti-trampa.

**Reglas de trabajo (obligatorias):**
1. Este proyecto se construye **por fases (0 a 7)**. Ejecuta **solo la fase que yo te indique**. Al terminar una fase, detente y espera mi mensaje `APROBADO FASE N`. No adelantes trabajo de fases futuras.
2. Antes de escribir código en cada fase, entrégame un **plan breve (máx. 15 líneas)** con los archivos que vas a crear o modificar, y espera mi `OK`. (En la Fase 0 puedes empezar directo.)
3. Entrega **archivos completos**, uno por uno. Prohibido: `TODO`, `pass` sin implementar, `...`, datos simulados en lógica real, "implementar después". Si algo no lo implementas, dilo explícitamente en el cierre.
4. Ejecuta las pruebas y **muestra la salida real**. No afirmes que algo funciona sin haberlo ejecutado.
5. Si hay una ambigüedad que no bloquea, elige la opción más segura, regístrala en `docs/DECISIONES.md` y continúa. Pregunta solo si es bloqueante.
6. **Cierre obligatorio de cada fase** con este formato:
   - Lista de criterios de aceptación de la fase, cada uno marcado ✅ o ❌ **con evidencia** (comando ejecutado, salida de test, captura).
   - Lo que NO se implementó y por qué.
   - Supuestos tomados.
   - Cómo ejecutar y probar lo entregado (comandos exactos).
   - Actualización de `docs/PROGRESO.md`.
7. Idioma: interfaz, comentarios, documentación e identificadores de dominio en **español**. Código claro, funciones cortas, tipado con type hints en Python.
8. No modifiques archivos de fases anteriores salvo que sea necesario; si lo haces, explícalo y vuelve a ejecutar sus pruebas.

**Variables por definir** (si siguen como `[LLENAR]`, usa el valor de ejemplo, regístralo en `DECISIONES.md` y haz que sea configurable):
- `NOMBRE_INSTITUCION`: [LLENAR] (ejemplo: "Simulacros Sanmarquinos")
- `NUM_PREGUNTAS_POR_AREA`: [LLENAR] (ejemplo: 100, solo ejemplo)
- `DURACION_EXAMEN_MIN`: [LLENAR] (ejemplo: 180, solo ejemplo)
- `HOSTING_OBJETIVO`: [LLENAR] (ejemplo: PaaS tipo Render/Railway con PostgreSQL gestionado)
- `USO`: [LLENAR] (ejemplo: académico privado / comercial). Si es comercial, aplica la regla de licencias de la sección 10.

---

## 1. OBJETIVO Y ALCANCE

Plataforma web para rendir simulacros de admisión (áreas A, B, C, D, E) con:
- Registro/login, dashboard, examen cronometrado, resultados y rankings.
- **Sala de verificación previa al examen**, donde recién se pide la cámara: consentimiento, pruebas técnicas, identidad facial.
- Monitoreo continuo durante el examen (rostro, foco de ventana, cámara), con evidencia y **revisión humana** de las anulaciones.
- Paneles de supervisor y administrador.
- Capacidad: 30+ usuarios simultáneos en PCs/laptops de escritorio. Solo escritorio; móviles se redirigen a `/incompatible` (esto es una cortesía de UX, no una medida de seguridad).

---

## 2. PRINCIPIOS NO NEGOCIABLES

1. **El cliente NO es confiable.** Todo lo que corre en el navegador puede alterarse. El **servidor es la autoridad** en: tiempo, calificación, reglas de sanción, estado del intento y comparación de identidad.
2. **Inferencia en el navegador (edge).** El servidor **no procesa video ni imágenes** (sin OpenCV, dlib, face_recognition, CMake). Solo recibe JSON ligero, vectores (embeddings) y, puntualmente, **capturas de evidencia que solo almacena** (no las analiza).
3. **Evidencia + revisión humana.** Las anulaciones automáticas son **provisionales** y revisables por un supervisor. Ninguna señal débil (celular, atajos de teclado) anula un examen.
4. **La ausencia de eventos no es ausencia de faltas.** Se usa *heartbeat*; si el cliente deja de reportar, el servidor lo registra.
5. **Privacidad por diseño.** Los datos biométricos son datos personales sensibles (Ley N.º 29733 y su reglamento): consentimiento explícito, finalidad, retención limitada, cifrado y acceso restringido.
6. **Nunca se envía la clave de respuestas al navegador.**
7. **Honestidad técnica.** Documenta los límites conocidos (sección 13). No prometas detección perfecta.

---

## 3. STACK (CERRADO, NO CAMBIAR SIN APROBACIÓN)

- **Backend:** Python 3.11 o 3.12, Flask 3.x con Blueprints y *application factory* (`create_app`).
- **Servidor:** Gunicorn, workers `gthread` (2–3 workers × 4–8 threads; documenta la configuración elegida).
- **BD:** PostgreSQL con `psycopg2-binary`, SQL parametrizado (`%s`), `RealDictCursor`, `ThreadedConnectionPool` por worker. **Sin ORM.** Migraciones SQL numeradas en `migrations/` ejecutadas por `scripts/migrate.py` (tabla `schema_migrations`). No uses `CREATE TABLE IF NOT EXISTS` suelto al arrancar la app como único mecanismo.
- **Seguridad:** Werkzeug (hash de contraseñas), Flask-WTF (CSRF; para `fetch` usa token en cabecera), Flask-Limiter (rate limiting), `cryptography` (Fernet) para cifrar embeddings.
- **Frontend:** HTML5 semántico, Jinja2, CSS vanilla con variables, JavaScript ES2020+ en módulos nativos (`<script type="module">`). **Sin bundlers, sin frameworks, sin CDNs externos**: todo (modelos, WASM, fuentes, iconos) se hospeda en `static/`.
- **IA en el navegador (solo estos dos runtimes):**
  - **MediaPipe Tasks Vision** (WASM, delegado GPU con respaldo CPU): Face Detector / Face Landmarker para presencia y múltiples rostros; Object Detector (EfficientDet-Lite) para celular, **opcional y desactivable**.
  - **ONNX Runtime Web** con un modelo de embeddings faciales liviano (clase MobileFaceNet/ArcFace, 512 dimensiones) para identidad.
  - Prohibido usar face-api.js y TensorFlow.js.
- **Almacenamiento de evidencia:** almacenamiento de objetos compatible con S3 (R2/S3/Supabase Storage) detrás de una interfaz `services/evidencias.py`, con un backend local de disco para desarrollo. Nunca en la BD.
- **Pruebas:** `pytest` (+ `pytest-cov`), `node:test` para lógica JS pura, `locust` para carga.
- **Observabilidad:** logging estructurado (JSON), endpoint `/health`, Sentry opcional por variable de entorno.
- Fija las **versiones exactas** de todas las dependencias en `requirements.txt`.

---

## 4. FLUJO DE USUARIO (LA CÁMARA SOLO SE PIDE EN LA SALA DE VERIFICACIÓN)

```
Registro/Login (sin cámara)
   → Dashboard (simulacros disponibles según área y horario)
      → "Rendir simulacro"
         → SALA DE VERIFICACIÓN
              1. Pantalla informativa + consentimiento (casilla obligatoria, se guarda con fecha y versión)
              2. Solicitud de permiso de cámara (recién aquí se llama a getUserMedia)
              3. Pruebas técnicas: cámara, luz, red, benchmark de rendimiento del equipo
              4. Enrolamiento (primera vez) o verificación de identidad (siguientes veces)
              5. Reglas del examen + pantalla completa
         → EXAMEN (monitoreo activo; la cámara se libera al finalizar)
            → Resultado (con observaciones de conducta)
```

- **Registro:** con **código de invitación** emitido por el admin (`codigos_invitacion`). El usuario **elige su propia contraseña** (mínimo 10 caracteres). El DNI **no** es contraseña. Los usuarios importados por CSV reciben una contraseña temporal aleatoria y deben cambiarla en el primer ingreso (`debe_cambiar_password`).
- **Enrolamiento facial:** ocurre en la primera sala de verificación. Se captura de 3 a 5 embeddings en distintas poses. Queda en estado `PENDIENTE` hasta que un supervisor lo apruebe (con la persona identificada, p. ej. comparando con su DNI). El admin puede revocarlo o reiniciarlo.
- **Un solo intento por usuario y simulacro**, con sesión única (un nuevo login invalida la sesión anterior durante un intento en curso).

---

## 5. MODELO DE DATOS (PostgreSQL; migración `0001_init.sql`)

```sql
CREATE TABLE usuarios (
  id SERIAL PRIMARY KEY,
  nombre TEXT NOT NULL,
  apellido TEXT NOT NULL,
  dni VARCHAR(15) NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  debe_cambiar_password BOOLEAN NOT NULL DEFAULT FALSE,
  carrera TEXT NOT NULL,
  area CHAR(1) NOT NULL CHECK (area IN ('A','B','C','D','E')),
  rol TEXT NOT NULL DEFAULT 'estudiante' CHECK (rol IN ('estudiante','supervisor','admin')),
  alias_ranking TEXT,
  consentimiento_en TIMESTAMPTZ,
  consentimiento_version TEXT,
  activo BOOLEAN NOT NULL DEFAULT TRUE,
  sesion_actual TEXT,
  creado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE codigos_invitacion (
  codigo TEXT PRIMARY KEY,
  area CHAR(1),
  usos_max INTEGER NOT NULL DEFAULT 1,
  usos INTEGER NOT NULL DEFAULT 0,
  expira_en TIMESTAMPTZ NOT NULL,
  creado_por INTEGER REFERENCES usuarios(id),
  creado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE rostros_enrolados (
  id SERIAL PRIMARY KEY,
  usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
  embeddings_cifrados TEXT NOT NULL,          -- token Fernet con la lista de embeddings
  modelo_version TEXT NOT NULL,
  estado TEXT NOT NULL DEFAULT 'PENDIENTE'
    CHECK (estado IN ('PENDIENTE','APROBADO','RECHAZADO','REVOCADO')),
  aprobado_por INTEGER REFERENCES usuarios(id),
  aprobado_en TIMESTAMPTZ,
  creado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX uq_rostro_vigente ON rostros_enrolados(usuario_id)
  WHERE estado IN ('PENDIENTE','APROBADO');

CREATE TABLE simulacros (
  id SERIAL PRIMARY KEY,
  titulo TEXT NOT NULL,
  area CHAR(1) NOT NULL CHECK (area IN ('A','B','C','D','E')),
  duracion_segundos INTEGER NOT NULL CHECK (duracion_segundos > 0),
  abre_en TIMESTAMPTZ NOT NULL,
  cierra_en TIMESTAMPTZ NOT NULL,
  activo BOOLEAN NOT NULL DEFAULT TRUE,
  creado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE intentos (
  id SERIAL PRIMARY KEY,
  usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
  simulacro_id INTEGER NOT NULL REFERENCES simulacros(id),
  area CHAR(1) NOT NULL,
  token_sesion UUID NOT NULL UNIQUE,          -- generado por el SERVIDOR
  semilla INTEGER NOT NULL,                   -- orden aleatorio determinista por alumno
  estado TEXT NOT NULL DEFAULT 'EN_CURSO'
    CHECK (estado IN ('EN_CURSO','COMPLETADO','ANULADO')),
  motivo_anulacion TEXT,
  revision TEXT NOT NULL DEFAULT 'NO_REQUERIDA'
    CHECK (revision IN ('NO_REQUERIDA','PENDIENTE','ANULACION_CONFIRMADA','REPUESTO')),
  revisado_por INTEGER REFERENCES usuarios(id),
  revisado_en TIMESTAMPTZ,
  nota_revision TEXT,
  inicio_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  limite_en TIMESTAMPTZ NOT NULL,             -- inicio_en + duración
  ultimo_heartbeat_en TIMESTAMPTZ,
  fin_en TIMESTAMPTZ,
  puntaje REAL, correctas INTEGER, incorrectas INTEGER, blanco INTEGER,
  tiempo_segundos INTEGER,                    -- calculado por el servidor
  UNIQUE (usuario_id, simulacro_id)
);
CREATE INDEX idx_intentos_ranking ON intentos(area, puntaje DESC, tiempo_segundos ASC)
  WHERE estado = 'COMPLETADO';
CREATE INDEX idx_intentos_estado ON intentos(estado, revision);

CREATE TABLE respuestas (
  intento_id INTEGER NOT NULL REFERENCES intentos(id) ON DELETE CASCADE,
  pregunta_id TEXT NOT NULL,
  opcion CHAR(1),                             -- NULL = en blanco / deseleccionada
  actualizado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (intento_id, pregunta_id)
);

CREATE TABLE eventos_monitoreo (
  id BIGSERIAL PRIMARY KEY,
  intento_id INTEGER NOT NULL REFERENCES intentos(id) ON DELETE CASCADE,
  id_cliente TEXT NOT NULL,                   -- UUID del cliente para deduplicar reintentos
  modulo VARCHAR(50) NOT NULL,
  tipo VARCHAR(50) NOT NULL,
  severidad TEXT NOT NULL CHECK (severidad IN ('INFO','LEVE','GRAVE')), -- la asigna el SERVIDOR
  descripcion TEXT,
  segundo_examen INTEGER,
  metadata JSONB,
  registrado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (intento_id, id_cliente)
);
CREATE INDEX idx_eventos_intento ON eventos_monitoreo(intento_id, registrado_en);

CREATE TABLE evidencias (
  id SERIAL PRIMARY KEY,
  intento_id INTEGER NOT NULL REFERENCES intentos(id) ON DELETE CASCADE,
  evento_id BIGINT REFERENCES eventos_monitoreo(id) ON DELETE SET NULL,
  ruta_objeto TEXT NOT NULL,
  bytes INTEGER,
  creado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expira_en TIMESTAMPTZ NOT NULL
);

CREATE TABLE auditoria (
  id BIGSERIAL PRIMARY KEY,
  actor_id INTEGER REFERENCES usuarios(id),
  accion TEXT NOT NULL,
  entidad TEXT NOT NULL,
  entidad_id TEXT,
  detalle JSONB,
  creado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

Reglas de datos:
- El ranking incluye solo intentos `COMPLETADO` con `revision` distinta de `PENDIENTE`. Muestra `alias_ranking` o nombre + inicial de apellido. **Nunca el DNI.**
- Si un supervisor **repone** un intento anulado: `estado = 'COMPLETADO'`, `revision = 'REPUESTO'`, y el puntaje se calcula con las respuestas guardadas.

---

## 6. ÁREAS, CARRERAS Y CALIFICACIÓN

- **Área A (Ciencias de la Salud):** Medicina Humana, Obstetricia, Enfermería, Tecnología Médica, Nutrición, Farmacia y Bioquímica, Odontología, Medicina Veterinaria, Psicología.
- **Área B (Ciencias Básicas):** Química, Física, Matemática, Estadística, Investigación Operativa, Genética, Ciencias Biológicas.
- **Área C (Ingenierías):** Ingeniería Civil, Ingeniería de Sistemas, Ingeniería Industrial, Ingeniería de Software, Ingeniería Eléctrica, Ingeniería Electrónica, Ingeniería de Telecomunicaciones, Ingeniería Nuclear, Ingeniería Biomédica, Ingeniería Mecatrónica.
- **Área D (Ciencias Económicas y de la Gestión):** Administración, Administración de Negocios Internacionales, Administración de Turismo, Auditoría Empresarial, Contabilidad, Economía.
- **Área E (Humanidades y Ciencias Jurídicas y Sociales):** Derecho, Literatura, Filosofía, Historia, Educación, Comunicación Social, Lingüística, Arqueología.

Guarda esta estructura en un único módulo (`app/dominio/areas.py`), no duplicada.

**Puntaje** (valores en `config.py`, no hardcodeados): correcta **+20.0**, incorrecta **−1.125**, blanco **0.0**. `puntaje = max(0.0, total)`. **Desempate:** 1.º mayor puntaje, 2.º menor `tiempo_segundos`.

**Banco de preguntas** (`data/examenes/area_x.json`; lo proveo yo, tú solo creas ejemplos marcados `DEMO`):
```json
{ "area": "C", "version": "2026-1",
  "preguntas": [
    { "id": "C-MAT-001", "curso": "Matemática", "enunciado": "...",
      "opciones": {"A": "...", "B": "...", "C": "...", "D": "...", "E": "..."},
      "correcta": "B", "imagen": null }
  ] }
```
Crea `scripts/validar_preguntas.py` (ids únicos, 5 opciones, `correcta` válida, cantidad esperada) y úsalo al cargar el banco. Orden de preguntas y opciones aleatorio **determinista por `semilla` del intento**.

---

## 7. REGLAS DE MONITOREO Y SANCIONES (CONFIGURABLES EN `config.py` Y DOCUMENTADAS EN `docs/REGLAS.md`)

El **servidor** asigna la severidad según el `tipo` (nunca confíes en la severidad que envíe el cliente) y aplica las reglas en `services/riesgo.py` cada vez que llega un lote de eventos o un heartbeat. Cada evento enviado por el cliente representa una **ventana confirmada** (no un frame suelto).

| Tipo de evento | Qué representa un evento | Severidad | Efecto |
|---|---|---|---|
| `rostro_ausente` | Ventana de 10 s sin rostro | LEVE | 1.º: advertencia. ≥ 6 ventanas acumuladas (60 s): `revision = PENDIENTE`. No anula. |
| `multiples_rostros` | Ventana de 5 s con ≥ 2 rostros (confianza ≥ 0.7 en ≥ 80% de los frames de la ventana) | GRAVE | Captura de evidencia en la 1.ª ventana y cada 3.ª. ≥ 3 ventanas consecutivas, o ≥ 6 acumuladas: **anulación provisional**. |
| `identidad_fallida` | Verificación periódica de identidad que no supera el umbral | LEVE | Reintento a los 10 s. **3 fallos consecutivos:** anulación provisional + evidencia. |
| `salida_foco` (`tab_switch`, `window_blur`, `fullscreen_exit`) | Salida de la ventana/pantalla completa. El servidor agrupa eventos del mismo episodio (misma ventana de 3 s) como **una** salida | LEVE | 1.ª y 2.ª: advertencia visible con contador. **3.ª: anulación provisional.** |
| `camara_perdida` | Pista de video terminada o cámara desconectada | LEVE | Overlay bloqueante para restablecerla. Si no se restablece en 60 s: anulación provisional. |
| `celular_detectado` | Detección de celular (opcional) | INFO | Solo evidencia. ≥ 3 detecciones: `revision = PENDIENTE`. **Nunca anula.** |
| `atajo_bloqueado` (PrintScreen, F12, Ctrl+U, etc.) | Intento de atajo | INFO | Solo registro. **Nunca sanciona.** |
| `sin_senal` | Generado por el servidor: sin heartbeat > 45 s | LEVE | ≥ 5 min acumulados: `revision = PENDIENTE`. No anula. |

**Anulación provisional:** `estado = 'ANULADO'`, `revision = 'PENDIENTE'`, `motivo_anulacion` con el motivo exacto. El cliente recibe la orden de terminar en el siguiente heartbeat y se muestra la pantalla de resultado con las observaciones. El supervisor puede **confirmar** (`ANULACION_CONFIRMADA`) o **reponer** (`REPUESTO`) con una nota; toda decisión queda en `auditoria`.

**Heartbeat:** el cliente envía uno cada 10 s; la respuesta trae el tiempo restante (según el servidor), el estado del intento y las advertencias vigentes. **Sin tareas en segundo plano:** la brecha de heartbeat se registra cuando llega el siguiente heartbeat o cuando el supervisor consulta.

**Tiempo:** `limite_en = inicio_en + duración`, calculado por el servidor al iniciar. Si el intento sigue `EN_CURSO` pasado `limite_en` + 30 s de gracia, el servidor lo finaliza al detectarlo (*finalización perezosa*) con las respuestas ya autoguardadas. `tiempo_segundos` lo calcula siempre el servidor.

---

## 8. CONTRATO DE API (documéntalo completo en `docs/API.md`)

Todas las rutas `/api/*` exigen sesión + CSRF, devuelven JSON con códigos HTTP correctos y validan entradas (tipos, tamaños, rangos). Un alumno solo accede a **sus** intentos.

| Método y ruta | Rol | Función |
|---|---|---|
| `POST /auth/registro`, `/auth/login`, `/auth/logout`, `/auth/cambiar-password` | público/autenticado | Autenticación (rate limit en login y registro) |
| `GET /dashboard` | estudiante | Simulacros disponibles |
| `GET /verificacion/<simulacro_id>` | estudiante | Sala de verificación |
| `POST /api/verificacion/consentimiento` | estudiante | Registra consentimiento (fecha y versión) |
| `POST /api/verificacion/enrolar` | estudiante | Recibe 3–5 embeddings, valida dimensión, los cifra y deja `PENDIENTE` |
| `POST /api/verificacion/identidad` | estudiante | Recibe embedding; **el servidor compara** (similitud coseno) y, si pasa, emite `verificacion_ok` de **un solo uso** y TTL de 5 min |
| `POST /api/examen/iniciar` | estudiante | Exige `verificacion_ok`; crea el intento; devuelve preguntas **sin clave**, semilla, `limite_en` y `token_sesion` |
| `PUT /api/examen/<id>/respuestas` | estudiante | Autoguardado por lotes (cada ~10 s y al cambiar de pregunta) |
| `POST /api/examen/<id>/eventos` | estudiante | Lote de eventos (cada ~5 s), deduplicado por `id_cliente` |
| `POST /api/examen/<id>/heartbeat` | estudiante | Estado, tiempo restante, advertencias, orden de terminar |
| `POST /api/examen/<id>/identidad` | estudiante | Verificación periódica de identidad |
| `POST /api/examen/<id>/evidencia` | estudiante | Captura JPEG pequeña (≤ 80 KB), solo se almacena |
| `POST /api/examen/<id>/finalizar` | estudiante | **Idempotente**: segundo envío devuelve el mismo resultado, no duplica |
| `GET /resultado/<intento_id>` | dueño/supervisor/admin | Resultado y observaciones de conducta |
| `GET /ranking` | estudiante | Filtros por área y carrera |
| `GET /supervisor/en-vivo` y `GET /api/supervisor/estado` | supervisor | Panel en vivo (polling cada 5 s) |
| `GET /supervisor/intento/<id>`, `POST /api/supervisor/intento/<id>/decision` | supervisor | Revisión, evidencias, confirmar/reponer |
| `/admin/...` | admin | Usuarios, importación CSV, códigos de invitación, aprobar/revocar rostros, simulacros, exportar CSV, auditoría |

**Comparación de identidad en el servidor:** normaliza los vectores y usa similitud coseno (puedes implementarla en Python puro, son 512 flotantes). Umbral inicial `UMBRAL_IDENTIDAD_COSENO` configurable (valor de partida a **calibrar con datos reales**, ver `docs/CALIBRACION.md`).

---

## 9. SEGURIDAD

- Cookies de sesión `Secure`, `HttpOnly`, `SameSite=Lax`; `SECRET_KEY` y la clave Fernet solo por variables de entorno (`.env.example` sin valores reales; `.env` en `.gitignore`).
- CSRF en todas las rutas que cambian estado; rate limiting en login, registro y endpoints de API.
- Cabeceras: CSP estricta (permitiendo `'wasm-unsafe-eval'` solo por los runtimes WASM), `X-Content-Type-Options`, `X-Frame-Options`/`frame-ancestors`, `Referrer-Policy`, HSTS en producción.
- Autorización por rol con decoradores; verificar propiedad del recurso en **cada** endpoint.
- Validación de tamaño de cuerpo y tipo de archivo en `evidencia`; nombres de objeto generados por el servidor (nunca por el cliente).
- Logs sin datos sensibles (sin embeddings, sin contraseñas, DNI enmascarado).
- `pip-audit` en la revisión de dependencias.

---

## 10. IA EN EL NAVEGADOR: DETECCIÓN SIN TRABAS

**Planificador central (`static/js/proctoring/engine.js`):** un solo bucle que programa los detectores de forma **escalonada** para que nunca coincidan dos inferencias pesadas.

| Detector | Frecuencia inicial | Notas |
|---|---|---|
| Rostros (presencia/múltiples) | cada 700 ms | Video reducido a 320×240 para análisis |
| Identidad (embedding) | cada 90 s ± 30 s (aleatorio), y tras `rostro_ausente` prolongado | Solo recorta el rostro, calcula el embedding y lo envía |
| Objetos (celular) | cada 5 s | Opcional, apagable por configuración |

Rendimiento obligatorio:
- **Medición adaptativa:** si una inferencia supera su presupuesto de tiempo, el motor reduce la frecuencia automáticamente y registra un evento INFO de rendimiento.
- Delegado GPU con respaldo a CPU/WASM; mover la inferencia a un **Web Worker** cuando la API lo permita.
- Modelos cargados **una sola vez**, con caché HTTP largo y versionado; un único `<video>` compartido.
- **Benchmark en la sala de verificación:** mide el tiempo de inferencia; si el equipo es demasiado lento, advierte con instrucciones (cerrar programas, usar otro equipo) o bloquea según la configuración.
- Sin fugas de memoria: liberar recursos (`close()`) de resultados y detectores al finalizar.

**Verificación de identidad:** incluye un **reto de vida básico** (giro de cabeza o parpadeo, usando landmarks) en la sala de verificación para dificultar el uso de una foto.

**Licencias (obligatorio en Fase 0):** documenta en `docs/DECISIONES.md` la licencia de **cada** modelo y librería elegida. Varios pesos preentrenados populares de reconocimiento facial (p. ej. los de InsightFace) están restringidos a uso **no comercial**. Si `USO` es comercial, elige un modelo con licencia permisiva y verifica los términos antes de usarlo.

---

## 11. PRIVACIDAD

- Texto de consentimiento claro (qué se monitorea, para qué, cuánto tiempo, a quién se muestra, cómo reclamar), con **versión** y fecha de aceptación guardadas.
- Retención configurable: evidencias con `expira_en`; `scripts/purgar_expirados.py` para ejecutar por cron. Procedimiento para borrar los datos de un usuario a su pedido.
- Embeddings **cifrados en reposo** (Fernet), accesibles solo para el servicio de identidad.
- `docs/PRIVACIDAD.md` con el borrador de política y el registro de tratamiento de datos. Indica que debe ser **revisado por un abogado** antes de operar con terceros.

---

## 12. DISEÑO VISUAL (UI/UX): NO ACEPTO UN ASPECTO GENÉRICO

**Dirección:** sobrio, confiable, institucional pero moderno; cero distracciones durante el examen. Pensado para sesiones de hasta 3 horas.

**Tema:** claro por defecto, con modo oscuro opcional (interruptor, preferencia guardada). Define tokens en `static/css/tokens.css`:
- Claro: `--bg #F7F8FB`, `--surface #FFFFFF`, `--ink #0F172A`, `--muted #5B6475`, `--border #E3E7EF`, `--primary #1E3A8A`, `--accent #F59E0B`, `--success #15803D`, `--warning #B45309`, `--danger #B91C1C`.
- Oscuro: `--bg #0B1020`, `--surface #121A30`, `--ink #E8ECF6`, `--muted #9AA6BF`, `--border #232E4A`, `--primary #7C9CFF`, `--accent #FBBF24`, y variantes ajustadas de éxito/aviso/peligro.
- Verifica contraste **WCAG AA** en ambos temas.

**Tipografía:** Outfit para títulos, Inter para texto, ambas **autohospedadas** (con *fallback* a fuentes del sistema); números del cronómetro con `font-variant-numeric: tabular-nums`.

**Reglas visuales:** escala de espaciado de 4/8 px, radios y sombras definidos como tokens, iconos SVG consistentes (un solo set, en línea). **Evita:** degradados morado/azul genéricos, emojis como iconos, sombras exageradas, tarjetas idénticas apiladas sin jerarquía, texto gris de bajo contraste.

**Pantallas y componentes obligatorios**, con todos sus estados (normal, hover, foco visible, deshabilitado, error, cargando, vacío):
- Login, registro, dashboard (tarjetas de simulacros con estado y cuenta regresiva), sala de verificación (stepper de 5 pasos con estado de cada prueba), examen, resultado, ranking (podio + tabla), `/incompatible`, paneles de supervisor y admin.
- **Pantalla de examen:** barra superior con área, **cronómetro grande** (cambia de color en los últimos 10 y 5 minutos) e indicador de estado de cámara/monitoreo; zona central de la pregunta con tipografía cómoda; **navegador de preguntas** lateral en cuadrícula (estados: respondida, marcada para revisar, en blanco, actual); barra inferior anterior/siguiente/marcar; **miniatura de cámara** (~160×120) con punto de estado; avisos como *toasts* no intrusivos; overlays bloqueantes claros para pantalla completa perdida y cámara perdida.
- Accesibilidad: navegación por teclado completa, `aria-live` para avisos, foco visible, `prefers-reduced-motion` respetado.
- Resolución objetivo: 1366×768 a 1920×1080.
- Entrega en Fase 2 una página `static/design-system.html` con todos los componentes antes de aplicarlos a las pantallas reales. Si puedes renderizar y revisar capturas, hazlo y corrige antes de entregar.

---

## 13. LÍMITES CONOCIDOS (INCLÚYELOS EN `docs/ARQUITECTURA.md`, SIN OCULTARLOS)

- Un cliente manipulado puede enviar embeddings falsos o bloquear el envío de eventos; se mitiga con verificación periódica, heartbeat, evidencia y revisión humana, no se elimina.
- No se detectan de forma fiable: segundo monitor, segundo dispositivo, audífonos, ayuda fuera del encuadre.
- Los detectores pueden fallar con poca luz, lentes u otras condiciones y producir falsos positivos/negativos (incluidos sesgos entre distintos tonos de piel); por eso las sanciones son provisionales y revisables.
- La detección de celular es poco fiable; los atajos de teclado bloqueados no impiden capturas externas.
- El filtro de móviles por *user agent*/pantalla táctil se puede evadir.

---

## 14. ESTRUCTURA DEL PROYECTO

```
simulacro_unmsm/
├── wsgi.py
├── config.py
├── requirements.txt / requirements-dev.txt
├── Procfile
├── .env.example
├── .gitignore
├── migrations/                 # 0001_init.sql, ...
├── scripts/                    # migrate.py, crear_admin.py, importar_usuarios.py,
│                               # validar_preguntas.py, purgar_expirados.py, calibrar_umbral.py
├── docs/                       # ARQUITECTURA, REGLAS, DECISIONES, API, PRIVACIDAD,
│                               # CALIBRACION, RUNBOOK, PRUEBAS_MANUALES, PROGRESO (.md)
├── data/examenes/              # area_a.json ... area_e.json
├── app/
│   ├── __init__.py             # create_app
│   ├── db.py                   # pool y helpers
│   ├── security.py             # CSRF, limiter, cabeceras, decoradores de rol
│   ├── dominio/                # areas.py, constantes
│   ├── repos/                  # usuarios, intentos, respuestas, eventos, evidencias, auditoria
│   ├── services/               # puntaje, temporizador, riesgo, identidad, preguntas,
│   │                           # evidencias, cifrado
│   ├── blueprints/             # auth, dashboard, verificacion, examen, resultados,
│   │                           # ranking, supervisor, admin
│   ├── templates/
│   └── static/
│       ├── css/                # tokens.css, base.css, componentes.css, examen.css
│       ├── fonts/  img/  icons/
│       ├── models/             # modelos autohospedados (con versión)
│       ├── vendor/             # WASM/JS de MediaPipe y ONNX Runtime Web (versión fijada)
│       └── js/
│           ├── comun/          # api.js (fetch + CSRF), utilidades
│           ├── verificacion/   # sala.js, enrolamiento.js, pruebas_tecnicas.js
│           ├── examen/         # examen.js, navegador_preguntas.js, autoguardado.js
│           └── proctoring/     # engine.js (planificador adaptativo), transporte.js,
│                               # detectores/ (rostros.js, identidad.js, objetos.js),
│                               # guardias/ (foco.js, atajos.js, movil.js),
│                               # ui/ (hud.js, avisos.js, overlays.js)
└── tests/                      # unit/, integration/, js/ (node:test), load/locustfile.py
```

---

## 15. FASES (EJECUTA SOLO LA QUE YO INDIQUE)

### FASE 0: Documentación y decisiones (sin código de aplicación)
**Incluye:** repositorio con la estructura vacía de la sección 14; `ARQUITECTURA.md` (diagramas en texto/Mermaid, flujos, límites conocidos); `REGLAS.md` (puntaje, umbrales y tabla de sanciones tal como en la sección 7); `API.md` (contrato completo); `DECISIONES.md` (versiones fijadas, licencia de cada modelo/librería, supuestos); `PRIVACIDAD.md` (borrador); `PROGRESO.md`; `requirements.txt`, `.env.example`, `.gitignore`.
**No incluye:** código de la aplicación.
**Aceptación:** todas las tablas de la sección 5 y todos los endpoints de la sección 8 documentados sin contradicciones; versiones exactas y licencias listadas; lista de decisiones abiertas para mí.

### FASE 1: Núcleo del examen, sin cámara
**Incluye:** `create_app`, configuración por entorno, pool de BD, `migrate.py` y `0001_init.sql`; auth completa (registro con código de invitación, login, logout, cambio obligatorio de contraseña, sesión única, rate limit, CSRF); roles; simulacros; carga y validación del banco de preguntas; iniciar intento (token, semilla, `limite_en`); orden aleatorio determinista; autoguardado; finalizar idempotente; calificación; finalización perezosa por vencimiento; resultados; ranking. Frontend funcional con HTML básico (sin estilo final).
**No incluye:** cámara, IA, monitoreo, diseño final, paneles de supervisor/admin (salvo `crear_admin.py`).
**Pruebas obligatorias:** puntaje (casos borde: todo correcto, todo incorrecto, negativo → 0, blancos), desempate, temporizador y vencimiento, idempotencia de `finalizar`, autorización (un alumno no ve intentos ajenos), **la clave de respuestas jamás aparece en ninguna respuesta de la API**, sesión única, reanudación tras cerrar el navegador con el tiempo restante correcto.
**Aceptación:** un alumno completa un examen de principio a fin; cerrar y reabrir el navegador conserva respuestas y tiempo; doble envío no duplica; todos los tests pasan.

### FASE 2: Sistema de diseño y pantallas
**Incluye:** `tokens.css`, `base.css`, `componentes.css`, `static/design-system.html` con todos los componentes y estados; plantillas Jinja aplicadas a todas las pantallas de la Fase 1; página `/incompatible` con la guarda móvil; modo oscuro.
**No incluye:** lógica nueva de backend.
**Aceptación:** contraste AA verificado; navegación por teclado; revisión visual a 1366×768 y 1920×1080; las pantallas de la sección 12 existen con todos sus estados.

### FASE 3: Sala de verificación e identidad
**Incluye:** flujo de 5 pasos de la sección 4; consentimiento persistido; `getUserMedia` **solo** en esta sala; pruebas de cámara, luz, red y benchmark; enrolamiento (3–5 poses, estado `PENDIENTE`); verificación con reto de vida; comparación en el servidor; `verificacion_ok` de un solo uso con TTL; pantalla completa; liberación de la cámara; manejo de errores (permiso denegado, sin cámara, cámara ocupada, fallo de carga de modelos); `scripts/calibrar_umbral.py` y plantilla de `CALIBRACION.md`.
**No incluye:** monitoreo continuo durante el examen.
**Pruebas:** servicio de identidad (coseno, normalización, umbral), TTL y reutilización de `verificacion_ok`, rechazo de dimensión incorrecta, flujo de integración con embeddings simulados.
**Aceptación:** sin `verificacion_ok` válido no se puede iniciar el examen; el permiso de cámara no se pide en ninguna otra página.

### FASE 4: Motor de monitoreo en el cliente
**Incluye:** `engine.js` (planificador escalonado y adaptativo), detectores, guardias (foco, pantalla completa, atajos, móvil), `transporte.js` (lotes cada 5 s, reintentos con backoff, deduplicación por `id_cliente`), heartbeat cada 10 s, HUD, avisos y overlays; endpoints de eventos, heartbeat y evidencia (recepción y almacenamiento).
**No incluye:** las reglas de sanción del servidor (Fase 5); seguimiento de mirada.
**Pruebas:** lógica pura de ventanas y agrupación con `node:test`; checklist en `docs/PRUEBAS_MANUALES.md` (tapar la cámara, segunda persona, cambiar de pestaña, salir de pantalla completa, desconectar la cámara, cortar internet).
**Aceptación:** con 3 detectores activos en un equipo de gama media la interfaz no se traba; los eventos llegan deduplicados; el cliente sigue funcionando si el servidor tarda.

### FASE 5: Reglas en servidor, revisión y paneles
**Incluye:** `services/riesgo.py` según la sección 7 (severidad asignada por el servidor); anulación provisional; `sin_senal` generado por el servidor; panel de supervisor en vivo; detalle del intento con línea de tiempo y evidencias; confirmar/reponer con nota y auditoría; panel de admin (usuarios, importación CSV, códigos de invitación, aprobar/revocar rostros, simulacros, exportar CSV, auditoría); resultado con "OBSERVACIONES DE CONDUCTA" (o "Examen completado sin observaciones").
**Pruebas:** una prueba por cada fila de la tabla de sanciones (incluida la agrupación de episodios de `salida_foco`), reposición y confirmación, exclusión del ranking mientras la revisión está `PENDIENTE`.
**Aceptación:** todas las reglas de la sección 7 verificadas por tests; ninguna señal INFO sanciona.

### FASE 6: Seguridad y privacidad
**Incluye:** cabeceras y CSP, cifrado de embeddings, retención y purga, borrado a pedido, logs seguros, `pip-audit`, revisión contra una lista OWASP ASVS/Top 10 documentada, backups documentados, Sentry opcional.
**Aceptación:** checklist de seguridad completo y evidenciado; embeddings ilegibles en la BD; purga funcionando.

### FASE 7: Carga, ensayo y despliegue
**Incluye:** `locustfile.py` simulando **60 usuarios** (login, iniciar, autoguardado, eventos, heartbeat, finalizar); configuración de Gunicorn y del pool de BD; guía de despliegue; `RUNBOOK.md` del día del examen (antes, durante, contingencias); plan de ensayo con 8–10 personas.
**Metas:** p95 < 500 ms en endpoints ligeros, 0 errores 5xx, conexiones de BD dentro del límite del plan; entrada simultánea de 30 usuarios sin saturar la descarga de modelos.
**Aceptación:** informe de la prueba de carga con resultados reales.

---

## 16. DEFINICIÓN DE "TERMINADO" (GLOBAL)

El proyecto está terminado solo si: todas las fases tienen su cierre con evidencia; los tests pasan; no hay `TODO` ni datos simulados en producción; los límites conocidos están documentados; la prueba de carga cumple las metas; y el RUNBOOK permite a otra persona operar el día del examen.

---

## ORDEN INICIAL

**INSTRUCCIÓN HISTÓRICA DEL PROMPT ORIGINAL (NO EJECUTAR AUTOMÁTICAMENTE).** En un repositorio ya existente, ejecutar primero la FASE -1 de auditoría, comparar los requisitos con el código y esperar aprobación explícita. No reconstruir fases implementadas.
