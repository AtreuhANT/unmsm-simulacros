# Preparación de publicación — 2026-10-08

El usuario autorizó publicar el proyecto y preparar una copia limpia, conservando la carpeta, `.env` e historial originales.

## Cambios de la copia

- `config.py`: se eliminan secretos de respaldo; `SECRET_KEY` y `DATABASE_URL` deben configurarse por entorno. La aplicación falla con un mensaje claro si faltan.
- `docker-compose.yml`: contraseña de PostgreSQL, conexión y clave de sesiones por variables obligatorias.
- `.env.example`: ejemplos y secretos vacíos que cada desarrollador debe completar.
- `README.md`: configuración, colaboración por pull requests y pruebas aisladas.
- `docs/guia_portabilidad.md`: se retiran claves fijas y la recomendación de ejecutar todas las pruebas contra la base local.

Requisito de referencia: especificación, sección 9, secretos por entorno; AGENTS.md, prohibición de publicar datos sensibles. Impacto: configurar el entorno antes del arranque. Propuesta aprobada: copia independiente para no subir el commit original con secretos. Verificación necesaria: compilación, pruebas unitarias aisladas y revisión de archivos antes del push.

No se corrigen endpoints ni se migra el esquema o el stack. El fallo del botón de preparación queda fuera de esta publicación. Las subfases 1A y 1B siguen pendientes.
