"""Episodios de ausencia facial y una fotografía cifrada por episodio."""

import base64
import hashlib
import os
from pathlib import Path
from uuid import UUID, uuid4

from cryptography.fernet import Fernet
from psycopg2.extras import RealDictCursor

from config import Config
from models.database import get_db_connection, get_db_cursor
from models.evidencia_celular import _normalizar_jpeg


DIRECTORIO = Path(__file__).resolve().parents[1] / 'instance/evidencias_ausencia'
CONSENTIMIENTO = 'ausencia-v1-foto'
MAX_INTERVALO = 30
MOTIVO_AUSENCIA = 'Ausencia de rostro detectada por la cámara; fotografía y duración estimada para revisión humana.'


def _cifrador():
    clave = hashlib.sha256(b'evidencias-ausencia-v1:' + Config.SECRET_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(clave))


def _respuesta(episodio):
    return dict(episodio_id=str(episodio['episodio_id']),
                segundos_observados=round(episodio['duracion_segundos'], 1),
                estado=episodio['estado'], incompleto=episodio['incompleto'],
                foto_guardada=bool(episodio['archivo']))


def _descripcion(episodio):
    segundos = round(episodio['duracion_segundos'], 1)
    estados = {'ausente':'en curso', 'presente':'rostro detectado nuevamente',
               'interrumpido':'análisis interrumpido', 'fin_examen':'examen finalizado durante el episodio'}
    detalle = ' Medición incompleta; hay un intervalo sin observaciones.' if episodio['incompleto'] else ''
    return f'Sin rostro detectado: {segundos} s de duración estimada; {estados[episodio["estado"]]}.{detalle}'


def registrar_observacion(token, usuario_id, episodio_id, secuencia, estado, datos=None):
    try:
        episodio_id = str(UUID(str(episodio_id)))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError('Episodio inválido') from exc
    if type(secuencia) is not int or not 1 <= secuencia <= 100_000:
        raise ValueError('Secuencia inválida')
    if estado not in ('ausente', 'presente', 'interrumpido'):
        raise ValueError('Observación inválida')
    ruta_creada = None
    try:
        with get_db_connection() as conn, conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT i.id FROM intentos i JOIN usuarios u ON u.id=i.usuario_id "
                        "WHERE i.token_sesion=%s AND i.usuario_id=%s AND i.estado_academico='EN_CURSO' "
                        "AND i.fecha_vencimiento > CURRENT_TIMESTAMP "
                        "AND u.consentimiento_ausencia_version=%s FOR UPDATE OF i",
                        (token, usuario_id, CONSENTIMIENTO))
            intento = cur.fetchone()
            if not intento:
                raise PermissionError('Intento o consentimiento de ausencia no disponibles')
            cur.execute('SELECT * FROM episodios_ausencia WHERE intento_id=%s AND episodio_id=%s',
                        (intento['id'], episodio_id))
            episodio = cur.fetchone()
            if episodio and secuencia <= episodio['secuencia']:
                return _respuesta(episodio)
            if episodio and episodio['cerrado_en']:
                raise ValueError('El episodio ya terminó')
            cur.execute('SELECT clock_timestamp() AS ahora')
            ahora = cur.fetchone()['ahora']
            if not episodio:
                if estado != 'ausente' or secuencia != 1:
                    raise ValueError('El episodio debe comenzar con una observación de ausencia')
                cur.execute('SELECT count(*) AS total FROM episodios_ausencia WHERE intento_id=%s', (intento['id'],))
                if cur.fetchone()['total'] >= 60:
                    raise ValueError('Límite de episodios alcanzado')
                cur.execute("INSERT INTO episodios_ausencia (intento_id,usuario_id,episodio_id,secuencia,estado,inicio_en,ultima_observacion) "
                            "VALUES (%s,%s,%s,%s,'ausente',%s,%s) RETURNING *",
                            (intento['id'],usuario_id,episodio_id,secuencia,ahora,ahora))
                episodio = cur.fetchone()
            else:
                intervalo = max(0, (ahora - episodio['ultima_observacion']).total_seconds())
                interrumpido = estado == 'interrumpido' or intervalo > MAX_INTERVALO
                # No contar un hueco sin cámara/red como ausencia comprobada.
                duracion = episodio['duracion_segundos'] + (0 if interrumpido else intervalo)
                cur.execute('UPDATE episodios_ausencia SET duracion_segundos=%s,secuencia=%s,estado=%s,'
                            'ultima_observacion=%s,cerrado_en=%s,incompleto=%s WHERE id=%s RETURNING *',
                            (duracion,secuencia,estado,ahora,None if estado=='ausente' else ahora,
                             episodio['incompleto'] or interrumpido,episodio['id']))
                episodio = cur.fetchone()
            if datos and not episodio['archivo']:
                jpeg = _normalizar_jpeg(datos)
                archivo = f'{uuid4().hex}.bin'
                DIRECTORIO.mkdir(parents=True, exist_ok=True)
                ruta = DIRECTORIO / archivo
                with os.fdopen(os.open(ruta,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as salida:
                    ruta_creada = ruta
                    salida.write(_cifrador().encrypt(jpeg))
                cur.execute('UPDATE episodios_ausencia SET archivo=%s WHERE id=%s', (archivo,episodio['id']))
                episodio['archivo'] = archivo
            descripcion = _descripcion(episodio)
            cur.execute("INSERT INTO eventos_monitoreo (usuario_id,intento_id,modulo,tipo,descripcion,id_cliente) "
                        "VALUES (%s,%s,'facial_presence','ausencia_rostro',%s,%s) "
                        "ON CONFLICT (intento_id,id_cliente) WHERE id_cliente IS NOT NULL "
                        "DO UPDATE SET descripcion=EXCLUDED.descripcion",
                        (usuario_id,intento['id'],descripcion,'ausencia:'+episodio_id))
            cur.execute("UPDATE intentos SET estado_supervision='PENDIENTE' WHERE id=%s", (intento['id'],))
            return _respuesta(episodio)
    except Exception:
        if ruta_creada:
            ruta_creada.unlink(missing_ok=True)
        raise


def cerrar_episodios(cur, intento_id):
    """Al terminar no inferir nuevos segundos sin observaciones de cámara."""
    cur.execute("UPDATE episodios_ausencia SET cerrado_en=CURRENT_TIMESTAMP,estado='fin_examen',incompleto=TRUE "
                "WHERE intento_id=%s AND cerrado_en IS NULL RETURNING *", (intento_id,))
    for episodio in cur.fetchall():
        cur.execute('UPDATE eventos_monitoreo SET descripcion=%s WHERE intento_id=%s AND id_cliente=%s',
                    (_descripcion(episodio),intento_id,'ausencia:'+str(episodio['episodio_id'])))


def listar_ausencias_resultado(resultado_id):
    with get_db_cursor() as cur:
        cur.execute('SELECT a.id,a.episodio_id,a.inicio_en,a.cerrado_en,a.estado,a.incompleto,'
                    'a.duracion_segundos,(a.archivo IS NOT NULL AND a.expira_en>CURRENT_TIMESTAMP) AS tiene_foto '
                    'FROM episodios_ausencia a JOIN intentos i ON i.id=a.intento_id '
                    'JOIN resultados r ON r.token_sesion=i.token_sesion AND r.usuario_id=i.usuario_id '
                    'WHERE r.id=%s ORDER BY a.inicio_en,a.id', (resultado_id,))
        return cur.fetchall()


def leer_foto_ausencia(evidencia_id):
    with get_db_cursor() as cur:
        cur.execute('SELECT archivo FROM episodios_ausencia WHERE id=%s AND expira_en>CURRENT_TIMESTAMP', (evidencia_id,))
        fila = cur.fetchone()
    if not fila or not fila['archivo']:
        return None
    archivo = fila['archivo']
    if len(archivo) != 36 or not archivo.endswith('.bin'):
        return None
    try:
        UUID(archivo[:-4])
    except ValueError:
        return None
    return _cifrador().decrypt((DIRECTORIO/archivo).read_bytes())
