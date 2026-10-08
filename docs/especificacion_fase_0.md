# FASE 0: DOCUMENTO DE ESPECIFICACIÓN TÉCNICA Y CONTRATOS
## Sistema de Simulacros de Admisión UNMSM con Supervisión Biométrica Edge

---

## 1. Alcance del MVP y Actores

### 1.1 Objetivo del Producto
Construir una plataforma web de simulacros para el examen de admisión de la Universidad Nacional Mayor de San Marcos (UNMSM) que ofrezca:
1. Una experiencia de evaluación fidedigna a las reglas de calificación y áreas académicas oficiales.
2. Un motor de examen de alta confiabilidad que persista las respuestas de forma continua e impida la pérdida de datos ante desconexiones o recargas.
3. Un subsistema de supervisión por IA local en el navegador (Edge Computing) que registre telemetría e incidentes para auditoría académica sin vulnerar la privacidad ni colapsar el ancho de banda del servidor.

### 1.2 Actores del Sistema
* **Postulante / Alumno:**
  * Crea su cuenta con credenciales personalizadas sin necesidad de cámara.
  * Consulta su panel con historial, puntajes y catálogo de simulacros por área.
  * Realiza el protocolo de preparación técnica y enrolamiento/verificación biométrica voluntaria antes de rendir.
  * Resuelve el examen con persistencia continua de respuestas y tiempo sincronizado.
  * Visualiza su reporte de resultados con desglose de puntos y estado de supervisión.
  * Consulta el ranking general y por especialidad.
* **Administrador / Supervisor:**
  * Monitorea estadísticas globales de evaluaciones (completadas, observadas, promedios).
  * Audita la telemetría de incidentes (cambios de foco, ausencia facial, múltiples rostros).
  * Valida o anula exámenes observados con registro de auditoría justificatoria.
  * Gestiona versiones de exámenes y postulantes.

### 1.3 Límites Explícitos de la Supervisión
* **Confianza en el Cliente:** La inferencia por IA (`face-api.js`) se ejecuta en el navegador del postulante. Por diseño fundamental de la web, un cliente modificado puede alterar señales locales.
* **Valor de las Detecciones:** Las incidencias detectadas (pérdida de foco, ausencia de rostro, discrepancia biométrica) se tratan como **señales de telemetría para revisión humana**, no como causales de expulsión automática ciega por el sistema.

---

## 2. Mapa de Pantallas y Flujo de Usuario Refinado

```
[Portada / Landing]
         │
         ├───> [Inicio de Sesión (/login)] ───┐
         │                                    ▼
         └───> [Registro (/register)]  ──> [Dashboard (/dashboard)]
               (Sin cámara, clave segura)     │
                                              ├─ Historial de resultados
                                              ├─ Métricas de rendimiento
                                              └─ Selección de Simulacro por Área
                                                      │
                                                      ▼
                                         [Preparación Técnica Pre-Examen]
                                         (Carga IA, permisos, cámara voluntaria,
                                          enrolamiento 1ª vez o verificación 1:1)
                                                      │
                                          [Comenzar Examen (Petición Backend)]
                                          * El reloj oficial arranca AQUÍ *
                                                      ▼
                                            [Examen en Vivo]
                                            ├─ Guardado incremental continuo
                                            ├─ HUD compacto de webcam
                                            ├─ Matriz de navegación + Deselección
                                            └─ Tolerancia a desconexiones (F5)
                                                      │
                                                      ▼
                                            [Entrega / Calificación Backend]
                                                      │
                                                      ▼
                                            [Informe de Resultados]
                                            ├─ Puntaje UNMSM (+20 / -1.125 / 0)
                                            └─ Observaciones de Supervisión
                                                      │
                                                      ▼
                                            [Ranking Oficial UNMSM]
```

### 2.1 Detalle de Flujos Clave
1. **Registro sin Fricción (`/register`):**
   * Campos requeridos: Nombres, Apellidos, DNI, Correo/Usuario, Contraseña personalizada (mínimo 6 caracteres, confirmación obligatoria), Área Académica y Carrera.
   * **Cero solicitud de cámara web ni carga de modelos de visión artificial.**
2. **Sala de Preparación Pre-Examen:**
   * Se accede tras pulsar "Preparar Simulacro" en el dashboard.
   * Se informa de forma transparente qué datos se procesarán localmente (vectores matemáticos de 128 floats, nunca video grabado).
   * Se cargan los pesos locales de IA con barra de progreso visible.
   * Botón explícito "Activar Cámara".
   * **Caso 1 (Usuario sin plantilla):** Enrolamiento guiado. Se toman 3 muestras del rostro con buena iluminación para crear la referencia facial base.
   * **Caso 2 (Usuario con plantilla existente):** Verificación 1:1 calculando la distancia euclidiana mínima.
   * El cronómetro del examen **NO se consume** durante esta fase.
3. **Inicio y Persistencia Continua del Examen:**
   * El postulante pulsa "Iniciar Examen en Pantalla Completa".
   * El backend crea el registro en la tabla `intentos`, fija `fecha_inicio` y `fecha_vencimiento_oficial`, y emite el `token_sesion`.
   * Al hacer clic en una alternativa (A, B, C, D, E), la respuesta se envía inmediatamente mediante `POST /api/intento/respuesta` y el frontend muestra un indicador `Guardado ✓`.
   * Si el usuario desmarca la opción, se envía estado `en_blanco: true`.
   * Si el usuario recarga la pestaña (`F5`), el frontend solicita `/api/intento/activo`. El servidor retorna las preguntas, las respuestas ya confirmadas y el tiempo restante exacto calculado por el reloj del servidor.

---

## 3. Modelo de Datos Refinado (PostgreSQL)

### 3.1 Tablas Principales
* **`usuarios`**:
  * `id` (SERIAL PRIMARY KEY)
  * `nombre` (TEXT NOT NULL)
  * `apellido` (TEXT NOT NULL)
  * `dni` (VARCHAR(15) UNIQUE NOT NULL)
  * `password_hash` (TEXT NOT NULL) - *Contraseña real, nunca DNI por defecto*
  * `area` (CHAR(1) NOT NULL)
  * `carrera` (TEXT NOT NULL)
  * `es_admin` (BOOLEAN DEFAULT FALSE)
  * `creado_en` (TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP)

* **`plantillas_faciales`** *(Desacoplada de usuario)*:
  * `id` (SERIAL PRIMARY KEY)
  * `usuario_id` (INT REFERENCES usuarios(id) ON DELETE CASCADE)
  * `modelo_version` (VARCHAR(50) NOT NULL) - *Ej: 'face-api-tiny-0.22'*
  * `dimension` (INT DEFAULT 128)
  * `descriptores` (JSONB NOT NULL) - *Array de vectores normalizados*
  * `estado_acreditacion` (VARCHAR(30) DEFAULT 'AUTO_ENROLADO')
  * `creado_en` (TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP)

* **`examenes_versiones`**:
  * `id` (SERIAL PRIMARY KEY)
  * `area` (CHAR(1) NOT NULL)
  * `titulo` (TEXT NOT NULL)
  * `version` (INT DEFAULT 1)
  * `duracion_minutos` (INT DEFAULT 60)
  * `preguntas_json` (JSONB NOT NULL) - *Snapshot inmutable de preguntas*
  * `activo` (BOOLEAN DEFAULT TRUE)

* **`intentos`**:
  * `id` (SERIAL PRIMARY KEY)
  * `usuario_id` (INT REFERENCES usuarios(id) ON DELETE CASCADE)
  * `examen_version_id` (INT REFERENCES examenes_versiones(id))
  * `token_sesion` (UUID UNIQUE NOT NULL)
  * `fecha_inicio` (TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)
  * `fecha_vencimiento` (TIMESTAMPTZ NOT NULL)
  * `fecha_cierre` (TIMESTAMPTZ)
  * `estado_academico` (VARCHAR(20) DEFAULT 'EN_CURSO') - *'EN_CURSO', 'ENTREGADO', 'VENCIDO', 'ABANDONADO'*
  * `estado_supervision` (VARCHAR(25) DEFAULT 'SIN_OBSERVACIONES') - *'SIN_OBSERVACIONES', 'PENDIENTE', 'VALIDADO', 'ANULADO'*

* **`respuestas_intento`**:
  * `id` (SERIAL PRIMARY KEY)
  * `intento_id` (INT REFERENCES intentos(id) ON DELETE CASCADE)
  * `pregunta_id` (INT NOT NULL)
  * `opcion_seleccionada` (CHAR(1))
  * `es_blanco` (BOOLEAN DEFAULT FALSE)
  * `marcado_revision` (BOOLEAN DEFAULT FALSE)
  * `numero_revision` (INT DEFAULT 1) - *Para rechazar peticiones tardías fuera de orden*
  * `actualizado_en` (TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP)
  * *CONSTRAINT UNIQUE (intento_id, pregunta_id)*

* **`eventos_monitoreo`**:
  * `id` (SERIAL PRIMARY KEY)
  * `intento_id` (INT REFERENCES intentos(id) ON DELETE CASCADE)
  * `modulo` (VARCHAR(50) NOT NULL) - *'facial_presence', 'focus_monitor', 'screenshot_guard'*
  * `tipo` (VARCHAR(50) NOT NULL) - *'ausencia', 'multiple_rostro', 'no_coincide', 'foco_perdido'*
  * `descripcion` (TEXT)
  * `segundo_examen` (INT NOT NULL)
  * `registrado_en` (TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP)

* **`resultados`**:
  * `id` (SERIAL PRIMARY KEY)
  * `intento_id` (INT UNIQUE REFERENCES intentos(id) ON DELETE CASCADE)
  * `puntaje` (NUMERIC(7,3) NOT NULL DEFAULT 0.0)
  * `correctas` (INT NOT NULL DEFAULT 0)
  * `incorrectas` (INT NOT NULL DEFAULT 0)
  * `blanco` (INT NOT NULL DEFAULT 0)
  * `tiempo_segundos` (INT NOT NULL DEFAULT 0)
  * `motivo_revision` (TEXT)
  * `evaluado_por` (INT REFERENCES usuarios(id))

---

## 4. Matriz de Requisitos y Trazabilidad (Fases 0 a 8)

| ID | Requisito | Fases | Criterio de Aceptación / Evidencia |
| :--- | :--- | :---: | :--- |
| **FL-01** | Navegación y registro sin cámara | 1, 3, 5 | Portada, `/login`, `/register` y `/dashboard` no solicitan permisos multimedia ni cargan scripts pesados. |
| **FL-02** | Enrolamiento separado de verificación | 0, 2, 5 | Flujo de enrolamiento inicial crea plantilla; intentos posteriores usan comparación 1:1. |
| **FL-03** | Preparación previa sin consumo de tiempo | 4, 5 | El cronómetro del examen comienza solo tras `POST /api/intento/iniciar`. |
| **FL-04** | Cancelación y liberación de recursos | 2, 5 | Salir de la preparación o del examen apaga los tracks de la cámara web (`stream.getTracks().forEach(t => t.stop())`). |
| **UI-01** | Dirección visual sobria y profesional | 1 | Paleta armoniosa, tipografía legible (16-18px cuerpo), contraste verificado y sin decoraciones que distraigan. |
| **UI-02** | Accesibilidad y estados de error | 1, 8 | Soporte para teclado en opciones, foco visible, estados de carga, sin conexión y feedback de guardado. |
| **EX-01** | Banco inmutable y claves privadas | 3, 4 | El frontend jamás recibe `correcta` ni `explicacion` mientras el intento está en curso. |
| **EX-02** | Reloj de servidor y recuperación ante F5 | 4 | Si el postulante recarga la página, el tiempo restante se calcula en base a `fecha_vencimiento - NOW()` de PostgreSQL. |
| **EX-03** | Guardado incremental de respuestas | 4 | Cada selección se sincroniza al instante en `respuestas_intento` con confirmación visual. |
| **EX-04** | Tolerancia a cortes de red | 4 | Buffer local ante desconexión temporal; reintento automático y aviso visible de estado offline. |
| **EX-05** | Finalización e idempotencia estricta | 4, 8 | Transacción única para cerrar el intento. Entregas dobles retornan el resultado existente sin duplicar filas. |
| **EX-06** | Cierre automático de intentos vencidos | 4, 8 | El servidor rechaza respuestas posteriores al vencimiento y cierra el examen automáticamente. |
| **AC-01** | Calificación oficial UNMSM parametrizada | 0, 7 | Fórmula oficial: `+20.0` acierto, `-1.125` error, `0.0` blanco. Límite inferior no negativo (mínimo 0.0 pts). |
| **SE-01** | Seguridad de contraseñas y sesiones | 3, 8 | Contraseña con hash Werkzeug elegida por el usuario; cookies `HttpOnly`, `SameSite=Lax`. |
| **SE-02** | Protección de plantillas faciales | 5 | Ninguna API pública expone vectores faciales de otros usuarios. |
| **IA-01** | Modelos locales offline completos | 2 | Pesos descargados localmente en `static/models/` sin dependencias de CDNs externos. |
| **IA-02** | Diferenciación de calidad e incertidumbre | 2, 5 | La falta de iluminación o rostro no centrado se reporta como aviso de ajuste técnico, no como fraude. |
| **IA-03** | Rendimiento y no bloqueo de interfaz | 2, 6 | Inferencia no acumulada; frecuencia adaptable de inspección (1 muestra cada 5-8 seg). |
| **MO-01** | Deduplicación de eventos de supervisión | 6 | Una pérdida de foco no genera ráfagas de 10 eventos; se agrupa por episodio con debounce. |
| **MO-02** | Separación entre aviso, reporte y sanción | 6, 7 | El sistema registra observaciones; la anulación es potestad administrativa o por infracción grave verificada. |
| **RA-01** | Ranking oficial y privacidad | 7 | Cuadro de mérito ordenado por puntaje desc y tiempo asc. DNI oculto en vistas públicas. |
| **OP-01** | Concurrencia de 30 usuarios simultáneos | 8 | Pruebas de carga HTTP verificando que el pool de conexiones soporte guardados continuos concurrentes. |

---

## 5. Casos de Error y Recuperación de Fallos

1. **Permiso de Cámara Denegado:**
   * No bloquea la aplicación. Muestra una guía gráfica para habilitar permisos en Chrome/Edge y botón para regresar al Dashboard. El tiempo del examen nunca se inicia.
2. **Corte de Conexión a Internet durante el Examen:**
   * La interfaz muestra un banner superior ámbar: *«Sin conexión. Guardando localmente tus respuestas...»*.
   * Las respuestas marcadas se conservan en memoria / `localStorage`. Al restablecerse la red, se sincronizan por lotes con el servidor.
   * El reloj oficial del examen en el servidor continúa corriendo para evitar fraudes por desconexión provocada.
3. **Recarga Involuntaria o Cierre del Navegador (`F5` / Accidente):**
   * Al reingresar al simulacro, el sistema detecta que existe un intento `EN_CURSO` y carga las preguntas junto con todas las respuestas confirmadas previamente en la base de datos.
4. **Respuestas Tardías o Fuera de Plazo:**
   * Si una respuesta llega después de la `fecha_vencimiento` (con margen de tolerancia de red de 10s), el servidor responde `HTTP 403 / 410: Intento Vencido` y no modifica el registro.
5. **Falsos Positivos de Supervisión (Popups de Windows, Antivirus):**
   * Se añade un debounce de 2 segundos. Un cambio de ventana momentáneo registra un evento leve de advertencia, pero no penaliza con descalificación inmediata.

---

## 6. Criterios de Aceptación por Fases (Hoja de Ruta)

* **Fase 0 (Actual):** Aprobación del presente documento de especificación, matriz de requisitos y resolución de decisiones clave.
* **Fase 1 (Prototipo Visual):** Presentación de dos direcciones visuales para Panel, Preparación y Examen; validación de jerarquía, lectura y ergonomía antes de escribir lógica backend.
* **Fase 2 (Prueba de IA Aislada):** Banco de pruebas en página aislada para verificar carga de pesos, rendimiento de FPS/latencia de `face-api.js` y liberación estricta de memoria.
* **Fase 3 (Backend y Migraciones):** Implementación del esquema PostgreSQL (`intentos`, `respuestas_intento`, `plantillas_faciales`), registro sin cámara y autenticación con contraseña segura.
* **Fase 4 (Motor de Examen Confiable):** Navegación completa, guardado incremental de respuestas, sincronización de reloj en servidor y calificación idempotente.
* **Fase 5 (Integración de Preparación e Identidad):** Módulo de preparación previa con enrolamiento y verificación 1:1 antes de autorizar el arranque del cronómetro.
* **Fase 6 (Supervisión y Telemetría Limpia):** Detección facial periódica, deduplicación de eventos de foco y panel de avisos no destructivos.
* **Fase 7 (Resultados, Auditoría y Ranking):** Reporte detallado de respuestas, panel de supervisión de incidentes y ranking por carreras/áreas.
* **Fase 8 (Pruebas de Carga y Despliegue):** Ensayo con 30 conexiones concurrentes simuladas y verificación de memoria en equipos reales.

---

## 7. Decisiones Aprobadas en Fase 0

1. **Dirección Visual (Fase 1):**
   * Se diseñarán y presentarán **ambas direcciones** (Tema Claro institucional sobrio vs. Tema Oscuro moderno con paleta vino `#7b1a2a` y dorado `#b8923a`) en maquetas de demostración de tres pantallas clave (Panel, Preparación y Examen) para compararlas antes de fijar los estilos definitivos.
2. **Tratamiento de Incidencias de Supervisión:**
   * Las alertas de conducta (pérdidas de foco, ausencia facial momentánea o no coincidencia) se registrarán como **Observaciones de Auditoría para revisión del evaluador/administrador**. No se descalificará ciegamente a los postulantes por ráfagas de falsos positivos en el navegador.
3. **Contenido Académico y Banco de Preguntas:**
   * Para el desarrollo del MVP se utilizará el banco actual de 20 preguntas modelo por área (A, B, C, D, E), estructurado de manera flexible y versionada en JSON/Base de Datos para permitir su sustitución sin fricción por el banco oficial definitivo que proporcionará el usuario.
