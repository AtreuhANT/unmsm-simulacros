import logging
import secrets
from flask import Blueprint, render_template, session, redirect, url_for, flash, request, abort, Response
from cryptography.fernet import InvalidToken
from models.resultado import (
    obtener_resultado_por_id, obtener_decision_revision, obtener_eventos_resultado,
    obtener_ranking, obtener_estadisticas_generales
)
from models.intento import obtener_intento_por_token, obtener_respuestas_intento
from models.usuario import listar_usuarios
from utils.helpers import login_required, admin_required, formatear_tiempo
from utils.preguntas import AREAS_UNMSM, cargar_preguntas_area
from models.supervision import IntentoNoDisponible, listar_pendientes, resolver_revision
from models.evidencia_celular import listar_evidencias_resultado, leer_evidencia

logger = logging.getLogger(__name__)
resultados_bp = Blueprint('resultados', __name__)

@resultados_bp.route('/resultado/<int:id>')
@login_required
def ver_resultado(id):
    """
    Vista de resultados individuales del simulacro.
    Muestra:
    - Puntaje oficial UNMSM y desglose de aciertos/errores.
    - Revisión detallada de preguntas con retroalimentación académica DECO.
    - Panel cronológico de OBSERVACIONES DE CONDUCTA (auditoría anti-trampa).
    """
    resultado = obtener_resultado_por_id(id)
    if not resultado:
        flash('El resultado solicitado no existe.', 'warning')
        return redirect(url_for('dashboard.dashboard_view'))

    usuario_id = session['usuario_id']
    es_admin = session.get('es_admin', False)

    # Solo el propio alumno o un administrador pueden ver el resultado
    if resultado['usuario_id'] != usuario_id and not es_admin:
        flash('No tienes permiso para ver este resultado.', 'danger')
        return redirect(url_for('dashboard.dashboard_view'))

    eventos = obtener_eventos_resultado(id)
    decision_revision = obtener_decision_revision(id)

    # Conteo y categorización de eventos de telemetría
    conteo_eventos = {
        'total': len(eventos),
        'ausencia': sum(1 for e in eventos if 'ausencia' in e['tipo']),
        'multiple_rostro': sum(1 for e in eventos if 'multiple' in e['tipo']),
        'no_coincide': sum(1 for e in eventos if 'coincide' in e['tipo']),
        'foco': sum(1 for e in eventos if e['tipo'] in ('cambio_pestana', 'desenfoque_ventana', 'salida_pantalla_completa', 'tab_switch', 'window_blur', 'fullscreen_exit')),
        'captura': sum(1 for e in eventos if 'captura' in e['tipo'] or 'screenshot' in e['tipo'] or 'devtools' in e['tipo'])
    }

    # Desglose de preguntas académicas con retroalimentación DECO
    detalles_preguntas = []
    preguntas_area = cargar_preguntas_area(resultado['area'])
    intento = obtener_intento_por_token(resultado['token_sesion'])
    respuestas_map = {}
    if intento:
        respuestas_db = obtener_respuestas_intento(intento['id'])
        for pid_str, r_info in respuestas_db.items():
            if r_info.get('opcion'):
                respuestas_map[int(pid_str)] = r_info['opcion']

    for q in preguntas_area:
        q_id = int(q['id'])
        marcada = respuestas_map.get(q_id, None)
        es_blanco = (marcada is None)
        es_correcta = (marcada == q['correcta']) if not es_blanco else False
        puntos = 20.0 if es_correcta else (-1.125 if not es_blanco else 0.0)

        detalles_preguntas.append({
            'id': q_id,
            'seccion': q.get('seccion', 'General'),
            'enunciado': q.get('enunciado', ''),
            'opciones': q.get('opciones', {}),
            'marcada': marcada,
            'correcta': q.get('correcta'),
            'es_correcta': es_correcta,
            'es_blanco': es_blanco,
            'puntos': puntos,
            'explicacion': q.get('explicacion', '')
        })

    return render_template(
        'resultado.html',
        resultado=resultado,
        decision_revision=decision_revision,
        eventos=eventos,
        conteo=conteo_eventos,
        detalles_preguntas=detalles_preguntas,
        formatear_tiempo=formatear_tiempo,
        areas=AREAS_UNMSM,
        evidencias_celular=listar_evidencias_resultado(id) if es_admin else []
    )


@resultados_bp.route('/admin/evidencia-celular/<int:evidencia_id>')
@admin_required
def ver_evidencia_celular(evidencia_id):
    try:
        foto = leer_evidencia(evidencia_id)
    except (OSError, InvalidToken):
        abort(404)
    if foto is None:
        abort(404)
    respuesta = Response(foto, mimetype='image/jpeg')
    respuesta.headers['Cache-Control'] = 'no-store, private'
    respuesta.headers['X-Content-Type-Options'] = 'nosniff'
    respuesta.headers['Content-Security-Policy'] = "default-src 'none'"
    return respuesta

@resultados_bp.route('/ranking')
@login_required
def ranking_view():
    """
    Ranking oficial UNMSM con ordenamiento y desempate:
    1° Mayor Puntaje
    2° Menor tiempo transcurrido en segundos
    Permite filtrar por Área y Carrera.
    """
    area_filtro = request.args.get('area', '').upper().strip()
    carrera_filtro = request.args.get('carrera', '').strip()

    if area_filtro and area_filtro not in AREAS_UNMSM:
        area_filtro = None

    ranking = obtener_ranking(area=area_filtro, carrera=carrera_filtro, limite=100)

    # Identificar podio (primeros 3 lugares)
    podio = ranking[:3] if len(ranking) >= 3 else ranking

    return render_template(
        'ranking.html',
        ranking=ranking,
        podio=podio,
        area_filtro=area_filtro,
        carrera_filtro=carrera_filtro,
        areas=AREAS_UNMSM,
        formatear_tiempo=formatear_tiempo
    )

@resultados_bp.route('/admin')
@admin_required
def admin_panel():
    """Panel de administración y supervisión global en tiempo real."""
    estadisticas = obtener_estadisticas_generales()
    usuarios = listar_usuarios(limite=50)
    pendientes = listar_pendientes()
    if 'csrf_revision' not in session:
        session['csrf_revision'] = secrets.token_urlsafe(32)

    return render_template(
        'admin.html',
        estadisticas=estadisticas,
        usuarios=usuarios,
        pendientes=pendientes,
        areas=AREAS_UNMSM,
        formatear_tiempo=formatear_tiempo
    )


@resultados_bp.route('/admin/revision/<int:resultado_id>', methods=['POST'])
@admin_required
def revisar_anulacion(resultado_id):
    token = session.get('csrf_revision')
    if not token or not secrets.compare_digest(request.form.get('csrf_revision', ''), token):
        abort(403)
    try:
        resolver_revision(resultado_id, session['usuario_id'],
                         request.form.get('decision'), request.form.get('nota'))
        flash('Revisión registrada.', 'success')
    except (ValueError, IntentoNoDisponible):
        flash('Revisión inválida o ya resuelta.', 'danger')
    return redirect(url_for('resultados.admin_panel'))
