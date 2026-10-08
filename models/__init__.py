from models.database import init_db, get_db_connection, get_db_cursor
from models.usuario import (
    crear_usuario, obtener_usuario_por_dni, obtener_usuario_por_id,
    verificar_credenciales, actualizar_descriptores, hacer_admin_por_dni, listar_usuarios
)
from models.resultado import (
    guardar_resultado, obtener_resultado_por_id, obtener_resultado_por_token,
    obtener_resultados_usuario, registrar_evento, asociar_eventos_a_resultado,
    obtener_eventos_resultado, obtener_ranking, obtener_estadisticas_generales
)

__all__ = [
    'init_db', 'get_db_connection', 'get_db_cursor',
    'crear_usuario', 'obtener_usuario_por_dni', 'obtener_usuario_por_id',
    'verificar_credenciales', 'actualizar_descriptores', 'hacer_admin_por_dni', 'listar_usuarios',
    'guardar_resultado', 'obtener_resultado_por_id', 'obtener_resultado_por_token',
    'obtener_resultados_usuario', 'registrar_evento', 'asociar_eventos_a_resultado',
    'obtener_eventos_resultado', 'obtener_ranking', 'obtener_estadisticas_generales'
]
