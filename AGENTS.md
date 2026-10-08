# AGENTS.md — Plataforma de simulacros de admisión

## Contexto y fuentes
Proyecto **existente y parcialmente implementado**. No partir desde cero ni reemplazar componentes funcionales por una arquitectura nueva sin autorización. Consultar antes de cada decisión relevante:
- `docs/ESPECIFICACION.md`: requisitos completos y fases de referencia.
- `docs/REGLAS.md`: reglas del monitoreo y revisión humana.
- `docs/AUDITORIA_INICIAL.md`: evidencias del estado real del repositorio.
- `docs/PROGRESO.md`: seguimiento del trabajo.

En caso de discrepancia entre la especificación y el código existente, documentar: implementación actual, requisito, impacto, propuesta, pruebas necesarias y aprobación requerida. No interpretar las órdenes históricas del prompt maestro como autorización para ejecutar automáticamente la Fase 0 ni otra fase.

## Forma de trabajar
1. **Inspeccionar → comprender → planificar → pedir aprobación → modificar mínimamente → probar → informar**.
2. Ejecutar solo la fase/subfase expresamente aprobada. Antes de cambios de riesgo medio o alto, presentar plan (máximo 15 líneas) y esperar permiso.
3. Preservar archivos y cambios no confirmados del usuario; revisar el estado de Git antes de editar, cuando esté disponible. No crear commits ni ramas ni hacer push sin permiso.
4. Nunca afirmar que una prueba se ejecutó si no se ejecutó. Reportar comandos, salidas, limitaciones y pruebas fallidas.
5. No introducir implementaciones ficticias, `TODO` o mocks como comportamiento de producción. Los fixtures de prueba sí pueden ser ficticios y deben quedar aislados.
6. Tras cada fase actualizar `docs/PROGRESO.md`, resumir diff/archivos afectados, criterios de aceptación, pruebas y pendientes. Mantener documentación y explicaciones en español.

## Restricciones de seguridad
- El **servidor es la autoridad** para autorizar usuarios e intentos, tiempo, resultados, calificación, estado, sanciones y revisión. Nunca aceptar del navegador como verdad `puntaje`, `area`, `estado`, `tiempo` ni autorización de anulación.
- No enviar claves correctas en respuestas de API. Validar sesión, token, propiedad del intento, estado, autorización, CSRF y límites de entrada.
- Las operaciones de cierre, persistencia y calificación deben ser coherentes ante solicitudes repetidas y concurrentes; planificar transacciones e idempotencia.
- La inferencia de cámara ocurre en navegador según la especificación. Tratar embeddings y evidencias como información sensible; cifrar, restringir y no registrar secretos ni biometría en logs.
- No ejecutar operaciones destructivas (`git reset --hard`, `git clean -fd`, `git push --force`, DROP TABLE/DATABASE, eliminación masiva, migraciones destructivas) sin autorización expresa.
- No sobrescribir `.env`, claves, credenciales, certificados ni configuraciones locales; no publicar datos sensibles.

## Especial: pruebas y PostgreSQL
**Se ha detectado que importar `app.py` podría inicializar el esquema y tocar la base de datos.** Antes de importar la aplicación o ejecutar pruebas de integración, verificar que la conexión apunta exclusivamente a una base efímera/de pruebas. Rechazar explícitamente cualquier configuración ambigua o que coincida con una base de desarrollo/prod. No imprimir credenciales completas. Si no puede garantizarse aislamiento, detener la ejecución y solicitar instrucciones.

La subfase 1A de pruebas de seguridad requiere aprobación separada (`OK SUBFASE 1A`). No corregir endpoints de entrega ni modificar el esquema durante esa subfase. La subfase 1B requiere nueva aprobación.

## Tecnologías y futuro
Preservar el stack real existente; evaluar Svelte/Vite, cambios de infraestructura, portada interactiva, imágenes de preguntas y despliegue como decisiones futuras independientes, no autorizadas por este archivo. Priorizar integridad de calificaciones y pruebas frente a cambios visuales.
