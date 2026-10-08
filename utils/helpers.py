import re
from functools import wraps
from flask import session, redirect, url_for, request, jsonify, flash

def es_dispositivo_movil(user_agent_str):
    """
    Detecta si el agente de usuario corresponde a un dispositivo móvil o tablet.
    La plataforma UNMSM está restringida a PC / Laptop de escritorio para supervisión webcam.
    """
    if not user_agent_str:
        return False
    patron_movil = re.compile(
        r'mobile|android|iphone|ipad|ipod|blackberry|iemobile|kindle|silk|opera mini|windows phone',
        re.IGNORECASE
    )
    return bool(patron_movil.search(user_agent_str))

def login_required(f):
    """Decorador para proteger rutas que exigen autenticación."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Sesión no iniciada o expirada.', 'redirect': url_for('auth.login')}), 401
            flash('Por favor inicia sesión para continuar.', 'warning')
            return redirect(url_for('auth.login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorador para proteger rutas exclusivas de administración."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'No autorizado.'}), 401
            flash('Debes iniciar sesión con una cuenta de administrador.', 'warning')
            return redirect(url_for('auth.login'))
        if not session.get('es_admin', False):
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Acceso denegado: privilegios insuficientes.'}), 403
            flash('No tienes permisos de administrador para acceder a esta sección.', 'danger')
            return redirect(url_for('dashboard.dashboard_view'))
        return f(*args, **kwargs)
    return decorated_function

def formatear_tiempo(segundos):
    """Convierte segundos a formato 'MMm SSs' o 'HHh MMm SSs'."""
    if segundos is None:
        return "0s"
    segundos = int(segundos)
    horas = segundos // 3600
    minutos = (segundos % 3600) // 60
    segs = segundos % 60
    
    if horas > 0:
        return f"{horas}h {minutos}m {segs}s"
    elif minutos > 0:
        return f"{minutos}m {segs}s"
    else:
        return f"{segs}s"
