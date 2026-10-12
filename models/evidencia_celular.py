"""Capturas puntuales cifradas para revisión humana de detecciones de celular."""

import base64
import hashlib
import io
import os
from pathlib import Path
from uuid import UUID, uuid4

from cryptography.fernet import Fernet
from PIL import Image, UnidentifiedImageError
from psycopg2.extras import RealDictCursor

from config import Config
from models.database import get_db_connection, get_db_cursor


DIRECTORIO = Path(__file__).resolve().parents[1] / 'instance' / 'evidencias'
MAX_JPEG_BYTES = 80_000
MOMENTOS = {1, 3, 7, 10}


def _cifrador():
    # Dominio separado de la clave de sesión; una rotación de SECRET_KEY exige
    # respaldar/re-cifrar las evidencias antes de efectuarla.
    clave = hashlib.sha256(b'evidencias-celular-v1:' + Config.SECRET_KEY.encode('utf-8')).digest()
    return Fernet(base64.urlsafe_b64encode(clave))


def _normalizar_jpeg(datos):
    if not datos or len(datos) > MAX_JPEG_BYTES:
        raise ValueError('Imagen demasiado grande o vacía')
    try:
        with Image.open(io.BytesIO(datos)) as imagen:
            if imagen.format != 'JPEG' or not (160 <= imagen.width <= 1280 and 120 <= imagen.height <= 1280):
                raise ValueError('Formato o dimensiones de imagen inválidos')
            salida = io.BytesIO()
            imagen.convert('RGB').save(salida, format='JPEG', quality=72, optimize=True)
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError('Imagen JPEG inválida') from exc
    limpio = salida.getvalue()
    if len(limpio) > MAX_JPEG_BYTES:
        raise ValueError('Imagen normalizada demasiado grande')
    return limpio


def guardar_evidencia(token, usuario_id, episodio_id, segundo_objetivo, datos):
    try:
        episodio = UUID(str(episodio_id))
        segundo = int(segundo_objetivo)
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError('Identificador de captura inválido') from exc
    if segundo not in MOMENTOS:
        raise ValueError('Momento de captura inválido')
    jpeg = _normalizar_jpeg(datos)
    archivo = f'{uuid4().hex}.bin'
    ruta = DIRECTORIO / archivo
    creado = False
    try:
        with get_db_connection() as conn, conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT i.id FROM intentos i JOIN usuarios u ON u.id = i.usuario_id "
                        "WHERE i.token_sesion = %s AND i.usuario_id = %s AND i.estado_academico = 'EN_CURSO' "
                        "AND u.consentimiento_celular_version = 'celular-v2-fotos' FOR UPDATE OF i",
                        (token, usuario_id))
            intento = cur.fetchone()
            if not intento:
                raise PermissionError('Intento o consentimiento no disponibles')
            cur.execute("SELECT id FROM evidencias_celular WHERE intento_id = %s "
                        "AND episodio_id = %s AND segundo_objetivo = %s",
                        (intento['id'], str(episodio), segundo))
            existente = cur.fetchone()
            if existente:
                return existente['id']
            cur.execute("SELECT count(*) AS total FROM evidencias_celular WHERE intento_id = %s",
                        (intento['id'],))
            if cur.fetchone()['total'] >= 40:
                raise ValueError('Límite de evidencias alcanzado')
            cur.execute("SELECT min(registrado_en) AS inicio, max(registrado_en) AS ultima "
                        "FROM eventos_monitoreo WHERE intento_id = %s AND tipo = 'celular_detectado' "
                        "AND id_cliente LIKE %s",
                        (intento['id'], str(episodio) + ':%'))
            observacion = cur.fetchone()
            if not observacion['inicio'] or not observacion['ultima']:
                raise ValueError('No existe detección asociada al episodio')
            cur.execute('SELECT CURRENT_TIMESTAMP AS ahora')
            ahora = cur.fetchone()['ahora']
            if (ahora - observacion['ultima']).total_seconds() > 5:
                raise ValueError('La detección del episodio ya no es reciente')
            minimo = {1: 0, 3: 1.5, 7: 5.5, 10: 8.5}[segundo]
            if (observacion['ultima'] - observacion['inicio']).total_seconds() < minimo:
                raise ValueError('El episodio aún no llegó al momento indicado')
            DIRECTORIO.mkdir(parents=True, exist_ok=True)
            with os.fdopen(os.open(ruta, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb') as salida:
                salida.write(_cifrador().encrypt(jpeg))
            creado = True
            cur.execute("INSERT INTO evidencias_celular "
                        "(intento_id,usuario_id,episodio_id,segundo_objetivo,archivo,sha256) "
                        "VALUES (%s,%s,%s,%s,%s,%s) RETURNING id",
                        (intento['id'], usuario_id, str(episodio), segundo, archivo,
                         hashlib.sha256(jpeg).hexdigest()))
            return cur.fetchone()['id']
    except Exception:
        if creado:
            ruta.unlink(missing_ok=True)
        raise


def listar_evidencias_resultado(resultado_id):
    with get_db_cursor() as cur:
        cur.execute("SELECT e.id, e.episodio_id, e.segundo_objetivo, e.creado_en "
                    "FROM evidencias_celular e JOIN intentos i ON i.id = e.intento_id "
                    "JOIN resultados r ON r.token_sesion = i.token_sesion AND r.usuario_id = i.usuario_id "
                    "WHERE r.id = %s AND e.expira_en > CURRENT_TIMESTAMP "
                    "ORDER BY e.creado_en, e.segundo_objetivo", (resultado_id,))
        return cur.fetchall()


def leer_evidencia(evidencia_id):
    with get_db_cursor() as cur:
        cur.execute("SELECT archivo FROM evidencias_celular WHERE id = %s "
                    "AND expira_en > CURRENT_TIMESTAMP", (evidencia_id,))
        fila = cur.fetchone()
    if not fila or not fila['archivo'].endswith('.bin') or len(fila['archivo']) != 36:
        return None
    try:
        UUID(fila['archivo'][:-4])
    except ValueError:
        return None
    return _cifrador().decrypt((DIRECTORIO / fila['archivo']).read_bytes())
