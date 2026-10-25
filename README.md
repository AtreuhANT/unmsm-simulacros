# Simulacros UNMSM

En el proyecto usamos Flask, PostgreSQL y supervisión mediante cámara en el navegador. La implementación es parcial: consultar `docs/AUDITORIA_INICIAL.md`, `docs/PROGRESO.md` y `AGENTS.md` antes de continuar.

## Configuración local

Para que lo instales en tu laptop te dejo la guía y ya sigues los pasos nomás, cualquier cosa me escribes al wsp para seguir desarrollando o hacer los cambios correspondientes, la base de datos ya hacemos una nueva para la exposición y si es para el profe, haremos que el de registre para que vea el funcionamiento de la pág. Seguir la [guía completa para otra PC](docs/guia_portabilidad.md). Incluye instalación de Python/PostgreSQL, creación de usuario y base propios, configuración privada y arranque. No se necesita restaurar un respaldo.

```powershell
git clone https://github.com/AtreuhANT/unmsm-simulacros.git
cd unmsm-simulacros
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Guardar la clave generada en `SECRET_KEY` dentro de `.env`. Configurar `DATABASE_URL` con una base PostgreSQL propia. Codificar los caracteres especiales de la contraseña para usarlos en una URL. `.env` es privado y no se comparte por Git.

Con PostgreSQL instalado y en ejecución, `crear_bd.bat` crea la base indicada en `.env`; `iniciar.bat` inicia la aplicación en http://localhost:5000. El arranque puede crear o ajustar tablas: usar una base dedicada al proyecto.

## Docker

En `.env`, definir `SECRET_KEY`, `POSTGRES_PASSWORD` y `DOCKER_DATABASE_URL`. La URL de Docker utiliza el host `db`, por ejemplo `postgresql://postgres:TU_PASSWORD@db:5432/simulacro_db`, y debe contener la misma contraseña que `POSTGRES_PASSWORD`.

```powershell
docker compose up --build
```

## Colaboración

La captura de fotografías durante detecciones de celular, el acceso del administrador y la purga de evidencias se explican en [EVIDENCIAS.md](docs/EVIDENCIAS.md).

Invitar al compañero desde Settings → Collaborators del repositorio. Ambos deben seguir `AGENTS.md` y las fases autorizadas.

```powershell
git pull --ff-only
git switch -c mejora/nombre-del-cambio
# Realizar y verificar el cambio.
git add ruta/del/archivo
git commit -m "Descripción del cambio"
git push -u origin mejora/nombre-del-cambio
```

Abrir una pull request hacia `main` para revisar el cambio entre ambos. No subir `.env`, backups SQL, datos personales ni plantillas biométricas.

## Comprobaciones aisladas

Los simulacros supervisados de las áreas **A, B, C, D y E ya utilizan 100 preguntas y duran 3 horas por nuevo intento**. Se inician desde «Preparar Simulacro» en el dashboard. Las áreas B–E usan [material original de práctica](docs/PRACTICA_AREAS_BCDE.md), con tres lecturas sin imágenes y figuras de apoyo en Geometría; A conserva los textos, fórmulas y figuras revisados del PDF. Los enlaces «Revisar Área» permiten consultar una vista sin iniciar el reloj.

Cada nuevo intento guarda su versión de preguntas en la tabla existente `examenes_versiones`. Recargar mantiene el contenido y vencimiento originales. Los intentos anteriores sin versión conservan los bancos de diez preguntas archivados en `data/examenes/anteriores/` y su plazo previo. La duración del servidor se fija en 180 minutos en `config.py`; valores antiguos en `.env` no la reducen.

Para publicar futuras modificaciones de los bancos revisados, ejecutar `scripts/activar_bancos_100.py` después de regenerarlos. Conserva el archivo histórico y valida las cinco áreas antes de escribir los bancos activos.

Con `SECRET_KEY` y `DATABASE_URL` configuradas:

```powershell
python -m unittest tests.test_puntuacion tests.test_modelos -v
```

No ejecutar pruebas de integración ni importar `app.py` sin verificar una base efímera de pruebas: la importación puede inicializar el esquema. La subfase de seguridad 1A continúa pendiente de autorización separada. La publicación conserva los hallazgos de integridad de calificaciones de la auditoría.
