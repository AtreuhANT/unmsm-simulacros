import time
import json
import logging
import secrets
from flask import Blueprint, render_template, session, redirect, url_for, flash
from config import Config
from models.usuario import obtener_usuario_por_id, obtener_plantilla_facial
from models.intento import (
    crear_intento, obtener_intento_activo, obtener_respuestas_intento, cerrar_intento
)
from utils.helpers import login_required
from utils.preguntas import AREAS_UNMSM, cargar_preguntas_area, sanitizar_preguntas_para_cliente

logger = logging.getLogger(__name__)
simulacro_bp = Blueprint('simulacro', __name__)

@simulacro_bp.route('/simulacro')
@login_required
def simulacro_index():
    """Redirige a la sala de preparación del examen correspondiente al postulante."""
    area_usuario = session.get('area', 'A').upper()
    return redirect(url_for('simulacro.preparacion_examen', area=area_usuario))

@simulacro_bp.route('/preparacion/<area>')
@login_required
def preparacion_examen(area):
    """
    Sala de preparación técnica y verificación de identidad (Fase 5).
    - NO consume tiempo de examen (el cronómetro oficial arranca tras iniciar intento).
    - Permite probar la cámara web, validar identidad 1:1 o enrolar la primera referencia.
    - Si el postulante ya tiene un intento en curso activo, lo redirige directo al examen.
    """
    area = area.upper().strip()
    if area not in AREAS_UNMSM:
        flash(f'El área académica "{area}" no es válida.', 'danger')
        return redirect(url_for('dashboard.dashboard_view'))

    usuario_id = session['usuario_id']
    usuario = obtener_usuario_por_id(usuario_id)
    if not usuario:
        session.clear()
        return redirect(url_for('auth.login'))

    # Si ya tiene un intento en curso no vencido, saltar directo al examen
    intento_activo = obtener_intento_activo(usuario_id)
    if intento_activo and (not Config.DETECCION_CELULAR_ACTIVA or usuario.get('consentimiento_celular_version') == 'celular-v2-fotos'):
        if intento_activo.get('segundos_restantes', 0) > 0:
            return redirect(url_for('simulacro.rendir_examen', area=intento_activo.get('area', area)))
        else:
            cerrar_intento(intento_activo['id'], estado_academico='VENCIDO', estado_supervision='TIEMPO_AGOTADO')

    # Consultar plantilla biométrica de referencia
    session['csrf_preparacion'] = secrets.token_urlsafe(32)
    plantilla = obtener_plantilla_facial(usuario_id)
    descriptores_faciales = []
    enrolado = False

    if plantilla and plantilla.get('descriptores'):
        descriptores_faciales = plantilla['descriptores']
        enrolado = True
    else:
        desc_raw = usuario.get('descriptores_faciales')
        if isinstance(desc_raw, str):
            try:
                descriptores_faciales = json.loads(desc_raw)
            except Exception:
                descriptores_faciales = []
        elif isinstance(desc_raw, list):
            descriptores_faciales = desc_raw
        enrolado = bool(descriptores_faciales and len(descriptores_faciales) > 0)

    return render_template(
        'preparacion.html',
        area=area,
        info_area=AREAS_UNMSM[area],
        enrolado=enrolado,
        descriptores_faciales_json=json.dumps(descriptores_faciales),
        usuario=usuario,
        csrf_preparacion=session['csrf_preparacion'],
        deteccion_celular_activa=Config.DETECCION_CELULAR_ACTIVA
    )

@simulacro_bp.route('/examen/<area>')
@login_required
def rendir_examen(area):
    """
    Carga la interfaz del examen con persistencia continua e inmunidad ante recargas (F5).
    - Si existe un intento 'EN_CURSO', restaura el tiempo restante y las respuestas confirmadas.
    - Si no existe, inicializa un intento oficial en PostgreSQL con vencimiento inmutable.
    - Envía las preguntas estrictamente sanitizadas (sin claves ni explicaciones).
    """
    area = area.upper().strip()
    if area not in AREAS_UNMSM:
        flash(f'El área académica "{area}" no es válida.', 'danger')
        return redirect(url_for('dashboard.dashboard_view'))

    usuario_id = session['usuario_id']
    usuario = obtener_usuario_por_id(usuario_id)
    if not usuario:
        session.clear()
        return redirect(url_for('auth.login'))

    if Config.DETECCION_CELULAR_ACTIVA and usuario.get('consentimiento_celular_version') != 'celular-v2-fotos':
        return redirect(url_for('simulacro.preparacion_examen', area=area))

    # Cargar y sanitizar banco de preguntas (EX-01: sin respuestas correctas en cliente)
    preguntas_completas = cargar_preguntas_area(area)
    if not preguntas_completas:
        flash(f'Aún no hay preguntas disponibles para el Área {area}.', 'warning')
        return redirect(url_for('dashboard.dashboard_view'))

    preguntas_cliente = sanitizar_preguntas_para_cliente(preguntas_completas)

    # 1. Gestión del ciclo de vida del intento (EX-02: Reloj oficial de PostgreSQL)
    intento = obtener_intento_activo(usuario_id)
    
    if intento:
        # Verificar si el intento activo pertenece a otra área
        if intento.get('area') != area:
            logger.info(f"Usuario {usuario_id} tiene intento activo en área {intento.get('area')}, redirigiendo.")
            return redirect(url_for('simulacro.rendir_examen', area=intento.get('area')))

        segundos_restantes = intento.get('segundos_restantes', 0)
        
        # Si ya venció en el servidor, cerrar formalmente
        if segundos_restantes <= 0:
            cerrar_intento(intento['id'], estado_academico='VENCIDO', estado_supervision='TIEMPO_AGOTADO')
            flash('Tu tiempo oficial de examen ha concluido.', 'info')
            return redirect(url_for('dashboard.dashboard_view'))

        intento_id = intento['id']
        token_sesion = intento['token_sesion']
        respuestas_guardadas = obtener_respuestas_intento(intento_id)
        ya_en_curso = True
        logger.info(f"Recuperando intento {intento_id} en curso para usuario {usuario_id}. Segundos restantes: {segundos_restantes}")
    else:
        # Iniciar nuevo intento oficial
        duracion_min = getattr(Config, 'DURACION_EXAMEN_MINUTOS', 60)
        intento = crear_intento(usuario_id=usuario_id, area=area, duracion_minutos=duracion_min)
        intento_id = intento['id']
        token_sesion = intento['token_sesion']
        segundos_restantes = duracion_min * 60
        respuestas_guardadas = {}
        ya_en_curso = False
        logger.info(f"Nuevo intento {intento_id} iniciado para usuario {usuario_id} en área {area}.")

    # Sincronizar en sesión de Flask
    session['token_sesion'] = token_sesion
    session['intento_id'] = intento_id
    session['examen_area'] = area
    session['csrf_examen'] = secrets.token_urlsafe(32)

    # 2. Descriptores faciales para verificación Edge en el navegador
    plantilla = obtener_plantilla_facial(usuario_id)
    descriptores_faciales = []
    if plantilla and plantilla.get('descriptores'):
        descriptores_faciales = plantilla['descriptores']
    else:
        desc_raw = usuario.get('descriptores_faciales')
        if isinstance(desc_raw, str):
            try:
                descriptores_faciales = json.loads(desc_raw)
            except Exception:
                descriptores_faciales = []
        elif isinstance(desc_raw, list):
            descriptores_faciales = desc_raw

    return render_template(
        'examen.html',
        area=area,
        info_area=AREAS_UNMSM[area],
        intento_id=intento_id,
        token_sesion=token_sesion,
        segundos_restantes=segundos_restantes,
        respuestas_guardadas_json=json.dumps(respuestas_guardadas),
        ya_en_curso=ya_en_curso,
        preguntas=preguntas_cliente,
        preguntas_json=json.dumps(preguntas_cliente),
        descriptores_faciales_json=json.dumps(descriptores_faciales),
        usuario=usuario,
        csrf_examen=session['csrf_examen'],
        deteccion_celular_activa=Config.DETECCION_CELULAR_ACTIVA and usuario.get('consentimiento_celular_version') == 'celular-v2-fotos'
    )
