@echo off
chcp 65001 > nul
title UNMSM - Crear e Inicializar Base de Datos PostgreSQL

echo ======================================================================
echo           UNMSM Simulacros Pro - Creación de Base de Datos
echo ======================================================================
echo.

python crear_bd.py

echo.
pause
