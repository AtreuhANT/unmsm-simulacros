import time
import json
import logging
import secrets
from flask import Blueprint, request, jsonify, session, url_for
from config import Config
from models.resultado import (
    guardar_resultado, obtener_resultado_por_token, 
    registrar_evento, asociar_eventos_a_resultado
)
from models.intento import (
    crear_intento, iniciar_o_recuperar_intento_atomico, obtener_intento_activo, obtener_intento_por_id,
    obtener_intento_por_token, guardar_respuesta_incremental, 
    obtener_respuestas_intento, cerrar_intento
)
from models.usuario import guardar_plantilla_facial, obtener_plantilla_facial
from utils.helpers import login_required
from utils.preguntas import AREAS_UNMSM, cargar_preguntas_area, calcular_puntaje, sanitizar_preguntas_para_cliente
from models.supervision import IntentoNoDisponible, entregar_examen, registrar_salida_foco, registrar_celular, registrar_presencia_no_confirmada
from models.database import get_db_cursor
from models.examen import cargar_preguntas_intento
from models.evidencia_celular import guardar_evidencia
from models.ausencia import registrar_observacion, CONSENTIMIENTO

logger = logging.getLogger(__name__)
api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/intento/consentimiento-ausencia', methods=['POST'])
@login_required
def guardar_consentimiento_ausencia():
    csrf = session.get('csrf_preparacion')
    if not csrf or not secrets.compare_digest(request.headers.get('X-CSRF-Token',''),csrf):
        return jsonify({'error':'CSRF inválido'}),403
    data = request.get_json(silent=True)
    if not isinstance(data,dict) or data.get('acepta') is not True:
        return jsonify({'error':'Consentimiento explícito requerido'}),400
    with get_db_cursor(commit=True) as cur:
        cur.execute('UPDATE usuarios SET consentimiento_ausencia_en=CURRENT_TIMESTAMP,'
                    'consentimiento_ausencia_version=%s WHERE id=%s', (CONSENTIMIENTO,session['usuario_id']))
    return jsonify({'status':'ok'})


@api_bp.route('/intento/ausencia', methods=['POST'])
@login_required
def recibir_observacion_ausencia():
    csrf = session.get('csrf_examen')
    if not csrf or not secrets.compare_digest(request.headers.get('X-CSRF-Token',''),csrf):
        return jsonify({'error':'CSRF inválido'}),403
    if not request.content_length or request.content_length > 100_000:
        return jsonify({'error':'Solicitud demasiado grande o vacía'}),400
    try:
        secuencia = int(request.form.get('secuencia',''))
        foto = request.files.get('foto')
        respuesta = registrar_observacion(request.form.get('token_sesion'),session['usuario_id'],
                    request.form.get('episodio_id'),secuencia,request.form.get('estado'),
                    foto.read(80_001) if foto else None)
        return jsonify(respuesta)
    except PermissionError:
        return jsonify({'error':'Intento o consentimiento no disponibles'}),403
    except ValueError as exc:
        return jsonify({'error':str(exc)}),400
    except Exception as exc:
        logger.error('Error al guardar ausencia: %s',type(exc).__name__)
        return jsonify({'error':'No se pudo guardar la observación'}),500


@api_bp.route('/intento/consentimiento-celular', methods=['POST'])
@login_required
def guardar_consentimiento_celular():
    csrf = session.get('csrf_preparacion')
    if not csrf or not secrets.compare_digest(request.headers.get('X-CSRF-Token', ''), csrf):
        return jsonify({'error': 'CSRF inválido'}), 403
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or data.get('acepta') is not True:
        return jsonify({'error': 'Consentimiento explícito requerido'}), 400
    with get_db_cursor(commit=True) as cur:
        cur.execute("UPDATE usuarios SET consentimiento_celular_en = CURRENT_TIMESTAMP, "
                    "consentimiento_celular_version = 'celular-v2-fotos' WHERE id = %s",
                    (session['usuario_id'],))
    return jsonify({'status': 'ok', 'version': 'celular-v2-fotos'})

@api_bp.route('/carreras/<area>')
def obtener_carreras(area):
    """Devuelve el listado de carreras asociadas a un área académica en formato JSON."""
    area = area.upper().strip()
    if area in AREAS_UNMSM:
        return jsonify({
            'area': area,
            'nombre': AREAS_UNMSM[area]['nombre'],
            'carreras': AREAS_UNMSM[area]['carreras']
        })
    return jsonify({'error': 'Área no encontrada'}), 404

@api_bp.route('/evento-monitoreo', methods=['POST'])
@login_required
def reportar_evento_monitoreo():
    """
    Recibe un evento anti-trampa reportado en tiempo real desde el motor Edge en el navegador.
    Payload: { modulo, tipo, descripcion, segundo_examen, token_sesion }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Payload JSON requerido'}), 400

    usuario_id = session['usuario_id']
    modulo = data.get('modulo', 'desconocido')
    tipo = data.get('tipo', 'alerta')
    descripcion = data.get('descripcion', '')
    segundo_examen = data.get('segundo_examen', 0)

    try:
        evento = registrar_evento(
            usuario_id=usuario_id,
            resultado_id=None,  # Se vinculará al guardar_resultado
            modulo=modulo,
            tipo=tipo,
            descripcion=descripcion,
            segundo_examen=int(segundo_examen)
        )
        return jsonify({'status': 'ok', 'evento_id': evento['id'] if evento else None})
    except Exception as e:
        logger.error(f"Error al registrar evento de monitoreo: {e}")
        return jsonify({'error': 'Error interno al registrar evento'}), 500

@api_bp.route('/guardar-resultado', methods=['POST'])
@login_required
def api_guardar_resultado():
    """Cierra y califica desde el intento, las respuestas y el reloj del servidor."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'Payload JSON inválido'}), 400
    csrf = session.get('csrf_examen')
    if not csrf or not secrets.compare_digest(request.headers.get('X-CSRF-Token', ''), csrf):
        return jsonify({'error': 'CSRF inválido'}), 403
    token_sesion = data.get('token_sesion')
    if not isinstance(token_sesion, str) or not token_sesion or len(token_sesion) > 80:
        return jsonify({'error': 'Token de sesión ausente'}), 400
    try:
        resultado = entregar_examen(token_sesion, session['usuario_id'])
        session.pop('token_sesion', None)
        session.pop('intento_id', None)
        session.pop('examen_inicio', None)
        session.pop('examen_area', None)
        return jsonify({
            'status': 'ok',
            'resultado_id': resultado['id'],
            'motivo': resultado['motivo_anulacion'],
            'redirect': url_for('resultados.ver_resultado', id=resultado['id'])
        })
    except IntentoNoDisponible:
        return jsonify({'error': 'Intento inexistente o ajeno'}), 404
    except Exception as e:
        logger.error('Error al cerrar resultado: %s', type(e).__name__)
        return jsonify({'error': 'Error de base de datos al guardar examen'}), 500


@api_bp.route('/intento/salida-foco', methods=['POST'])
@login_required
def reportar_salida_foco():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'Payload inválido'}), 400
    csrf = session.get('csrf_examen')
    if not csrf or not secrets.compare_digest(request.headers.get('X-CSRF-Token', ''), csrf):
        return jsonify({'error': 'CSRF inválido'}), 403
    token = data.get('token_sesion')
    if not isinstance(token, str) or not token or len(token) > 80:
        return jsonify({'error': 'Token inválido'}), 400
    try:
        estado = registrar_salida_foco(token, session['usuario_id'], data.get('id_cliente'), data.get('tipo'))
        if estado.get('resultado_id'):
            estado['redirect'] = url_for('resultados.ver_resultado', id=estado['resultado_id'])
        return jsonify(estado)
    except ValueError:
        return jsonify({'error': 'Evento inválido'}), 400
    except IntentoNoDisponible:
        return jsonify({'error': 'Intento inexistente o ajeno'}), 404
    except Exception as e:
        logger.error('Error al registrar salida de foco: %s', type(e).__name__)
        return jsonify({'error': 'No se pudo registrar la salida'}), 500


@api_bp.route('/intento/celular', methods=['POST'])
@login_required
def reportar_celular():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'Payload inválido'}), 400
    csrf = session.get('csrf_examen')
    if not csrf or not secrets.compare_digest(request.headers.get('X-CSRF-Token', ''), csrf):
        return jsonify({'error': 'CSRF inválido'}), 403
    token = data.get('token_sesion')
    if not isinstance(token, str) or not token or len(token) > 80:
        return jsonify({'error': 'Token inválido'}), 400
    try:
        return jsonify(registrar_celular(token, session['usuario_id'], data.get('id_cliente')))
    except ValueError:
        return jsonify({'error': 'Evento inválido'}), 400
    except IntentoNoDisponible:
        return jsonify({'error': 'Intento inexistente o ajeno'}), 404
    except Exception as e:
        logger.error('Error al registrar celular: %s', type(e).__name__)
        return jsonify({'error': 'No se pudo registrar el evento'}), 500


@api_bp.route('/intento/presencia-no-confirmada', methods=['POST'])
@login_required
def reportar_presencia_no_confirmada():
    csrf = session.get('csrf_examen')
    if not csrf or not secrets.compare_digest(request.headers.get('X-CSRF-Token', ''), csrf):
        return jsonify({'error': 'CSRF inválido'}), 403
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'Payload inválido'}), 400
    token = data.get('token_sesion')
    if not isinstance(token, str) or not token or len(token) > 80:
        return jsonify({'error': 'Token inválido'}), 400
    try:
        return jsonify(registrar_presencia_no_confirmada(token, session['usuario_id'], data.get('id_cliente')))
    except ValueError:
        return jsonify({'error': 'Evento inválido'}), 400
    except IntentoNoDisponible:
        return jsonify({'error': 'Intento inexistente o ajeno'}), 404
    except Exception as exc:
        logger.error('Error al registrar presencia no confirmada: %s', type(exc).__name__)
        return jsonify({'error': 'No se pudo registrar el evento'}), 500


@api_bp.route('/intento/evidencia-celular', methods=['POST'])
@login_required
def recibir_evidencia_celular():
    csrf = session.get('csrf_examen')
    if not csrf or not secrets.compare_digest(request.headers.get('X-CSRF-Token', ''), csrf):
        return jsonify({'error': 'CSRF inválido'}), 403
    if request.content_length is None or request.content_length > 100_000:
        return jsonify({'error': 'Captura demasiado grande'}), 413
    token = request.form.get('token_sesion')
    if not isinstance(token, str) or not token or len(token) > 80:
        return jsonify({'error': 'Token inválido'}), 400
    foto = request.files.get('foto')
    if not foto or foto.mimetype != 'image/jpeg':
        return jsonify({'error': 'Imagen JPEG requerida'}), 400
    datos = foto.read(80_001)
    try:
        evidencia_id = guardar_evidencia(token, session['usuario_id'],
                                          request.form.get('episodio_id'),
                                          request.form.get('segundo_objetivo'), datos)
        return jsonify({'status': 'guardada', 'evidencia_id': evidencia_id})
    except ValueError:
        return jsonify({'error': 'Captura inválida o fuera de límite'}), 400
    except PermissionError:
        return jsonify({'error': 'Intento o consentimiento no disponibles'}), 403
    except Exception as e:
        logger.error('Error al guardar evidencia: %s', type(e).__name__)
        return jsonify({'error': 'No se pudo guardar la evidencia'}), 500


# =============================================================================
# SERIALIZADORES AUXILIARES PARA JSON
# =============================================================================

def _serializar_intento(intento):
    if not intento:
        return None
    d = dict(intento)
    for k in ('fecha_inicio', 'fecha_vencimiento', 'fecha_cierre', 'creado_en'):
        if k in d and d[k] is not None and hasattr(d[k], 'isoformat'):
            d[k] = d[k].isoformat()
    return d

def _serializar_respuesta(resp):
    if not resp:
        return None
    d = dict(resp)
    if 'actualizado_en' in d and d['actualizado_en'] is not None and hasattr(d['actualizado_en'], 'isoformat'):
        d['actualizado_en'] = d['actualizado_en'].isoformat()
    return d


# =============================================================================
# ENDPOINTS DE INTENTO DE EXAMEN (PERSISTENCIA CONTINUA E IDEMPOTENCIA)
# =============================================================================

@api_bp.route('/intento/iniciar', methods=['POST'])
@login_required
def iniciar_o_recuperar_intento():
    """
    Inicia un nuevo intento de examen o recupera el intento activo existente.
    Garantiza que una recarga (F5) o reconexión no cree intentos duplicados.
    """
    csrf = session.get('csrf_examen')
    if not csrf or not secrets.compare_digest(request.headers.get('X-CSRF-Token', ''), csrf):
        return jsonify({'error': 'CSRF inválido'}), 403
    usuario_id = session['usuario_id']
    area = session.get('examen_area')
    if area not in AREAS_UNMSM:
        return jsonify({'error': 'Abre primero la página del examen'}), 403
    preguntas = cargar_preguntas_area(area)
    if not preguntas:
        return jsonify({'error': 'No hay preguntas disponibles'}), 409
    with get_db_cursor() as cur:
        cur.execute('SELECT 1 FROM usuarios WHERE id=%s AND consentimiento_ausencia_version=%s',
                    (usuario_id,CONSENTIMIENTO))
        if not cur.fetchone():
            return jsonify({'error':'Consentimiento de fotografías de ausencia requerido'}),403
    if Config.DETECCION_CELULAR_ACTIVA:
        with get_db_cursor() as cur:
            cur.execute("SELECT 1 FROM usuarios WHERE id = %s AND consentimiento_celular_version = 'celular-v2-fotos'",
                        (usuario_id,))
            if not cur.fetchone():
                return jsonify({'error': 'Consentimiento requerido'}), 403
    duracion = Config.DURACION_EXAMEN_MINUTOS

    try:
        intento, nuevo = iniciar_o_recuperar_intento_atomico(usuario_id, area, duracion)
        preguntas = cargar_preguntas_intento(intento)
        session['token_sesion'] = intento['token_sesion']
        session['intento_id'] = intento['id']
        return jsonify({
            'status': 'iniciado' if nuevo else 'recuperado',
            'intento': _serializar_intento(intento),
            'respuestas': {} if nuevo else obtener_respuestas_intento(intento['id']),
            'segundos_restantes': intento['segundos_restantes'],
            'preguntas': sanitizar_preguntas_para_cliente(preguntas),
        })
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 409
    except Exception as e:
        logger.error(f"Error al iniciar/recuperar intento para usuario {usuario_id}: {e}")
        return jsonify({'error': 'Error de base de datos al gestionar el intento'}), 500


@api_bp.route('/intento/activo', methods=['GET'])
@login_required
def obtener_estado_intento_activo():
    """Retorna los datos y respuestas del intento actualmente activo del usuario."""
    usuario_id = session['usuario_id']
    try:
        intento = obtener_intento_activo(usuario_id)
        if not intento:
            return jsonify({'activo': False, 'intento': None, 'respuestas': {}})

        respuestas = obtener_respuestas_intento(intento['id'])
        return jsonify({
            'activo': True,
            'intento': _serializar_intento(intento),
            'respuestas': respuestas,
            'segundos_restantes': intento.get('segundos_restantes', 0)
        })
    except Exception as e:
        logger.error(f"Error al consultar intento activo: {e}")
        return jsonify({'error': 'Error interno al consultar intento'}), 500


@api_bp.route('/intento/respuesta', methods=['POST'])
@login_required
def persistir_respuesta_incremental():
    """
    Persiste de forma continua e incremental cada selección del alumno en PostgreSQL.
    Permite marcar alternativa, dejar en blanco o marcar para revisión.
    """
    usuario_id = session['usuario_id']
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Payload JSON requerido'}), 400

    intento_id = data.get('intento_id')
    pregunta_id = data.get('pregunta_id')
    opcion = data.get('opcion_seleccionada')
    es_blanco = bool(data.get('es_blanco', False))
    marcado_revision = bool(data.get('marcado_revision', False))

    if not intento_id or pregunta_id is None:
        return jsonify({'error': 'intento_id y pregunta_id son requeridos'}), 400

    try:
        intento = obtener_intento_por_id(intento_id)
        if not intento:
            return jsonify({'error': 'Intento no encontrado'}), 404

        if intento['usuario_id'] != usuario_id:
            return jsonify({'error': 'No autorizado para modificar este intento'}), 403

        if intento['estado_academico'] != 'EN_CURSO':
            return jsonify({'error': 'El examen ya ha sido cerrado'}), 400

        if intento.get('segundos_restantes', 0) <= 0:
            return jsonify({'error': 'El tiempo oficial del examen ha expirado'}), 400

        fila = guardar_respuesta_incremental(
            intento_id=intento_id,
            pregunta_id=pregunta_id,
            opcion_seleccionada=opcion,
            es_blanco=es_blanco,
            marcado_revision=marcado_revision
        )

        return jsonify({
            'status': 'guardado',
            'respuesta': _serializar_respuesta(fila)
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 409
    except Exception as e:
        logger.error(f"Error al guardar respuesta incremental: {e}")
        return jsonify({'error': 'Error al persistir respuesta'}), 500


# =============================================================================
# ENDPOINTS DE PLANTILLAS BIOMÉTRICAS FACIALES
# =============================================================================

@api_bp.route('/intento/enrolar-facial', methods=['POST'])
@login_required
def enrolar_plantilla_facial():
    """
    Guarda los vectores biométricos capturados durante la fase de preparación de cámara
    como plantilla facial de referencia en 'plantillas_faciales'.
    """
    usuario_id = session['usuario_id']
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Payload JSON requerido'}), 400

    descriptores = data.get('descriptores')
    if not descriptores or not isinstance(descriptores, list) or len(descriptores) < 1:
        return jsonify({'error': 'Se requiere al menos 1 descriptor facial válido'}), 400

    for d in descriptores:
        if not isinstance(d, list) or len(d) != 128:
            return jsonify({'error': 'Formato de vector biométrico inválido (se requieren 128 dimensiones)'}), 400

    try:
        dispositivo = request.headers.get('User-Agent', '')[:250]
        guardar_plantilla_facial(usuario_id=usuario_id, descriptores=descriptores, dispositivo=dispositivo)
        return jsonify({
            'status': 'ok',
            'mensaje': 'Plantilla facial registrada exitosamente.',
            'muestras': len(descriptores)
        })
    except Exception as e:
        logger.error(f"Error al guardar plantilla facial para usuario {usuario_id}: {e}")
        return jsonify({'error': 'Error de base de datos al guardar plantilla facial'}), 500


@api_bp.route('/intento/plantilla-facial', methods=['GET'])
@login_required
def obtener_plantilla_facial_postulante():
    """
    Consulta si el postulante cuenta con plantilla facial enrolada y retorna los descriptores
    de referencia para la verificación 1:1 en el navegador.
    """
    usuario_id = session['usuario_id']
    try:
        plantilla = obtener_plantilla_facial(usuario_id)
        if not plantilla:
            return jsonify({'enrolado': False, 'descriptores': []})

        descriptores = plantilla.get('descriptores', [])
        fecha_captura = plantilla.get('fecha_captura')
        if fecha_captura and hasattr(fecha_captura, 'isoformat'):
            fecha_captura = fecha_captura.isoformat()

        return jsonify({
            'enrolado': True,
            'muestras_count': len(descriptores),
            'descriptores': descriptores,
            'fecha_captura': fecha_captura
        })
    except Exception as e:
        logger.error(f"Error al obtener plantilla facial: {e}")
        return jsonify({'error': 'Error al consultar plantilla facial'}), 500
