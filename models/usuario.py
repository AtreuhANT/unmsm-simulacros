import json
from werkzeug.security import generate_password_hash, check_password_hash
from models.database import get_db_cursor

def crear_usuario(nombre, apellido, dni, password, carrera, area, descriptores_faciales=None, es_admin=False):
    """
    Registra un nuevo usuario en la base de datos con contraseña elegida libremente.
    - Password hasheado con Werkzeug.
    - descriptores_faciales es completamente opcional (el registro no exige cámara).
    """
    password_hash = generate_password_hash(password)
    
    # Formato JSON string para inserción en JSONB
    if descriptores_faciales is not None:
        if isinstance(descriptores_faciales, (list, dict)):
            descriptores_json = json.dumps(descriptores_faciales)
        else:
            descriptores_json = descriptores_faciales
    else:
        descriptores_json = json.dumps([])

    sql = """
        INSERT INTO usuarios (nombre, apellido, dni, password_hash, carrera, area, descriptores_faciales, es_admin)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, nombre, apellido, dni, carrera, area, descriptores_faciales, es_admin, creado_en;
    """
    
    with get_db_cursor(commit=True) as cur:
        cur.execute(sql, (
            nombre.strip(),
            apellido.strip(),
            dni.strip(),
            password_hash,
            carrera.strip(),
            area.upper().strip(),
            descriptores_json,
            es_admin
        ))
        return cur.fetchone()

def guardar_plantilla_facial(usuario_id, descriptores, modelo_version='face-api-0.22', dispositivo=None):
    """Guarda una nueva plantilla biométrica facial en la tabla independiente plantillas_faciales."""
    descriptores_json = json.dumps(descriptores) if isinstance(descriptores, (list, dict)) else descriptores
    sql = """
        INSERT INTO plantillas_faciales (usuario_id, modelo_version, dimension, descriptores, estado_acreditacion)
        VALUES (%s, %s, 128, %s, 'AUTO_ENROLADO')
        RETURNING id, usuario_id, modelo_version, dimension, descriptores, estado_acreditacion, creado_en;
    """
    with get_db_cursor(commit=True) as cur:
        cur.execute(sql, (usuario_id, modelo_version, descriptores_json))
        return cur.fetchone()

def obtener_plantilla_facial(usuario_id):
    """Retorna la última plantilla biométrica facial del usuario o None si aún no ha sido enrolado."""
    sql = """
        SELECT id, usuario_id, modelo_version, dimension, descriptores, estado_acreditacion, creado_en
        FROM plantillas_faciales
        WHERE usuario_id = %s
        ORDER BY creado_en DESC
        LIMIT 1;
    """
    with get_db_cursor(commit=False) as cur:
        cur.execute(sql, (usuario_id,))
        return cur.fetchone()

def obtener_usuario_por_dni(dni):
    """Retorna un usuario por su DNI o None si no existe."""
    sql = """
        SELECT id, nombre, apellido, dni, password_hash, carrera, area, 
               descriptores_faciales, es_admin, creado_en
        FROM usuarios 
        WHERE dni = %s;
    """
    with get_db_cursor(commit=False) as cur:
        cur.execute(sql, (dni.strip(),))
        return cur.fetchone()

def obtener_usuario_por_id(usuario_id):
    """Retorna un usuario por su ID interno o None si no existe."""
    sql = """
        SELECT id, nombre, apellido, dni, password_hash, carrera, area,
               consentimiento_celular_en, consentimiento_celular_version,
               descriptores_faciales, es_admin, creado_en
        FROM usuarios 
        WHERE id = %s;
    """
    with get_db_cursor(commit=False) as cur:
        cur.execute(sql, (usuario_id,))
        return cur.fetchone()

def verificar_credenciales(dni, password):
    """Valida DNI y contraseña. Retorna el usuario si coincide, o None."""
    usuario = obtener_usuario_por_dni(dni)
    if usuario and check_password_hash(usuario['password_hash'], password):
        return usuario
    return None

def actualizar_descriptores(usuario_id, descriptores_faciales):
    """Actualiza los vectores biométricos de un usuario."""
    descriptores_json = json.dumps(descriptores_faciales) if isinstance(descriptores_faciales, (list, dict)) else descriptores_faciales
    sql = """
        UPDATE usuarios 
        SET descriptores_faciales = %s 
        WHERE id = %s
        RETURNING id;
    """
    with get_db_cursor(commit=True) as cur:
        cur.execute(sql, (descriptores_json, usuario_id))
        return cur.fetchone() is not None

def hacer_admin_por_dni(dni, es_admin=True):
    """Modifica el rol de administrador de un usuario por su DNI."""
    sql = """
        UPDATE usuarios 
        SET es_admin = %s 
        WHERE dni = %s
        RETURNING id, dni, es_admin;
    """
    with get_db_cursor(commit=True) as cur:
        cur.execute(sql, (es_admin, dni.strip()))
        return cur.fetchone()

def listar_usuarios(limite=100, offset=0):
    """Lista usuarios para la vista de administración."""
    sql = """
        SELECT id, nombre, apellido, dni, carrera, area, es_admin, creado_en
        FROM usuarios
        ORDER BY id DESC
        LIMIT %s OFFSET %s;
    """
    with get_db_cursor(commit=False) as cur:
        cur.execute(sql, (limite, offset))
        return cur.fetchall()
