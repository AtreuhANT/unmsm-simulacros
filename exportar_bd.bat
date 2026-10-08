@echo off
chcp 65001 > nul
title UNMSM - Exportar Base de Datos PostgreSQL

echo ======================================================================
echo           UNMSM Simulacros Pro - Respaldo de Base de Datos
echo ======================================================================
echo.

set /p PG_USER="Ingrese usuario de PostgreSQL [default: postgres]: "
if "%PG_USER%"=="" set PG_USER=postgres

set /p PG_HOST="Ingrese host [default: localhost]: "
if "%PG_HOST%"=="" set PG_HOST=localhost

set /p PG_PORT="Ingrese puerto [default: 5432]: "
if "%PG_PORT%"=="" set PG_PORT=5432

set /p PG_DB="Ingrese nombre de la base de datos [default: simulacro_db]: "
if "%PG_DB%"=="" set PG_DB=simulacro_db

set ARCHIVO_SALIDA=backup_simulacro.sql

echo.
echo [INFO] Exportando base de datos a %ARCHIVO_SALIDA%...
pg_dump -U %PG_USER% -h %PG_HOST% -p %PG_PORT% -F p -b -v -f "%ARCHIVO_SALIDA%" %PG_DB%

if %errorlevel% equ 0 (
    echo.
    echo ======================================================================
    echo [EXITO] Respaldo guardado correctamente en: %ARCHIVO_SALIDA%
    echo Copie este archivo a la otra PC para restaurar sus datos.
    echo ======================================================================
) else (
    echo.
    echo [ERROR] No se pudo exportar la base de datos. Verifique que PostgreSQL este ejecutandose
    echo y que la utilidad pg_dump este en el PATH de Windows.
)

pause
