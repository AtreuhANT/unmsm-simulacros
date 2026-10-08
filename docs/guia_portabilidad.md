# Configurar el proyecto en otra PC

Clonar el repositorio y seguir `README.md` para instalar dependencias, crear `.env` con valores propios y ejecutar la aplicación con PostgreSQL local o Docker.

`SECRET_KEY` y `DATABASE_URL` son obligatorias. Docker exige además `POSTGRES_PASSWORD` y `DOCKER_DATABASE_URL`.

El repositorio contiene código y bancos de preguntas. No contiene usuarios, resultados, plantillas biométricas, `.env` ni backups. Los datos personales requieren un traslado privado autorizado y no deben publicarse en GitHub.

No ejecutar descubrimiento global de pruebas ni importar `app.py` contra la base de desarrollo. Consultar `AGENTS.md` para las pruebas de integración y el aislamiento requerido.
