import os
import logging
from flask import Flask, render_template, request, redirect, url_for
from config import config
from models.database import init_db, close_pool
from routes import auth_bp, dashboard_bp, simulacro_bp, api_bp, resultados_bp
from utils.preguntas import AREAS_UNMSM
from utils.helpers import es_dispositivo_movil, formatear_tiempo

# Configuración de logging estructurado
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
)
logger = logging.getLogger(__name__)

def create_app(config_name=None):
    """Fábrica de aplicaciones Flask para el sistema de simulacros UNMSM."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config.get(config_name, config['default']))

    # Inicializar base de datos PostgreSQL
    with app.app_context():
        try:
            init_db()
        except Exception as e:
            logger.error(f"Fallo al inicializar base de datos en inicio: {e}")

    # Registrar Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(simulacro_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(resultados_bp)

    # Middleware global para restringir a PC / Laptop de escritorio
    @app.before_request
    def verificar_acceso_escritorio():
        # Permitir recursos estáticos y endpoint incompatible
        if request.endpoint and (request.endpoint.startswith('static') or request.endpoint == 'auth.incompatible'):
            return None
        
        user_agent = request.headers.get('User-Agent', '')
        if es_dispositivo_movil(user_agent):
            return redirect(url_for('auth.incompatible'))

    # Inyección de variables globales en plantillas Jinja2
    @app.context_processor
    def inject_global_template_vars():
        return {
            'AREAS_UNMSM': AREAS_UNMSM,
            'formatear_tiempo': formatear_tiempo,
            'app_name': 'UNMSM Simulacros Pro - Sistema de Admisión'
        }

    # Manejadores de errores personalizados
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('base.html', error_code=404, error_title="Página no encontrada",
                               error_msg="La sección solicitada no existe o fue movida."), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('base.html', error_code=500, error_title="Error Interno del Servidor",
                               error_msg="Ocurrió un error inesperado al procesar la solicitud."), 500

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        pass

    return app

# Instancia ejecutable para Gunicorn y desarrollo local
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
