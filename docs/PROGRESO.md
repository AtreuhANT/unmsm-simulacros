# Progreso

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
