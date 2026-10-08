import logging
from flask import Blueprint, render_template, session, redirect, url_for
from models.usuario import obtener_usuario_por_id
from models.resultado import obtener_resultados_usuario
from models.intento import obtener_intento_activo
from utils.helpers import login_required
from utils.preguntas import AREAS_UNMSM

logger = logging.getLogger(__name__)
dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    """Ruta raíz: redirige a dashboard o login."""
    if 'usuario_id' in session:
        return redirect(url_for('dashboard.dashboard_view'))
    return redirect(url_for('auth.login'))

@dashboard_bp.route('/dashboard')
@login_required
def dashboard_view():
    """Panel principal del postulante: métricas, historial y acceso a simulacros."""
    usuario_id = session['usuario_id']
    usuario = obtener_usuario_por_id(usuario_id)
    if not usuario:
        session.clear()
        return redirect(url_for('auth.login'))

    resultados = obtener_resultados_usuario(usuario_id)
    
    # Calcular estadísticas del postulante
    total_examenes = len(resultados)
    completados = [r for r in resultados if r['estado'] == 'COMPLETADO']
    puntajes = [r['puntaje'] for r in completados]
    
    mejor_puntaje = max(puntajes) if puntajes else 0.0
    promedio_puntaje = round(sum(puntajes) / len(puntajes), 3) if puntajes else 0.0
    total_anulados = len([r for r in resultados if r['estado'] == 'ANULADO'])

    # Consultar si el alumno tiene un examen actualmente en curso
    intento_activo = obtener_intento_activo(usuario_id)
    if intento_activo and intento_activo.get('segundos_restantes', 0) <= 0:
        intento_activo = None

    return render_template(
        'dashboard.html',
        usuario=usuario,
        resultados=resultados,
        total_examenes=total_examenes,
        mejor_puntaje=mejor_puntaje,
        promedio_puntaje=promedio_puntaje,
        total_anulados=total_anulados,
        intento_activo=intento_activo,
        areas=AREAS_UNMSM
    )

@dashboard_bp.route('/test-ia')
def test_ia():
    """Banco de pruebas técnico de IA y compatibilidad aislado (Fase 2)."""
    return redirect(url_for('static', filename='test_ia_sandbox.html'))
