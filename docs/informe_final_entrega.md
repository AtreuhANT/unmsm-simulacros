# Informe Final de Entrega y Arquitectura: Plataforma de Simulacros UNMSM

**Proyecto:** Plataforma de Simulacros Virtuales y Supervisión Proctoring tipo Examen de Admisión UNMSM  
**Versión:** 2.0 (Arquitectura de Alta Fiabilidad y Dirección Visual «Alma Mater»)  
**Fecha de Entrega:** Octubre 2026  
**Estado:** Todas las Fases (0 a 8) Completadas y Verificadas con Pruebas Automatizadas.

---

## 1. Resumen Ejecutivo de la Transformación

A partir de la guía arquitectónica por etapas, se rediseñó integralmente la plataforma para elevarla de un prototipo básico a un **sistema académico de nivel universitario oficial**, resolviendo los puntos críticos identificados:

1. **Privacidad y Registro Ágil:** La visita al portal, creación de cuenta (`/register`) e inicio de sesión (`/login`) ya no solicitan permisos invasivos de cámara web. Los postulantes eligen su propia contraseña segura ($\ge 6$ caracteres).
2. **Separación de Preparación e Intento:** La cámara y la verificación facial se activan únicamente en la sala previa `/preparacion/<area>`. El cronómetro oficial de 60 minutos arranca de forma inmutable en PostgreSQL solo cuando el postulante pulsa «Comenzar Examen Oficial».
3. **Persistencia Continua e Inmunidad ante `F5`:** Cada alternativa marcada se persiste en tiempo real en la tabla `respuestas_intento` mediante *upserts* atómicos. Si el navegador se cierra o el alumno recarga la página, todas sus respuestas se restauran y el reloj oficial continúa sincronizado con el servidor.
4. **Resiliencia de Red:** Incorporación de búfer local y cola de reintentos (`syncQueue`). La pérdida temporal de internet no interrumpe la evaluación ni pierde datos.
5. **Supervisión Justa para Auditoría Humana:** Las incidencias (foco, ausencias) se deduplican por episodios y se registran como observaciones de telemetría para revisión del evaluador, eliminando las descalificaciones automáticas por falsos positivos.
6. **Diseño Visual «Alma Mater» (Claro Institucional Sobrio):** Estética académica inspirada en la Decana de América con fondo marfil `#f8fafc`, tarjetas blancas de alto contraste, tipografía *Playfair Display* y *DM Sans*, y acentos en vino granate `#7b1a2a` y dorado `#92691b`.

---

## 2. Hoja de Ruta Ejecutada por Fases

### Fase 0: Especificación y Matriz de Requisitos
* Documento de diseño formal: [`docs/especificacion_fase_0.md`](file:///d:/PROYECTO/UNMSM/docs/especificacion_fase_0.md).
* Matriz de trazabilidad con 16 requisitos clave (`FL-01` a `OP-01`).

### Fase 1: Prototipo Visual y Sistema de Diseño
* Implementación de la maqueta interactiva completa: [`static/prototipo_fase1.html`](file:///d:/PROYECTO/UNMSM/static/prototipo_fase1.html) con 6 vistas navegables.
* Refactorización completa de los estilos centrales ([`static/css/base.css`](file:///d:/PROYECTO/UNMSM/static/css/base.css), [`static/css/examen.css`](file:///d:/PROYECTO/UNMSM/static/css/examen.css), [`static/css/ranking.css`](file:///d:/PROYECTO/UNMSM/static/css/ranking.css)).

### Fase 2: Banco de Pruebas Técnico de IA en Sandbox
* Creación de la página aislada de pruebas: [`static/test_ia_sandbox.html`](file:///d:/PROYECTO/UNMSM/static/test_ia_sandbox.html) (accesible vía `/test-ia`).
* Verificación de pesos locales en `static/models/` (TinyFaceDetector, FaceLandmark68Tiny, FaceRecognitionNet) sin dependencias de CDNs externos.
* Validación del umbral euclidiano 1:1 ($\le 0.55$) y apagado estricto de pistas multimedia.

### Fase 3: Backend, Esquema PostgreSQL y Autenticación
* Modelos relacionales con pool multihilo:
  * `plantillas_faciales`: Almacenamiento seguro de vectores biométricos.
  * `intentos`: Ciclo de vida oficial (`EN_CURSO`, `ENTREGADO`, `VENCIDO`) con sellado temporal.
  * `respuestas_intento`: Restricción única `(intento_id, pregunta_id)` con control de revisión concurrente.
* Endpoints RESTful en [`routes/api.py`](file:///d:/PROYECTO/UNMSM/routes/api.py):
  * `POST /api/intento/iniciar`, `GET /api/intento/activo`, `POST /api/intento/respuesta`, `POST /api/intento/enrolar-facial`.
* Registro sin cámara web en [`templates/register.html`](file:///d:/PROYECTO/UNMSM/templates/register.html) y contraseñas seguras en [`routes/auth.py`](file:///d:/PROYECTO/UNMSM/routes/auth.py).

### Fase 4: Motor de Examen Confiable
* Controlador principal en [`static/js/monitor_engine.js`](file:///d:/PROYECTO/UNMSM/static/js/monitor_engine.js).
* Sincronización continua con retroalimentación visual (`✓ Guardado en servidor`).
* Inmunidad ante recargas accidentales (`F5`) restaurando tiempo exacto y respuestas marcadas.
* Sanitización estricta del banco de preguntas en cliente (`sanitizar_preguntas_para_cliente`).

### Fase 5: Sala de Preparación e Identidad
* Vista dedicada [`templates/preparacion.html`](file:///d:/PROYECTO/UNMSM/templates/preparacion.html) (`/preparacion/<area>`).
* Diferenciación de auto-enrolamiento en el primer intento y verificación 1:1 en intentos posteriores.
* Apagado forzado del hardware de cámara web al salir de la sala o cancelar (`stopCamera()`).
* Redirección automática si el estudiante intenta acceder a preparación teniendo un examen ya activo.

### Fase 6: Supervisión y Telemetría Limpia
* Submódulos proctoring desacoplados:
  * [`static/js/modulos/facial_presence.js`](file:///d:/PROYECTO/UNMSM/static/js/modulos/facial_presence.js): Ciclos de 6 segundos, tolerancia a miradas hacia abajo y registro solo ante ausencias $>12$s.
  * [`static/js/modulos/focus_monitor.js`](file:///d:/PROYECTO/UNMSM/static/js/modulos/focus_monitor.js): Agrupación por episodios con debounce de 2 segundos y medición de tiempo fuera.
  * [`static/js/modulos/screenshot_guard.js`](file:///d:/PROYECTO/UNMSM/static/js/modulos/screenshot_guard.js): Bloqueo de atajos (PrintScreen, F12, DevTools) con enfriamiento de 3s.
* Registro de observaciones en `eventos_monitoreo` para auditoría formal.

### Fase 7: Resultados, Auditoría y Ranking Oficial
* Vista de resultados enriquecida en [`templates/resultado.html`](file:///d:/PROYECTO/UNMSM/templates/resultado.html):
  * Revisión interactiva de preguntas con filtros (`Todas`, `Correctas`, `Incorrectas`, `En Blanco`).
  * Fundamento Académico DECO con la explicación pedagógica de cada clave oficial.
  * Línea de tiempo de auditoría con incidentes ordenados cronológicamente.
* Cuadro de Mérito y Ranking en [`templates/ranking.html`](file:///d:/PROYECTO/UNMSM/templates/ranking.html):
  * Regla oficial UNMSM: 1° Puntaje, 2° Tiempo de resolución.
  * Podio de honor con medallas y enmascaramiento de DNI (`77****11`).

### Fase 8: Pruebas de Carga y Concurrencia
* Script de prueba de estrés multi-hilo: [`tests/test_concurrencia_30.py`](file:///d:/PROYECTO/UNMSM/tests/test_concurrencia_30.py).
* **30 postulantes simultáneos** ejecutando 450 transacciones en paralelo.
* **0 errores, 0 fugas de conexiones y 100% de éxito**.
* Latencia media de guardado incremental: **63.60 ms**.

---

## 3. Guía de Ejecución y Operación

### 3.1 Requisitos del Sistema
* Python 3.9 o superior.
* PostgreSQL 13 o superior activo en el puerto 5432.
* Navegador moderno compatible con WebRTC (Google Chrome, Microsoft Edge, Firefox, Brave).

### 3.2 Iniciar la Aplicación en Modo Desarrollo
```powershell
python app.py
```
La consola indicará:
```
INFO in database: Pool de conexiones PostgreSQL inicializado correctamente.
INFO in database: Esquema de base de datos verificado e inicializado correctamente.
 * Running on http://127.0.0.1:5000
```

### 3.3 Ejecución de Pruebas Unitarias y de Carga
```powershell
# Suite completa de pruebas unitarias
python -m unittest discover tests

# Benchmark de concurrencia de 30 usuarios
python tests/test_concurrencia_30.py
```

---

## 4. Estructura Final del Repositorio

```
UNMSM/
├── app.py                     # Fábrica de aplicación Flask y registro de Blueprints
├── config.py                  # Parámetros centralizados, puntajes UNMSM y pool de BD
├── requirements.txt           # Dependencias Python
├── models/
│   ├── database.py            # Pool multihilo PostgreSQL e inicialización DDL
│   ├── usuario.py             # Autenticación, contraseñas y plantillas faciales
│   ├── intento.py             # Ciclo de vida del examen y persistencia incremental
│   └── resultado.py           # Calificación oficial, eventos y ranking
├── routes/
│   ├── auth.py                # Login y Registro sin cámara
│   ├── dashboard.py           # Panel principal con banner de examen activo
│   ├── simulacro.py           # Rutas /preparacion/<area> y /examen/<area>
│   ├── api.py                 # Endpoints REST para intento, respuestas y telemetría
│   └── resultados.py          # Vistas de resultado DECO, auditoría y ranking
├── static/
│   ├── css/
│   │   ├── base.css           # Sistema de diseño "Alma Mater"
│   │   ├── examen.css         # Interfaz HUD del examen y badge de sincronización
│   │   └── ranking.css        # Podio de honor y tabla de mérito
│   ├── js/
│   │   ├── monitor_engine.js  # Orquestador del examen, búfer offline y reloj
│   │   └── modulos/           # Supervisión: facial, foco y atajos
│   ├── models/                # Pesos neuronales locales de face-api.js
│   ├── prototipo_fase1.html   # Prototipo visual completo de 6 pantallas
│   └── test_ia_sandbox.html   # Sandbox técnico de IA
├── templates/
│   ├── base.html              # Layout base institucional
│   ├── register.html          # Registro limpio sin cámara
│   ├── login.html             # Acceso de usuarios
│   ├── dashboard.html         # Panel del estudiante
│   ├── preparacion.html       # Sala previa con verificación 1:1
│   ├── examen.html            # Examen oficial en vivo
│   ├── resultado.html         # Desglose DECO y auditoría
│   └── ranking.html           # Cuadro de mérito oficial
├── tests/
│   ├── test_puntuacion.py     # Pruebas de fórmula UNMSM (+20 / -1.125 / 0.0)
│   ├── test_seguridad_flujo.py# Pruebas de sesión e idempotencia
│   └── test_concurrencia_30.py# Benchmark de estrés para 30 usuarios simultáneos
└── docs/
    ├── especificacion_fase_0.md # Matriz de trazabilidad y arquitectura
    └── informe_final_entrega.md # El presente informe técnico consolidado
```

---
*Plataforma desarrollada y verificada conforme a los más altos estándares de confiabilidad, seguridad y pedagogía académica.*
