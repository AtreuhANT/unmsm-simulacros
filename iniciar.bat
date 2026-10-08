@echo off
chcp 65001 > nul
title UNMSM Simulacros Pro - Lanzador Automático

echo ======================================================================
echo           UNMSM Simulacros Pro - Sistema de Admisión
echo ======================================================================
echo.

:: 1. Verificar si Python está instalado
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] No se encontró Python en el sistema.
    echo Por favor instale Python 3.10 o superior desde https://www.python.org/
    echo y asegúrese de marcar la casilla "Add Python to PATH".
    pause
    exit /b 1
)

:: 2. Crear entorno virtual si no existe
if not exist ".venv" (
    echo [INFO] Creando entorno virtual Python (.venv)...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
    set INSTALAR_DEPS=1
)

:: 3. Activar entorno virtual
call .venv\Scripts\activate.bat

:: 4. Instalar o actualizar dependencias si es la primera vez
if "%INSTALAR_DEPS%"=="1" (
    echo [INFO] Instalando dependencias necesarias (Flask, psycopg2, etc.)...
    pip install --upgrade pip > nul 2>&1
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Falló la instalación de paquetes.
        pause
        exit /b 1
    )
    echo [OK] Dependencias instaladas correctamente.
)

:: 5. Verificar archivo .env
if not exist ".env" (
    if exist ".env.example" (
        echo [INFO] Generando archivo .env a partir de .env.example...
        copy .env.example .env > nul
        echo [ADVERTENCIA] Se ha creado un archivo .env predeterminado.
        echo Asegúrese de que las credenciales de PostgreSQL en .env coincidan con su servidor local.
    )
)

:: 6. Abrir navegador e iniciar servidor
echo.
echo [INFO] Iniciando servidor en http://localhost:5000 ...
echo [INFO] Presione Ctrl + C para detener el servidor en cualquier momento.
echo.

start "" http://localhost:5000
python app.py

pause
