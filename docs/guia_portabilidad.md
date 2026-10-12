# Configurar el proyecto en otra PC

## Instalación nueva en Windows (PowerShell)

Cada compañero instala sus herramientas y crea su propia base local. GitHub entrega el código; no instala PostgreSQL ni copia los datos de otro equipo.

### 1. Instalar herramientas

Instalar Git, Python 3.12 y PostgreSQL 17 desde sus proveedores oficiales o con WinGet:

```powershell
winget install --id Git.Git --exact --source winget
winget install --id Python.Python.3.12 --exact --source winget --scope user
winget install --id PostgreSQL.PostgreSQL.17 --exact --source winget --interactive
```

En PostgreSQL, instalar el servidor y las herramientas de línea de comandos; pgAdmin es opcional. Conservar el puerto 5432 si está libre y guardar la contraseña del usuario `postgres` en un gestor privado. Stack Builder no es necesario. Si ya existe una instalación, comprobarla antes de instalar otra. Cerrar y abrir la terminal tras instalar.

### 2. Descargar e instalar dependencias

```powershell
git clone https://github.com/AtreuhANT/unmsm-simulacros.git
cd unmsm-simulacros
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
```

Si el lanzador `py` no está disponible, usar el ejecutable instalado: `& "$env:LOCALAPPDATA/Programs/Python/Python312/python.exe" -m venv .venv`. Se usa el ejecutable del entorno directamente, sin cambiar la política de ejecución de PowerShell. No copiar el entorno virtual desde otra PC.

Las dependencias actuales declaran versiones mínimas, no un bloqueo exacto; dos instalaciones en fechas distintas pueden resolver versiones diferentes. Gunicorn forma parte de los requisitos de despliegue y se utiliza en Linux; para desarrollo en Windows se usa Flask. No hace falta instalar Node ni Docker para esta ruta local.

### 3. Crear una base nueva, sin restaurar datos

Abrir SQL Shell o ejecutar:

```powershell
& 'C:/Program Files/PostgreSQL/17/bin/psql.exe' -h 127.0.0.1 -p 5432 -U postgres -d postgres -W
```

Introducir la contraseña local cuando se solicite. En `psql`, ejecutar una sola vez:

```sql
CREATE ROLE unmsm_local LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE;
\password unmsm_local
CREATE DATABASE simulacro_local OWNER unmsm_local;
\q
```

`\password` solicita una contraseña nueva sin escribirla en el comando. Si el rol o la base ya existen, detenerse y comprobar su procedencia; no borrarlos ni restaurar encima. Esta base comienza con cero tablas y cero usuarios de la aplicación.

### 4. Configurar el archivo privado

Solo si no existe [.env](../.env), copiar [.env.example](../.env.example) a ese nombre. No sobrescribir una configuración existente.

```powershell
if (!(Test-Path .env)) { Copy-Item .env.example .env }
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```

Guardar la clave generada como `SECRET_KEY`. Configurar `DATABASE_URL` con este formato, sustituyendo la contraseña por la del rol `unmsm_local`:

```dotenv
DATABASE_URL=postgresql://unmsm_local:CONTRASENA_CODIFICADA@127.0.0.1:5432/simulacro_local
```

Los caracteres especiales de la contraseña deben codificarse para una URL (por ejemplo, `@` como `%40`). No compartir claves ni contraseñas por chat, capturas o GitHub. Las variables `POSTGRES_PASSWORD` y `DOCKER_DATABASE_URL` no se necesitan en esta instalación local.

### 5. Preparar tablas y arrancar para uso local

Comprobar primero que la URL corresponde exclusivamente a la base nueva del proyecto. [crear_bd.py](../crear_bd.py) crea o verifica tablas e índices, además de crear la base si no existe. En el procedimiento anterior la base ya existe y pertenece a un rol sin privilegios administrativos.

El script actual analiza la URL con `urlparse` sin decodificar la contraseña antes de su primera conexión. Si contiene caracteres codificados, ese paso puede fallar: no cambiar la contraseña por este motivo ni ejecutar restauraciones. Se puede preparar el esquema existente usando directamente el DSN que entiende psycopg2:

```powershell
.\.venv\Scripts\python.exe -c "from models.database import init_db, close_pool; init_db(); close_pool()"
.\.venv\Scripts\python.exe app.py
```

Abrir http://localhost:5000 y detener con Ctrl+C. El primer comando y el arranque modifican el esquema; no son comprobaciones de solo lectura. No crean usuarios ni restauran resultados. El servidor de desarrollo no debe exponerse a Internet.

Para pruebas automatizadas, usar otra base exclusiva de pruebas y verificar su identidad antes de importar la aplicación; seguir [AGENTS.md](../AGENTS.md). No ejecutar pruebas de integración sobre esta base local. La aprobación de instalación no autoriza las subfases de seguridad 1A/1B.

### 6. Qué compartir

Compartir código y documentación mediante GitHub. No subir `.env`, `.venv`, respaldos SQL ni datos de PostgreSQL. Comprobar las exclusiones:

```powershell
git check-ignore .env .venv/pyvenv.cfg
git status --short
```

[restaurar_bd.bat](../restaurar_bd.bat) solo se utiliza para trasladar un respaldo autorizado llamado `backup_simulacro.sql`; no instala herramientas y no se necesita para una instalación vacía. El script actual no detiene `psql` ante cada error SQL, por lo que su mensaje de éxito no basta para validar una restauración. No se modificó como parte de esta instalación.

## Referencias y límites

Clonar el repositorio y seguir `README.md` para instalar dependencias, crear `.env` con valores propios y ejecutar la aplicación con PostgreSQL local o Docker.

`SECRET_KEY` y `DATABASE_URL` son obligatorias. Docker exige además `POSTGRES_PASSWORD` y `DOCKER_DATABASE_URL`.

El repositorio contiene código y bancos de preguntas. No contiene usuarios, resultados, plantillas biométricas, `.env` ni backups. Los datos personales requieren un traslado privado autorizado y no deben publicarse en GitHub.

No ejecutar descubrimiento global de pruebas ni importar `app.py` contra la base de desarrollo. Consultar `AGENTS.md` para las pruebas de integración y el aislamiento requerido.
