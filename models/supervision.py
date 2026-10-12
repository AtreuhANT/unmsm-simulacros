"""Cierre y observaciones del examen con transacciones sobre el intento propio."""

from datetime import datetime, timezone

from psycopg2.extras import RealDictCursor

from models.database import get_db_connection
from utils.preguntas import cargar_preguntas_area, calcular_puntaje


MOTIVO_FOCO = 'Tres salidas de la página del examen; anulación provisional pendiente de revisión humana.'
TIPOS_FOCO = {'cambio_pestana', 'desenfoque_ventana', 'salida_pantalla_completa'}
MOTIVO_CELULAR = 'Detecciones de celular registradas; pendiente de revisión humana.'
MOTIVO_PRESENCIA = 'No se confirmó el reto ocular de presencia; pendiente de revisión humana.'


class IntentoNoDisponible(Exception):
    """El intento no existe, no pertenece al usuario o ya no está abierto."""


def _bloquear_intento(cur, token, usuario_id):
    cur.execute(
        "SELECT id, usuario_id, area, token_sesion, estado_academico, fecha_inicio "
        "FROM intentos WHERE token_sesion = %s AND usuario_id = %s FOR UPDATE",
        (token, usuario_id),
    )
    intento = cur.fetchone()
    if not intento:
        raise IntentoNoDisponible()
    return intento


def _calcular_desde_bd(cur, intento):
    preguntas = cargar_preguntas_area(intento['area'])
    if not preguntas:
        raise ValueError('Banco de preguntas no disponible')
    cur.execute(
        'SELECT pregunta_id, opcion_seleccionada FROM respuestas_intento WHERE intento_id = %s',
        (intento['id'],),
    )
    respuestas = {str(fila['pregunta_id']): fila['opcion_seleccionada'] for fila in cur.fetchall()}
    return calcular_puntaje(respuestas, preguntas)


def _cerrar(cur, intento, estado, motivo=None):
    calc = _calcular_desde_bd(cur, intento)
    tiempo = max(0, int((datetime.now(timezone.utc) - intento['fecha_inicio']).total_seconds()))
    cur.execute('SELECT estado_supervision FROM intentos WHERE id = %s', (intento['id'],))
    pendiente = estado == 'ANULADO' or cur.fetchone()['estado_supervision'] == 'PENDIENTE'
    supervision = 'PENDIENTE' if pendiente else 'SIN_OBSERVACIONES'
    if pendiente and not motivo:
        cur.execute("SELECT DISTINCT tipo FROM eventos_monitoreo WHERE intento_id = %s "
                    "AND tipo IN ('celular_detectado', 'presencia_no_confirmada')",
                    (intento['id'],))
        tipos = {fila['tipo'] for fila in cur.fetchall()}
        razones = []
        if 'celular_detectado' in tipos:
            razones.append(MOTIVO_CELULAR)
        if 'presencia_no_confirmada' in tipos:
            razones.append(MOTIVO_PRESENCIA)
        motivo = ' '.join(razones) if razones else 'Observaciones de supervisión pendientes de revisión humana.'
    cur.execute(
        "UPDATE intentos SET estado_academico = %s, estado_supervision = %s, "
        "fecha_cierre = CURRENT_TIMESTAMP WHERE id = %s AND estado_academico = 'EN_CURSO'",
        (estado, supervision, intento['id']),
    )
    if cur.rowcount != 1:
        raise IntentoNoDisponible()
    cur.execute(
        "INSERT INTO resultados (usuario_id, area, puntaje, correctas, incorrectas, blanco, "
        "tiempo_segundos, token_sesion, estado, motivo_anulacion, revision) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
        (
            intento['usuario_id'], intento['area'],
            0.0 if estado == 'ANULADO' else calc['puntaje'],
            calc['correctas'], calc['incorrectas'], calc['blanco'], tiempo,
            intento['token_sesion'], 'COMPLETADO' if estado == 'ENTREGADO' else estado, motivo,
            'PENDIENTE' if pendiente else 'NO_REQUERIDA',
        ),
    )
    resultado_id = cur.fetchone()['id']
    cur.execute(
        'UPDATE eventos_monitoreo SET resultado_id = %s '
        'WHERE intento_id = %s AND resultado_id IS NULL',
        (resultado_id, intento['id']),
    )
    return resultado_id


def entregar_examen(token, usuario_id):
    """Califica respuestas persistidas y cierra una sola vez el intento propio."""
    with get_db_connection() as conn, conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        intento = _bloquear_intento(cur, token, usuario_id)
        if intento['estado_academico'] != 'EN_CURSO':
            cur.execute(
                'SELECT id, estado, motivo_anulacion FROM resultados '
                'WHERE token_sesion = %s AND usuario_id = %s',
                (token, usuario_id),
            )
            resultado = cur.fetchone()
            if not resultado:
                raise IntentoNoDisponible()
            return dict(resultado)
        resultado_id = _cerrar(cur, intento, 'ENTREGADO')
        return {'id': resultado_id, 'estado': 'COMPLETADO', 'motivo_anulacion': None}


def registrar_salida_foco(token, usuario_id, id_cliente, tipo):
    """Cuenta episodios únicos y anula provisionalmente en el tercero."""
    if tipo not in TIPOS_FOCO or not isinstance(id_cliente, str) or len(id_cliente) > 80 or not id_cliente:
        raise ValueError('Evento de foco inválido')
    with get_db_connection() as conn, conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        intento = _bloquear_intento(cur, token, usuario_id)
        if intento['estado_academico'] != 'EN_CURSO':
            cur.execute('SELECT id, motivo_anulacion FROM resultados WHERE token_sesion = %s AND usuario_id = %s',
                        (token, usuario_id))
            resultado = cur.fetchone()
            return {'cerrado': True, 'resultado_id': resultado['id'] if resultado else None,
                    'motivo': resultado['motivo_anulacion'] if resultado else None}
        cur.execute(
            "INSERT INTO eventos_monitoreo (usuario_id, intento_id, modulo, tipo, descripcion, id_cliente) "
            "VALUES (%s,%s,'focus_monitor','salida_foco',%s,%s) "
            "ON CONFLICT (intento_id, id_cliente) WHERE id_cliente IS NOT NULL DO NOTHING RETURNING id",
            (usuario_id, intento['id'], tipo, id_cliente),
        )
        nuevo = cur.fetchone() is not None
        cur.execute("SELECT count(*) AS total FROM eventos_monitoreo WHERE intento_id = %s AND tipo = 'salida_foco'",
                    (intento['id'],))
        total = cur.fetchone()['total']
        if nuevo and total >= 3:
            resultado_id = _cerrar(cur, intento, 'ANULADO', MOTIVO_FOCO)
            return {'cerrado': True, 'resultado_id': resultado_id, 'motivo': MOTIVO_FOCO, 'salidas': total}
        return {'cerrado': False, 'salidas': total}


def registrar_celular(token, usuario_id, id_cliente):
    """Marca revisión tras diez segundos de observaciones recibidas por el servidor."""
    if not isinstance(id_cliente, str) or not id_cliente or len(id_cliente) > 80:
        raise ValueError('Evento de celular inválido')
    with get_db_connection() as conn, conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        intento = _bloquear_intento(cur, token, usuario_id)
        if intento['estado_academico'] != 'EN_CURSO':
            return {'cerrado': True}
        cur.execute("SELECT 1 FROM usuarios WHERE id = %s AND consentimiento_celular_version = 'celular-v2-fotos'",
                    (usuario_id,))
        if not cur.fetchone():
            raise IntentoNoDisponible()
        cur.execute(
            "INSERT INTO eventos_monitoreo (usuario_id,intento_id,modulo,tipo,descripcion,id_cliente) "
            "VALUES (%s,%s,'object_detector','celular_detectado',%s,%s) "
            "ON CONFLICT (intento_id,id_cliente) WHERE id_cliente IS NOT NULL DO NOTHING RETURNING registrado_en",
            (usuario_id, intento['id'], 'Detección de celular en cámara', id_cliente),
        )
        nuevo = cur.fetchone()
        if not nuevo:
            cur.execute('SELECT estado_supervision FROM intentos WHERE id = %s', (intento['id'],))
            return {'revision_pendiente': cur.fetchone()['estado_supervision'] == 'PENDIENTE'}
        cur.execute("SELECT registrado_en FROM eventos_monitoreo WHERE intento_id = %s "
                    "AND tipo = 'celular_detectado' AND registrado_en >= CURRENT_TIMESTAMP - INTERVAL '30 seconds' "
                    'ORDER BY registrado_en DESC LIMIT 20', (intento['id'],))
        tiempos = [fila['registrado_en'] for fila in cur.fetchall()][::-1]
        inicio = tiempos[0]
        for anterior, actual in zip(tiempos, tiempos[1:]):
            if (actual - anterior).total_seconds() > 5:
                inicio = actual
        duracion = (tiempos[-1] - inicio).total_seconds()
        if duracion >= 10:
            cur.execute("UPDATE intentos SET estado_supervision = 'PENDIENTE' "
                        "WHERE id = %s AND estado_supervision = 'SIN_OBSERVACIONES'", (intento['id'],))
        cur.execute('SELECT estado_supervision FROM intentos WHERE id = %s', (intento['id'],))
        return {'revision_pendiente': cur.fetchone()['estado_supervision'] == 'PENDIENTE',
                'duracion_observada': round(duracion, 1)}


def registrar_presencia_no_confirmada(token, usuario_id, id_cliente):
    """Registra un reto no superado como indicio; nunca anula automáticamente."""
    if not isinstance(id_cliente, str) or not id_cliente or len(id_cliente) > 80:
        raise ValueError('Identificador de reto inválido')
    with get_db_connection() as conn, conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        intento = _bloquear_intento(cur, token, usuario_id)
        if intento['estado_academico'] != 'EN_CURSO':
            return {'cerrado': True}
        cur.execute("INSERT INTO eventos_monitoreo (usuario_id,intento_id,modulo,tipo,descripcion,id_cliente) "
                    "VALUES (%s,%s,'facial_presence','presencia_no_confirmada',%s,%s) "
                    "ON CONFLICT (intento_id,id_cliente) WHERE id_cliente IS NOT NULL DO NOTHING",
                    (usuario_id, intento['id'], 'Reto de movimiento ocular no confirmado', id_cliente))
        cur.execute("UPDATE intentos SET estado_supervision = 'PENDIENTE' "
                    "WHERE id = %s AND estado_supervision = 'SIN_OBSERVACIONES'", (intento['id'],))
        return {'revision_pendiente': True}


def listar_pendientes():
    with get_db_connection() as conn, conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "SELECT r.id, r.motivo_anulacion, r.terminado_en, u.nombre, u.apellido "
            "FROM resultados r JOIN usuarios u ON u.id = r.usuario_id "
            "WHERE r.revision = 'PENDIENTE' ORDER BY r.terminado_en ASC LIMIT 100"
        )
        return cur.fetchall()


def resolver_revision(resultado_id, admin_id, decision, nota):
    if decision not in {'confirmar', 'reponer'} or not isinstance(nota, str) or not nota.strip() or len(nota) > 1000:
        raise ValueError('Decisión o nota inválida')
    with get_db_connection() as conn, conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute('SELECT * FROM resultados WHERE id = %s FOR UPDATE', (resultado_id,))
        resultado = cur.fetchone()
        if not resultado or resultado['revision'] != 'PENDIENTE':
            raise IntentoNoDisponible()
        if decision == 'reponer':
            cur.execute('SELECT id, usuario_id, area, token_sesion, fecha_inicio FROM intentos '
                        'WHERE token_sesion = %s AND usuario_id = %s FOR UPDATE',
                        (resultado['token_sesion'], resultado['usuario_id']))
            intento = cur.fetchone()
            if not intento:
                raise IntentoNoDisponible()
            calc = _calcular_desde_bd(cur, intento)
            cur.execute("UPDATE resultados SET estado = 'COMPLETADO', revision = 'REPUESTO', "
                        'puntaje = %s WHERE id = %s', (calc['puntaje'], resultado_id))
            cur.execute("UPDATE intentos SET estado_academico = 'ENTREGADO', "
                        "estado_supervision = 'REPUESTO' WHERE id = %s", (intento['id'],))
        else:
            cur.execute("UPDATE resultados SET estado = 'ANULADO', puntaje = 0, "
                        "revision = 'ANULACION_CONFIRMADA' WHERE id = %s", (resultado_id,))
            cur.execute("UPDATE intentos SET estado_academico = 'ANULADO', "
                        "estado_supervision = 'ANULACION_CONFIRMADA' "
                        'WHERE token_sesion = %s AND usuario_id = %s',
                        (resultado['token_sesion'], resultado['usuario_id']))
        cur.execute('INSERT INTO auditoria_revision (resultado_id, admin_id, decision, nota) '
                    'VALUES (%s,%s,%s,%s)', (resultado_id, admin_id, decision, nota.strip()))
