import time
import json
import logging
from flask import Blueprint, request, jsonify, session, url_for
from config import Config
from models.resultado import (
    guardar_resultado, obtener_resultado_por_token, 
    registrar_evento, asociar_eventos_a_resultado
)
from models.intento import (
    crear_intento, obtener_intento_activo, obtener_intento_por_id,
    obtener_intento_por_token, guardar_respuesta_incremental, 
    obtener_respuestas_intento, cerrar_intento
)
from models.usuario import guardar_plantilla_facial, obtener_plantilla_facial
from utils.helpers import login_required
from utils.preguntas import AREAS_UNMSM, cargar_preguntas_area, calcular_puntaje

logger = logging.getLogger(__name__)
api_bp = Blueprint('api', __name__, url_prefix='/api')

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
    """
    Recibe las respuestas del examen, ejecuta las validaciones de seguridad temporal
    e idempotencia, computa el puntaje oficial UNMSM y persiste los resultados.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Payload JSON inválido'}), 400

    usuario_id = session['usuario_id']
    token_sesion = data.get('token_sesion', '').strip()
    area = data.get('area', '').upper().strip()
    respuestas = data.get('respuestas', {})
    tiempo_cliente = int(data.get('tiempo_segundos', 0))
    estado = data.get('estado', 'COMPLETADO').strip()
    motivo_anulacion = data.get('motivo_anulacion', None)

    # 1. Validación de Token e Idempotencia (anti-replay)
    if not token_sesion:
        return jsonify({'error': 'Token de sesión ausente'}), 400

    resultado_existente = obtener_resultado_por_token(token_sesion)
    if resultado_existente:
        logger.warning(f"Reenvío detectado para token {token_sesion}. Retornando resultado existente.")
        return jsonify({
            'status': 'duplicado',
            'resultado_id': resultado_existente['id'],
            'redirect': url_for('resultados.ver_resultado', id=resultado_existente['id'])
        })

    token_sesion_activa = session.get('token_sesion')
    if token_sesion_activa and token_sesion_activa != token_sesion:
        logger.warning(f"Discrepancia de token: session={token_sesion_activa}, payload={token_sesion}")

    # 2. Validación y vinculación con el intento oficial en PostgreSQL
    intento = obtener_intento_por_token(token_sesion)
    tiempo_final = tiempo_cliente

    if intento:
        # Recuperar y fusionar respuestas persistidas en la BD con las enviadas en el payload
        respuestas_db = obtener_respuestas_intento(intento['id'])
        for pid_str, r_info in respuestas_db.items():
            if pid_str not in respuestas and r_info.get('opcion'):
                respuestas[pid_str] = r_info['opcion']

        # Cálculo de tiempo en base a la hora oficial de inicio del intento
        if intento.get('fecha_inicio'):
            from datetime import datetime, timezone
            duracion_real = int((datetime.now(timezone.utc) - intento['fecha_inicio']).total_seconds())
            tolerancia = Config.TOLERANCIA_TIEMPO_EXAMEN_SEGUNDOS
            if abs(duracion_real - tiempo_cliente) > tolerancia:
                logger.warning(f"Discrepancia temporal: Servidor={duracion_real}s, Cliente={tiempo_cliente}s")
                tiempo_final = max(0, duracion_real)
            else:
                tiempo_final = max(0, tiempo_cliente)
    else:
        # Fallback al reloj en sesión
        examen_inicio = session.get('examen_inicio')
        if examen_inicio:
            tiempo_servidor = int(time.time() - examen_inicio)
            tolerancia = Config.TOLERANCIA_TIEMPO_EXAMEN_SEGUNDOS
            if abs(tiempo_servidor - tiempo_cliente) > tolerancia:
                tiempo_final = max(0, tiempo_servidor)
            else:
                tiempo_final = max(0, tiempo_cliente)

    # 3. Cargar preguntas y computar calificación oficial UNMSM
    preguntas_area = cargar_preguntas_area(area)
    if not preguntas_area:
        return jsonify({'error': f'No existen preguntas para el área {area}'}), 400

    calc = calcular_puntaje(respuestas, preguntas_area)

    # Si fue ANULADO por falta grave anti-trampa, puntaje es 0.0
    if estado == 'ANULADO':
        puntaje_final = 0.0
        if not motivo_anulacion:
            motivo_anulacion = 'Infracción a las normas de supervisión biométrica.'
    else:
        estado = 'COMPLETADO'
        puntaje_final = calc['puntaje']
        motivo_anulacion = None

    # 4. Cerrar intento oficial y persistir en Base de Datos PostgreSQL
    try:
        if intento:
            estado_acad = 'ENTREGADO' if estado == 'COMPLETADO' else 'ANULADO'
            cerrar_intento(
                intento_id=intento['id'],
                estado_academico=estado_acad,
                estado_supervision=motivo_anulacion or 'SIN_OBSERVACIONES'
            )

        nuevo_resultado = guardar_resultado(
            usuario_id=usuario_id,
            area=area,
            puntaje=puntaje_final,
            correctas=calc['correctas'],
            incorrectas=calc['incorrectas'],
            blanco=calc['blanco'],
            tiempo_segundos=tiempo_final,
            token_sesion=token_sesion,
            estado=estado,
            motivo_anulacion=motivo_anulacion
        )

        if not nuevo_resultado:
            return jsonify({'error': 'No se pudo guardar el resultado'}), 500

        resultado_id = nuevo_resultado['id']

        # 5. Asociar eventos de monitoreo generados durante la prueba
        asociar_eventos_a_resultado(usuario_id, resultado_id)

        # 6. Limpiar variables de sesión del examen
        session.pop('token_sesion', None)
        session.pop('intento_id', None)
        session.pop('examen_inicio', None)
        session.pop('examen_area', None)

        return jsonify({
            'status': 'ok',
            'resultado_id': resultado_id,
            'redirect': url_for('resultados.ver_resultado', id=resultado_id)
        })

    except Exception as e:
        logger.error(f"Error al guardar resultado de examen: {e}")
        return jsonify({'error': 'Error de base de datos al guardar examen'}), 500


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
    usuario_id = session['usuario_id']
    data = request.get_json(silent=True) or {}
    area = data.get('area') or session.get('area') or 'A'
    area = str(area).upper().strip()
    duracion = int(data.get('duracion_minutos') or getattr(Config, 'DURACION_EXAMEN_MINUTOS', 180))

    try:
        intento_activo = obtener_intento_activo(usuario_id)
        if intento_activo:
            respuestas = obtener_respuestas_intento(intento_activo['id'])
            session['token_sesion'] = intento_activo['token_sesion']
            session['intento_id'] = intento_activo['id']
            return jsonify({
                'status': 'recuperado',
                'intento': _serializar_intento(intento_activo),
                'respuestas': respuestas,
                'segundos_restantes': intento_activo.get('segundos_restantes', 0)
            })

        nuevo_intento = crear_intento(usuario_id=usuario_id, area=area, duracion_minutos=duracion)
        session['token_sesion'] = nuevo_intento['token_sesion']
        session['intento_id'] = nuevo_intento['id']

        return jsonify({
            'status': 'iniciado',
            'intento': _serializar_intento(nuevo_intento),
            'respuestas': {},
            'segundos_restantes': duracion * 60
        })
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
