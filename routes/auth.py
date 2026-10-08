import json
import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models.usuario import (
    crear_usuario, obtener_usuario_por_dni, verificar_credenciales
)
from utils.preguntas import AREAS_UNMSM
from utils.helpers import es_dispositivo_movil

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)

@auth_bp.before_request
def verificar_dispositivo():
    """Bloquea dispositivos móviles y redirige a pantalla de incompatibilidad."""
    user_agent = request.headers.get('User-Agent', '')
    if es_dispositivo_movil(user_agent) and request.endpoint != 'auth.incompatible':
        return redirect(url_for('auth.incompatible'))

@auth_bp.route('/incompatible')
def incompatible():
    """Pantalla informativa cuando se intenta acceder desde móvil o tablet."""
    return render_template('incompatible.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Inicio de sesión con DNI y contraseña (contraseña por defecto = DNI)."""
    if 'usuario_id' in session:
        return redirect(url_for('dashboard.dashboard_view'))

    if request.method == 'POST':
        dni = request.form.get('dni', '').strip()
        password = request.form.get('password', '').strip()

        if not dni or not password:
            flash('Por favor ingresa tu DNI y contraseña.', 'danger')
            return render_template('login.html', dni=dni)

        usuario = verificar_credenciales(dni, password)
        if usuario:
            session.clear()
            session['usuario_id'] = usuario['id']
            session['nombre'] = usuario['nombre']
            session['apellido'] = usuario['apellido']
            session['dni'] = usuario['dni']
            session['area'] = usuario['area']
            session['carrera'] = usuario['carrera']
            session['es_admin'] = usuario['es_admin']
            session.permanent = True

            flash(f'¡Bienvenido(a), {usuario["nombre"]}!', 'success')
            next_url = request.args.get('next')
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect(url_for('dashboard.dashboard_view'))
        else:
            flash('DNI o contraseña incorrectos. Verifica tus datos de acceso.', 'danger')

    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Registro formal de postulantes sin requerimiento invasivo de cámara web.
    La verificación biométrica se realiza exclusivamente antes de iniciar un examen.
    """
    if 'usuario_id' in session:
        return redirect(url_for('dashboard.dashboard_view'))

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        apellido = request.form.get('apellido', '').strip()
        dni = request.form.get('dni', '').strip()
        area = request.form.get('area', '').strip().upper()
        carrera = request.form.get('carrera', '').strip()
        password = request.form.get('password', '').strip()
        password_confirm = request.form.get('password_confirm', '').strip()

        # Validaciones de campos obligatorios
        if not nombre or not apellido or not dni or not area or not carrera:
            flash('Todos los campos académicos y personales son obligatorios.', 'danger')
            return render_template('register.html', areas=AREAS_UNMSM)

        if not dni.isdigit() or len(dni) not in (8, 9, 10, 11, 12):
            flash('El documento de identidad debe contener entre 8 y 12 dígitos numéricos.', 'danger')
            return render_template('register.html', areas=AREAS_UNMSM)

        if area not in AREAS_UNMSM:
            flash('Área académica seleccionada no válida.', 'danger')
            return render_template('register.html', areas=AREAS_UNMSM)

        # Validación de contraseña elegida por el postulante
        if not password or len(password) < 6:
            flash('La contraseña debe tener un mínimo de 6 caracteres.', 'danger')
            return render_template('register.html', areas=AREAS_UNMSM)

        if password != password_confirm:
            flash('Las contraseñas ingresadas no coinciden. Por favor verifícalas.', 'danger')
            return render_template('register.html', areas=AREAS_UNMSM)

        # Validar si ya existe el DNI registrado
        if obtener_usuario_por_dni(dni):
            flash('El DNI ingresado ya se encuentra registrado en el sistema. Puedes iniciar sesión.', 'warning')
            return redirect(url_for('auth.login'))

        try:
            nuevo_usuario = crear_usuario(
                nombre=nombre,
                apellido=apellido,
                dni=dni,
                password=password,
                carrera=carrera,
                area=area,
                descriptores_faciales=None,
                es_admin=False
            )
            flash('¡Cuenta creada con éxito! Ahora puedes iniciar sesión con tu DNI y tu contraseña.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            logger.error(f"Error al registrar usuario en base de datos: {e}")
            flash('Ocurrió un error al registrar tu cuenta. Inténtalo nuevamente.', 'danger')

    return render_template('register.html', areas=AREAS_UNMSM)

@auth_bp.route('/logout')
def logout():
    """Cierra la sesión del usuario."""
    session.clear()
    flash('Has cerrado sesión correctamente.', 'info')
    return redirect(url_for('auth.login'))
