import os
import json
import logging
from config import Config

logger = logging.getLogger(__name__)

# Catálogo oficial de Áreas y Carreras UNMSM
AREAS_UNMSM = {
    'A': {
        'nombre': 'Ciencias de la Salud',
        'carreras': [
            'Medicina Humana', 'Obstetricia', 'Enfermería', 'Tecnología Médica', 
            'Nutrición', 'Farmacia y Bioquímica', 'Odontología', 
            'Medicina Veterinaria', 'Psicología'
        ]
    },
    'B': {
        'nombre': 'Ciencias Básicas',
        'carreras': [
            'Química', 'Física', 'Matemática', 'Estadística', 
            'Investigación Operativa', 'Genética', 'Ciencias Biológicas'
        ]
    },
    'C': {
        'nombre': 'Ingenierías',
        'carreras': [
            'Ingeniería Civil', 'Ingeniería de Sistemas', 'Ingeniería Industrial', 
            'Ingeniería de Software', 'Ingeniería Eléctrica', 'Ingeniería Electrónica', 
            'Ingeniería de Telecomunicaciones', 'Ingeniería Nuclear', 
            'Ingeniería Biomédica', 'Ingeniería Mecatrónica'
        ]
    },
    'D': {
        'nombre': 'Ciencias Económicas y de la Gestión',
        'carreras': [
            'Administración', 'Administración de Negocios Internacionales', 
            'Administración de Turismo', 'Auditoría Empresarial', 
            'Contabilidad', 'Economía'
        ]
    },
    'E': {
        'nombre': 'Humanidades y Ciencias Jurídicas y Sociales',
        'carreras': [
            'Derecho', 'Literatura', 'Filosofía', 'Historia', 
            'Educación', 'Comunicación Social', 'Lingüística', 'Arqueología'
        ]
    }
}

def obtener_ruta_examen(area):
    """Devuelve la ruta absoluta del archivo JSON de preguntas según el área."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    area_normalizada = area.upper().strip()
    return os.path.join(base_dir, 'data', 'examenes', f'area_{area_normalizada.lower()}.json')

def cargar_preguntas_area(area):
    """
    Carga el banco de preguntas oficial del área indicada.
    Retorna la lista de preguntas completas (con respuesta correcta).
    """
    ruta = obtener_ruta_examen(area)
    if not os.path.exists(ruta):
        logger.warning(f"Archivo de examen no encontrado para el área {area}: {ruta}. Usando fallback.")
        # Retorna lista vacía si no existe
        return []
    
    with open(ruta, 'r', encoding='utf-8') as f:
        preguntas = json.load(f)
        return preguntas

def sanitizar_preguntas_para_cliente(preguntas):
    """
    SEGURIDAD: Elimina 'correcta' y 'explicacion' antes de enviar el examen al frontend.
    El navegador jamás debe recibir las respuestas correctas para evitar trampas en DevTools.
    """
    preguntas_cliente = []
    for q in preguntas:
        copia = {
            'id': q['id'],
            'seccion': q.get('seccion', 'General'),
            'enunciado': q['enunciado'],
            'opciones': q['opciones']
        }
        preguntas_cliente.append(copia)
    return preguntas_cliente

def calcular_puntaje(respuestas_usuario, preguntas):
    """
    Fórmula Oficial de Puntuación UNMSM:
    - Respuesta correcta: +20.0 puntos.
    - Respuesta incorrecta: -1.125 puntos.
    - Respuesta en blanco o deseleccionada: 0.0 puntos.
    - Puntaje final: Máximo entre 0.0 y el puntaje obtenido (nunca negativo).
    
    Parámetros:
        respuestas_usuario: dict con llaves str(id_pregunta) y valor letra seleccionada (o None/"")
        preguntas: lista de dicts con las preguntas y su campo 'correcta'
    """
    correctas = 0
    incorrectas = 0
    blanco = 0
    detalles = []
    
    # Crear un mapa rápido por id
    mapa_preguntas = {str(q['id']): q for q in preguntas}
    
    for q_id, q_data in mapa_preguntas.items():
        resp_dada = respuestas_usuario.get(q_id)
        if resp_dada:
            resp_dada = str(resp_dada).strip().upper()
        else:
            resp_dada = None
            
        correcta = str(q_data['correcta']).strip().upper()
        
        if not resp_dada:
            blanco += 1
            es_correcta = False
            es_blanco = True
            puntos_item = Config.PUNTO_BLANCO
        elif resp_dada == correcta:
            correctas += 1
            es_correcta = True
            es_blanco = False
            puntos_item = Config.PUNTO_CORRECTA
        else:
            incorrectas += 1
            es_correcta = False
            es_blanco = False
            puntos_item = Config.PUNTO_INCORRECTA
            
        detalles.append({
            'id': q_data['id'],
            'seccion': q_data.get('seccion', 'General'),
            'enunciado': q_data['enunciado'],
            'opciones': q_data.get('opciones', {}),
            'respuesta_usuario': resp_dada,
            'respuesta_correcta': correcta,
            'es_correcta': es_correcta,
            'es_blanco': es_blanco,
            'puntos': puntos_item,
            'explicacion': q_data.get('explicacion', '')
        })
        
    puntaje_bruto = (correctas * Config.PUNTO_CORRECTA) + (incorrectas * Config.PUNTO_INCORRECTA)
    puntaje_final = max(0.0, puntaje_bruto)
    
    return {
        'puntaje': round(puntaje_final, 3),
        'puntaje_bruto': round(puntaje_bruto, 3),
        'correctas': correctas,
        'incorrectas': incorrectas,
        'blanco': blanco,
        'total': len(preguntas),
        'detalles': detalles
    }
