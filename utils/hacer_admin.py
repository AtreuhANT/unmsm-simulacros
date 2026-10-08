#!/usr/bin/env python
"""
Script CLI para promover a un usuario existente al rol de Administrador.
Uso: python utils/hacer_admin.py <DNI>
"""
import sys
import os

# Asegurar que el directorio raíz del proyecto esté en el path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.usuario import hacer_admin_por_dni, obtener_usuario_por_dni

def main():
    if len(sys.argv) < 2:
        print("Uso: python utils/hacer_admin.py <DNI>")
        sys.exit(1)
        
    dni = sys.argv[1].strip()
    usuario = obtener_usuario_por_dni(dni)
    
    if not usuario:
        print(f"Error: No se encontró ningún usuario con el DNI: {dni}")
        sys.exit(1)
        
    actualizado = hacer_admin_por_dni(dni, es_admin=True)
    if actualizado:
        print(f"ÉXITO: El usuario {usuario['nombre']} {usuario['apellido']} (DNI: {dni}) ahora es ADMINISTRADOR.")
    else:
        print(f"Error al actualizar el usuario con DNI: {dni}")

if __name__ == '__main__':
    main()
