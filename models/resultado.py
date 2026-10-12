from models.database import get_db_cursor

def guardar_resultado(usuario_id, area, puntaje, correctas, incorrectas, blanco, 
                      tiempo_segundos, token_sesion, estado='COMPLETADO', motivo_anulacion=None):
    """
    Inserta el resultado del simulacro. 
    Usa token_sesion (UUIDv4) para garantizar idempotencia e impedir reenvíos duplicados.
    """
    sql = """
        INSERT INTO resultados (
            usuario_id, area, puntaje, correctas, incorrectas, blanco, 
            tiempo_segundos, token_sesion, estado, motivo_anulacion
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (token_sesion) DO NOTHING
        RETURNING id, usuario_id, area, puntaje, correctas, incorrectas, blanco, 
                  tiempo_segundos, token_sesion, estado, motivo_anulacion, terminado_en;
    """
    with get_db_cursor(commit=True) as cur:
        cur.execute(sql, (
            usuario_id,
            area.upper().strip(),
            float(puntaje),
            int(correctas),
            int(incorrectas),
            int(blanco),
            int(tiempo_segundos),
            str(token_sesion).strip(),
            estado.strip(),
            motivo_anulacion
        ))
        row = cur.fetchone()
        if not row:
            # Si hubo conflicto, retornar el registro existente
            cur.execute("SELECT * FROM resultados WHERE token_sesion = %s;", (str(token_sesion).strip(),))
            row = cur.fetchone()
        return row

def obtener_resultado_por_id(resultado_id):
    """Obtiene el resultado completo con datos del postulante."""
    sql = """
        SELECT r.*, u.nombre, u.apellido, u.dni, u.carrera
        FROM resultados r
        JOIN usuarios u ON r.usuario_id = u.id
        WHERE r.id = %s;
    """
    with get_db_cursor(commit=False) as cur:
        cur.execute(sql, (resultado_id,))
        return cur.fetchone()


def obtener_decision_revision(resultado_id):
    """Devuelve la decisión final y su justificación, sin datos del administrador."""
    with get_db_cursor(commit=False) as cur:
        cur.execute(
            "SELECT a.decision, a.nota FROM auditoria_revision a "
            "JOIN resultados r ON r.id = a.resultado_id "
            "WHERE a.resultado_id = %s AND r.revision IN ('REPUESTO', 'ANULACION_CONFIRMADA') "
            "ORDER BY a.id DESC LIMIT 1",
            (resultado_id,),
        )
        return cur.fetchone()

def obtener_resultado_por_token(token_sesion):
    """Verifica si ya existe un resultado con el token_sesion UUIDv4."""
    sql = """
        SELECT * FROM resultados WHERE token_sesion = %s;
    """
    with get_db_cursor(commit=False) as cur:
        cur.execute(sql, (str(token_sesion).strip(),))
        return cur.fetchone()

def obtener_resultados_usuario(usuario_id):
    """Retorna el historial cronológico de simulacros rendidos por un usuario."""
    sql = """
        SELECT id, area, puntaje, correctas, incorrectas, blanco, 
               tiempo_segundos, token_sesion, estado, motivo_anulacion, terminado_en
        FROM resultados
        WHERE usuario_id = %s
        ORDER BY terminado_en DESC;
    """
    with get_db_cursor(commit=False) as cur:
        cur.execute(sql, (usuario_id,))
        return cur.fetchall()

def registrar_evento(usuario_id, resultado_id, modulo, tipo, descripcion, segundo_examen):
    """
    Registra un evento de supervisión anti-trampa.
    resultado_id puede ser NULL si el examen aún no ha finalizado o vinculable al crearse.
    """
    sql = """
        INSERT INTO eventos_monitoreo (usuario_id, resultado_id, modulo, tipo, descripcion, segundo_examen)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id, registrado_en;
    """
    with get_db_cursor(commit=True) as cur:
        cur.execute(sql, (
            usuario_id,
            resultado_id,
            str(modulo)[:50],
            str(tipo)[:50],
            descripcion,
            segundo_examen
        ))
        return cur.fetchone()

def asociar_eventos_a_resultado(usuario_id, resultado_id):
    """Asocia los eventos huérfanos generados durante la sesión al resultado final."""
    sql = """
        UPDATE eventos_monitoreo
        SET resultado_id = %s
        WHERE usuario_id = %s AND resultado_id IS NULL;
    """
    with get_db_cursor(commit=True) as cur:
        cur.execute(sql, (resultado_id, usuario_id))

def obtener_eventos_resultado(resultado_id):
    """Obtiene todos los incidentes registrados durante el examen."""
    sql = """
        SELECT id, modulo, tipo, descripcion, segundo_examen, registrado_en
        FROM eventos_monitoreo
        WHERE resultado_id = %s
        ORDER BY segundo_examen ASC, registrado_en ASC;
    """
    with get_db_cursor(commit=False) as cur:
        cur.execute(sql, (resultado_id,))
        return cur.fetchall()

def obtener_ranking(area=None, carrera=None, limite=100):
    """
    Genera el ranking oficial UNMSM:
    1° Mayor puntaje
    2° Menor tiempo transcurrido en segundos
    Filtra exámenes válidos ('COMPLETADO').
    """
    clauses = ["r.estado = 'COMPLETADO'", "r.revision <> 'PENDIENTE'"]
    params = []
    
    if area:
        clauses.append("r.area = %s")
        params.append(area.upper().strip())
        
    if carrera:
        clauses.append("u.carrera = %s")
        params.append(carrera.strip())
        
    where_sql = " AND ".join(clauses)
    sql = f"""
        SELECT r.id, r.puntaje, r.correctas, r.incorrectas, r.blanco, r.tiempo_segundos,
               r.area, r.terminado_en,
               u.nombre, u.apellido, u.dni, u.carrera
        FROM resultados r
        JOIN usuarios u ON r.usuario_id = u.id
        WHERE {where_sql}
        ORDER BY r.puntaje DESC, r.tiempo_segundos ASC, r.terminado_en ASC
        LIMIT %s;
    """
    params.append(limite)
    
    with get_db_cursor(commit=False) as cur:
        cur.execute(sql, tuple(params))
        return cur.fetchall()

def obtener_estadisticas_generales():
    """Genera estadísticas globales para el panel de administración."""
    sql_totales = """
        SELECT 
            COUNT(*) as total_examenes,
            COUNT(CASE WHEN estado = 'COMPLETADO' THEN 1 END) as total_completados,
            COUNT(CASE WHEN estado = 'ANULADO' THEN 1 END) as total_anulados,
            COALESCE(AVG(CASE WHEN estado = 'COMPLETADO' THEN puntaje END), 0.0) as promedio_puntaje,
            COALESCE(MAX(puntaje), 0.0) as puntaje_maximo
        FROM resultados;
    """
    sql_por_area = """
        SELECT area, COUNT(*) as cantidad, COALESCE(AVG(puntaje), 0.0) as promedio
        FROM resultados
        WHERE estado = 'COMPLETADO'
        GROUP BY area
        ORDER BY area;
    """
    sql_ultimos = """
        SELECT r.*, u.nombre, u.apellido, u.dni, u.carrera,
               (SELECT COUNT(*) FROM eventos_monitoreo em WHERE em.resultado_id = r.id) as faltas_count
        FROM resultados r
        JOIN usuarios u ON r.usuario_id = u.id
        ORDER BY r.terminado_en DESC
        LIMIT 25;
    """
    with get_db_cursor(commit=False) as cur:
        cur.execute(sql_totales)
        totales = cur.fetchone()
        cur.execute(sql_por_area)
        por_area = cur.fetchall()
        cur.execute(sql_ultimos)
        ultimos = cur.fetchall()
        
    return {
        'totales': totales,
        'por_area': por_area,
        'ultimos': ultimos
    }
