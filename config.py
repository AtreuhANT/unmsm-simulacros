import os
from datetime import timedelta
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

class Config:
    """Configuración central de la plataforma de simulacros UNMSM."""
    
    # Llave secreta para sesiones seguras y CSRF
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY or not SECRET_KEY.strip():
        raise RuntimeError('Define SECRET_KEY en las variables de entorno o en .env')
    
    # URL de conexión a PostgreSQL
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL or not DATABASE_URL.strip():
        raise RuntimeError('Define DATABASE_URL en las variables de entorno o en .env')
    
    # Pool de conexiones psycopg2 (adecuado para 30+ usuarios concurrentes)
    DB_MIN_CONN = int(os.environ.get('DB_MIN_CONN', 2))
    DB_MAX_CONN = int(os.environ.get('DB_MAX_CONN', 35))
    
    # Configuración de Sesión
    PERMANENT_SESSION_LIFETIME = timedelta(hours=5)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Reglas de Puntuación UNMSM
    PUNTO_CORRECTA = 20.0
    PUNTO_INCORRECTA = -1.125
    PUNTO_BLANCO = 0.0
    
    # Duración oficial de simulacro (en minutos)
    DURACION_EXAMEN_MINUTOS = int(os.environ.get('DURACION_EXAMEN_MINUTOS', 60))

    # Tolerancia máxima para discrepancia temporal de examen (segundos de margen)
    TOLERANCIA_TIEMPO_EXAMEN_SEGUNDOS = 60

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
