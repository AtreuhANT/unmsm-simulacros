import os
import logging
from contextlib import contextmanager
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from config import Config

logger = logging.getLogger(__name__)

# Pool de conexiones multihilo global
_connection_pool = None

def get_connection_pool():
    """Obtiene o inicializa el pool de conexiones psycopg2 ThreadedConnectionPool."""
    global _connection_pool
    if _connection_pool is None:
        try:
            logger.info("Inicializando ThreadedConnectionPool de PostgreSQL...")
            _connection_pool = pool.ThreadedConnectionPool(
                minconn=Config.DB_MIN_CONN,
                maxconn=Config.DB_MAX_CONN,
                dsn=Config.DATABASE_URL
            )
            logger.info("Pool de conexiones PostgreSQL inicializado correctamente.")
        except Exception as e:
            logger.error(f"Error fatal al inicializar el pool de conexiones: {e}")
            raise
    return _connection_pool

def close_pool():
    """Cierra todas las conexiones del pool de manera segura."""
    global _connection_pool
    if _connection_pool is not None:
        _connection_pool.closeall()
        _connection_pool = None
        logger.info("Pool de conexiones PostgreSQL cerrado.")

@contextmanager
def get_db_connection():
    """Context manager para obtener y liberar conexiones del pool."""
    pool_instance = get_connection_pool()
    conn = pool_instance.getconn()
    try:
        yield conn
    finally:
        pool_instance.putconn(conn)

@contextmanager
def get_db_cursor(commit=False):
    """
    Context manager que entrega un cursor tipo RealDictCursor.
    Si commit=True, hace commit al terminar el bloque; en caso de excepción hace rollback.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            yield cursor
            if commit:
                conn.commit()
            else:
                conn.rollback()
        except Exception as e:
            conn.rollback()
            logger.error(f"Error en transacción SQL: {e}")
            raise
        finally:
            cursor.close()

def init_db():
    """
    Crea las tablas e índices obligatorios en PostgreSQL si no existen:
    - usuarios (con password seguro y rol)
    - plantillas_faciales (desacoplada de usuarios para enrolamiento en sala pre-examen)
    - examenes_versiones (snapshots inmutables de bancos de preguntas)
    - intentos (sesiones activas con reloj y vencimiento oficial en PostgreSQL)
    - respuestas_intento (guardado continuo e incremental de cada respuesta)
    - resultados (calificación oficial UNMSM e informes finales)
    - eventos_monitoreo (telemetría anti-trampa deduplicada)
    """
    ddl_statements = [
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id                    SERIAL PRIMARY KEY,
            nombre                TEXT NOT NULL,
            apellido              TEXT NOT NULL,
            dni                   VARCHAR(15) NOT NULL UNIQUE,
            password_hash         TEXT NOT NULL,
            carrera               TEXT NOT NULL DEFAULT '',
            area                  CHAR(1) NOT NULL DEFAULT 'A',
            descriptores_faciales JSONB DEFAULT '[]'::jsonb,
            es_admin              BOOLEAN NOT NULL DEFAULT FALSE,
            creado_en             TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS plantillas_faciales (
            id                    SERIAL PRIMARY KEY,
            usuario_id           INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            modelo_version       VARCHAR(50) NOT NULL DEFAULT 'face-api-0.22',
            dimension             INTEGER NOT NULL DEFAULT 128,
            descriptores          JSONB NOT NULL,
            estado_acreditacion   VARCHAR(30) NOT NULL DEFAULT 'AUTO_ENROLADO',
            creado_en             TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS examenes_versiones (
            id               SERIAL PRIMARY KEY,
            area             CHAR(1) NOT NULL,
            titulo           TEXT NOT NULL,
            version          INTEGER NOT NULL DEFAULT 1,
            duracion_minutos INTEGER NOT NULL DEFAULT 180,
            preguntas_json   JSONB NOT NULL,
            activo           BOOLEAN NOT NULL DEFAULT TRUE,
            creado_en        TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS intentos (
            id                  SERIAL PRIMARY KEY,
            usuario_id          INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            area                CHAR(1) NOT NULL,
            examen_version_id   INTEGER REFERENCES examenes_versiones(id),
            token_sesion        TEXT NOT NULL UNIQUE,
            fecha_inicio        TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            fecha_vencimiento   TIMESTAMPTZ NOT NULL,
            fecha_cierre        TIMESTAMPTZ,
            estado_academico    VARCHAR(20) NOT NULL DEFAULT 'EN_CURSO',   -- 'EN_CURSO', 'ENTREGADO', 'VENCIDO', 'ABANDONADO'
            estado_supervision  VARCHAR(25) NOT NULL DEFAULT 'SIN_OBSERVACIONES' -- 'SIN_OBSERVACIONES', 'PENDIENTE', 'VALIDADO', 'ANULADO'
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS respuestas_intento (
            id                  SERIAL PRIMARY KEY,
            intento_id          INTEGER NOT NULL REFERENCES intentos(id) ON DELETE CASCADE,
            pregunta_id         INTEGER NOT NULL,
            opcion_seleccionada CHAR(1),
            es_blanco           BOOLEAN NOT NULL DEFAULT FALSE,
            marcado_revision    BOOLEAN NOT NULL DEFAULT FALSE,
            numero_revision     INTEGER NOT NULL DEFAULT 1,
            actualizado_en      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT uq_intento_pregunta UNIQUE (intento_id, pregunta_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS resultados (
            id               SERIAL PRIMARY KEY,
            usuario_id       INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            area             CHAR(1) NOT NULL,
            puntaje          REAL NOT NULL DEFAULT 0.0,
            correctas        INTEGER NOT NULL DEFAULT 0,
            incorrectas      INTEGER NOT NULL DEFAULT 0,
            blanco           INTEGER NOT NULL DEFAULT 0,
            tiempo_segundos  INTEGER NOT NULL DEFAULT 0,
            token_sesion     TEXT NOT NULL UNIQUE,
            estado           TEXT NOT NULL DEFAULT 'COMPLETADO',
            motivo_anulacion TEXT,
            terminado_en     TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS eventos_monitoreo (
            id             SERIAL PRIMARY KEY,
            usuario_id     INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            resultado_id   INTEGER REFERENCES resultados(id) ON DELETE CASCADE,
            modulo         VARCHAR(50) NOT NULL,
            tipo           VARCHAR(50) NOT NULL,
            descripcion    TEXT,
            segundo_examen INTEGER,
            registrado_en  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_resultados_area_ranking 
        ON resultados(area, puntaje DESC, tiempo_segundos ASC);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_intentos_usuario 
        ON intentos(usuario_id, estado_academico);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_respuestas_intento 
        ON respuestas_intento(intento_id);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_eventos_resultado 
        ON eventos_monitoreo(resultado_id);
        """,
        # Migraciones automáticas idempotentes
        "ALTER TABLE usuarios ALTER COLUMN descriptores_faciales DROP NOT NULL;",
        "ALTER TABLE usuarios ALTER COLUMN descriptores_faciales SET DEFAULT '[]'::jsonb;",
        "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS carrera TEXT NOT NULL DEFAULT '';",
        "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS area CHAR(1) NOT NULL DEFAULT 'A';",
        "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS consentimiento_celular_en TIMESTAMPTZ;",
        "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS consentimiento_celular_version TEXT;",
        "ALTER TABLE resultados ADD COLUMN IF NOT EXISTS estado TEXT NOT NULL DEFAULT 'COMPLETADO';",
        "ALTER TABLE resultados ADD COLUMN IF NOT EXISTS motivo_anulacion TEXT;",
        "ALTER TABLE eventos_monitoreo ADD COLUMN IF NOT EXISTS intento_id INTEGER REFERENCES intentos(id) ON DELETE CASCADE;",
        "ALTER TABLE eventos_monitoreo ADD COLUMN IF NOT EXISTS id_cliente TEXT;",
        "ALTER TABLE resultados ADD COLUMN IF NOT EXISTS revision TEXT NOT NULL DEFAULT 'NO_REQUERIDA';",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_evento_intento_cliente ON eventos_monitoreo(intento_id, id_cliente) WHERE id_cliente IS NOT NULL;",
        """CREATE TABLE IF NOT EXISTS auditoria_revision (
            id BIGSERIAL PRIMARY KEY,
            resultado_id INTEGER NOT NULL REFERENCES resultados(id),
            admin_id INTEGER NOT NULL REFERENCES usuarios(id),
            decision TEXT NOT NULL,
            nota TEXT NOT NULL,
            creado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        );""",
        """CREATE TABLE IF NOT EXISTS evidencias_celular (
            id BIGSERIAL PRIMARY KEY,
            intento_id INTEGER NOT NULL REFERENCES intentos(id) ON DELETE CASCADE,
            usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            episodio_id UUID NOT NULL,
            segundo_objetivo SMALLINT NOT NULL CHECK (segundo_objetivo IN (1, 3, 7, 10)),
            archivo TEXT NOT NULL UNIQUE,
            sha256 TEXT NOT NULL,
            creado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            expira_en TIMESTAMPTZ NOT NULL DEFAULT (CURRENT_TIMESTAMP + INTERVAL '30 days'),
            UNIQUE (intento_id, episodio_id, segundo_objetivo)
        );""",
        "CREATE INDEX IF NOT EXISTS idx_evidencias_celular_intento ON evidencias_celular(intento_id, creado_en);"
    ]
    
    with get_db_cursor(commit=True) as cur:
        for statement in ddl_statements:
            cur.execute(statement)
    logger.info("Esquema de base de datos verificado e inicializado correctamente.")

