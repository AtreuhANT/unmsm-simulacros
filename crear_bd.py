import os
import sys
from urllib.parse import urlparse
from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Cargar variables de entorno desde .env
base_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(base_dir, ".env")
load_dotenv(dotenv_path=dotenv_path)

db_url = os.environ.get('DATABASE_URL')
if not db_url:
    print("[ERROR] DATABASE_URL no está configurada en .env")
    sys.exit(1)

parsed = urlparse(db_url)
db_name = parsed.path.lstrip('/') or 'simulacro_db'
user = parsed.username or 'postgres'
password = parsed.password
host = parsed.hostname or 'localhost'
port = parsed.port or 5432

print(f"[1/4] Conectando a PostgreSQL en {host}:{port} con usuario '{user}'...")
try:
    conn = psycopg2.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        dbname='postgres'
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (db_name,))
    exists = cur.fetchone()
    if not exists:
        print(f"[2/4] Creando base de datos '{db_name}'...")
        cur.execute(f'CREATE DATABASE "{db_name}";')
        print(f"      [OK] Base de datos '{db_name}' creada.")
    else:
        print(f"[2/4] La base de datos '{db_name}' ya existe.")
    
    cur.close()
    conn.close()
except Exception as e:
    print(f"[ERROR] No se pudo conectar al servidor de PostgreSQL o crear la base de datos: {e}")
    sys.exit(1)

# Inicializar esquema
sys.path.insert(0, base_dir)
from models.database import init_db, get_db_cursor

print(f"[3/4] Inicializando tablas e índices en '{db_name}'...")
try:
    init_db()
    print("      [OK] Tablas e índices creados/verificados correctamente.")
except Exception as e:
    print(f"[ERROR] Falló la inicialización del esquema: {e}")
    sys.exit(1)

# Comprobación final
print("[4/4] Verificando tablas:")
with get_db_cursor() as cur:
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)
    tables = cur.fetchall()
    for t in tables:
        print(f"      - {t['table_name']}")

print("\n[ÉXITO] La base de datos está lista para ejecutarse con iniciar.bat")
