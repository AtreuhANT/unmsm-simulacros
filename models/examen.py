"""Versiones inmutables: el intento conserva el banco con el que comenzó."""

import hashlib
import json

from models.database import get_db_cursor
from utils.preguntas import cargar_preguntas_area


def guardar_version_examen(cur, area, duracion_minutos):
    preguntas = cargar_preguntas_area(area)
    if not preguntas:
        raise ValueError('Banco de preguntas no disponible')
    contenido = json.dumps(preguntas, ensure_ascii=False, sort_keys=True)
    titulo = f'Área {area} · {hashlib.sha256(contenido.encode()).hexdigest()[:16]}'
    cur.execute('SELECT id FROM examenes_versiones WHERE area = %s AND titulo = %s '
                'AND duracion_minutos = %s AND preguntas_json = %s::jsonb ORDER BY id LIMIT 1',
                (area, titulo, duracion_minutos, contenido))
    version = cur.fetchone()
    if version:
        return version['id']
    cur.execute('INSERT INTO examenes_versiones (area,titulo,duracion_minutos,preguntas_json) '
                'VALUES (%s,%s,%s,%s::jsonb) RETURNING id',
                (area, titulo, duracion_minutos, contenido))
    return cur.fetchone()['id']


def cargar_preguntas_intento(intento, cur=None):
    version_id = intento.get('examen_version_id')
    if version_id is None:
        # Todos los intentos anteriores a la activación carecían de versión.
        return cargar_preguntas_area(intento['area'], historico=True)
    if cur is None:
        with get_db_cursor() as cursor:
            return cargar_preguntas_intento(intento, cursor)
    cur.execute('SELECT preguntas_json FROM examenes_versiones WHERE id = %s AND area = %s',
                (version_id, intento['area']))
    version = cur.fetchone()
    if not version:
        raise ValueError('Versión de examen no disponible')
    return version['preguntas_json']
