@echo off
chcp 65001 > nul
title UNMSM - Restaurar Base de Datos PostgreSQL

echo ======================================================================
echo           UNMSM Simulacros Pro - Restauración de Base de Datos
echo ======================================================================
echo.

set ARCHIVO_ORIGEN=backup_simulacro.sql

if not exist "%ARCHIVO_ORIGEN%" (
    echo [ERROR] No se encontro el archivo %ARCHIVO_ORIGEN% en este directorio.
    echo Asegurese de haber copiado el archivo backup_simulacro.sql antes de continuar.
    pause
    exit /b 1
)

set /p PG_USER="Ingrese usuario de PostgreSQL [default: postgres]: "
if "%PG_USER%"=="" set PG_USER=postgres

set /p PG_HOST="Ingrese host [default: localhost]: "
if "%PG_HOST%"=="" set PG_HOST=localhost

set /p PG_PORT="Ingrese puerto [default: 5432]: "
if "%PG_PORT%"=="" set PG_PORT=5432

set /p PG_DB="Ingrese nombre de la base de datos destino [default: simulacro_db]: "
if "%PG_DB%"=="" set PG_DB=simulacro_db

echo.
echo [INFO] Creando base de datos si no existe...
psql -U %PG_USER% -h %PG_HOST% -p %PG_PORT% -c "CREATE DATABASE %PG_DB%;" > nul 2>&1

echo [INFO] Restaurando datos desde %ARCHIVO_ORIGEN% en %PG_DB%...
psql -U %PG_USER% -h %PG_HOST% -p %PG_PORT% -d %PG_DB% -f "%ARCHIVO_ORIGEN%"

if %errorlevel% equ 0 (
    echo.
    echo ======================================================================
    echo [EXITO] Base de datos restaurada correctamente.
    echo Ya puede ejecutar iniciar.bat para usar el sistema.
    echo ======================================================================
) else (
    echo.
    echo [ERROR] Ocurrio un problema al restaurar. Verifique sus credenciales de PostgreSQL.
)

pause
