import uuid
import logging
from datetime import datetime, timedelta, timezone
from models.database import get_db_cursor

logger = logging.getLogger(__name__)

def crear_intento(usuario_id, area, duracion_minutos=60, examen_version_id=None):
    """
    Crea un nuevo intento de examen en PostgreSQL con reloj y vencimiento oficial del servidor.
    Emite un token_sesion UUIDv4 único.
    """
    token_sesion = str(uuid.uuid4())
    fecha_inicio = datetime.now(timezone.utc)
    fecha_vencimiento = fecha_inicio + timedelta(minutes=duracion_minutos)
    
    sql = """
        INSERT INTO intentos (
            usuario_id, area, examen_version_id, token_sesion, 
            fecha_inicio, fecha_vencimiento, estado_academico, estado_supervision
        )
        VALUES (%s, %s, %s, %s, %s, %s, 'EN_CURSO', 'SIN_OBSERVACIONES')
        RETURNING id, usuario_id, area, examen_version_id, token_sesion, 
                  fecha_inicio, fecha_vencimiento, estado_academico, estado_supervision;
    """
    with get_db_cursor(commit=True) as cur:
        cur.execute(sql, (
            usuario_id,
            area.upper().strip(),
            examen_version_id,
            token_sesion,
            fecha_inicio,
            fecha_vencimiento
        ))
        return cur.fetchone()

def obtener_intento_activo(usuario_id):
    """
    Retorna el intento actualmente 'EN_CURSO' y no vencido del usuario, o None.
    Permite recuperar la sesión ante recarga de página (F5) o corte de red.
    """
    sql = """
        SELECT id, usuario_id, area, examen_version_id, token_sesion,
               fecha_inicio, fecha_vencimiento, estado_academico, estado_supervision,
               EXTRACT(EPOCH FROM (fecha_vencimiento - CURRENT_TIMESTAMP))::INTEGER as segundos_restantes
        FROM intentos
        WHERE usuario_id = %s 
          AND estado_academico = 'EN_CURSO'
          AND fecha_vencimiento > CURRENT_TIMESTAMP
        ORDER BY fecha_inicio DESC
        LIMIT 1;
    """
    with get_db_cursor(commit=False) as cur:
        cur.execute(sql, (usuario_id,))
        return cur.fetchone()

def obtener_intento_por_id(intento_id):
    """Retorna un intento por su ID primario."""
    sql = """
        SELECT id, usuario_id, area, examen_version_id, token_sesion,
               fecha_inicio, fecha_vencimiento, fecha_cierre,
               estado_academico, estado_supervision,
               EXTRACT(EPOCH FROM (fecha_vencimiento - CURRENT_TIMESTAMP))::INTEGER as segundos_restantes
        FROM intentos
        WHERE id = %s;
    """
    with get_db_cursor(commit=False) as cur:
        cur.execute(sql, (intento_id,))
        return cur.fetchone()

def obtener_intento_por_token(token_sesion):
    """Retorna un intento por su token_sesion UUID."""
    sql = """
        SELECT id, usuario_id, area, examen_version_id, token_sesion,
               fecha_inicio, fecha_vencimiento, fecha_cierre,
               estado_academico, estado_supervision,
               EXTRACT(EPOCH FROM (fecha_vencimiento - CURRENT_TIMESTAMP))::INTEGER as segundos_restantes
        FROM intentos
        WHERE token_sesion = %s;
    """
    with get_db_cursor(commit=False) as cur:
        cur.execute(sql, (str(token_sesion).strip(),))
        return cur.fetchone()

def guardar_respuesta_incremental(intento_id, pregunta_id, opcion_seleccionada=None, es_blanco=False, marcado_revision=False):
    """
    Persistencia continua e incremental de respuestas.
    Inserta o actualiza la respuesta para la tupla única (intento_id, pregunta_id).
    Incrementa numero_revision para control de concurrencia y orden de recepción.
    """
    opcion = str(opcion_seleccionada).upper().strip() if opcion_seleccionada else None
    if es_blanco:
        opcion = None

    sql = """
        INSERT INTO respuestas_intento (
            intento_id, pregunta_id, opcion_seleccionada, es_blanco, 
            marcado_revision, numero_revision, actualizado_en
        )
        VALUES (%s, %s, %s, %s, %s, 1, CURRENT_TIMESTAMP)
        ON CONFLICT (intento_id, pregunta_id)
        DO UPDATE SET
            opcion_seleccionada = EXCLUDED.opcion_seleccionada,
            es_blanco = EXCLUDED.es_blanco,
            marcado_revision = EXCLUDED.marcado_revision,
            numero_revision = respuestas_intento.numero_revision + 1,
            actualizado_en = CURRENT_TIMESTAMP
        RETURNING id, intento_id, pregunta_id, opcion_seleccionada, es_blanco, marcado_revision, numero_revision, actualizado_en;
    """
    with get_db_cursor(commit=True) as cur:
        cur.execute(
            "SELECT 1 FROM intentos WHERE id = %s AND estado_academico = 'EN_CURSO' "
            "AND fecha_vencimiento > CURRENT_TIMESTAMP FOR UPDATE",
            (intento_id,),
        )
        if cur.fetchone() is None:
            raise ValueError('El intento no está abierto')
        cur.execute(sql, (
            intento_id,
            int(pregunta_id),
            opcion,
            bool(es_blanco),
            bool(marcado_revision)
        ))
        return cur.fetchone()

def obtener_respuestas_intento(intento_id):
    """
    Retorna un diccionario de respuestas confirmadas para el intento:
    { str(pregunta_id): { 'opcion': 'A', 'es_blanco': False, 'marcado_revision': False } }
    """
    sql = """
        SELECT pregunta_id, opcion_seleccionada, es_blanco, marcado_revision, numero_revision, actualizado_en
        FROM respuestas_intento
        WHERE intento_id = %s
        ORDER BY pregunta_id ASC;
    """
    with get_db_cursor(commit=False) as cur:
        cur.execute(sql, (intento_id,))
        rows = cur.fetchall()
        
    respuestas_map = {}
    for r in rows:
        respuestas_map[str(r['pregunta_id'])] = {
            'opcion': r['opcion_seleccionada'],
            'es_blanco': r['es_blanco'],
            'marcado_revision': r['marcado_revision'],
            'numero_revision': r['numero_revision']
        }
    return respuestas_map

def cerrar_intento(intento_id, estado_academico='ENTREGADO', estado_supervision='SIN_OBSERVACIONES'):
    """
    Cierra formalmente un intento en PostgreSQL.
    Solo puede cerrarse una vez (transición atómica).
    """
    sql = """
        UPDATE intentos
        SET estado_academico = %s,
            estado_supervision = %s,
            fecha_cierre = CURRENT_TIMESTAMP
        WHERE id = %s
        RETURNING id, usuario_id, area, token_sesion, fecha_inicio, fecha_cierre, estado_academico, estado_supervision;
    """
    with get_db_cursor(commit=True) as cur:
        cur.execute(sql, (
            estado_academico.strip(),
            estado_supervision.strip() if estado_supervision else 'SIN_OBSERVACIONES',
            intento_id
        ))
        return cur.fetchone()
