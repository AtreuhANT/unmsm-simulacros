"""Publica los bancos aprobados conservando los originales de diez preguntas.

Solo escribe JSON locales; no importa Flask ni conecta con PostgreSQL.
"""

import json
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]


def activar():
    carpeta = RAIZ / 'data/examenes'
    anteriores = carpeta / 'anteriores'
    preparados = {}
    for area in 'ABCDE':
        fuente = carpeta / ('area_a_2026_i_revision.json' if area == 'A' else f'area_{area.lower()}_practica.json')
        banco = json.loads(fuente.read_text(encoding='utf-8'))
        lecturas = {l['id']: l for l in banco['lecturas']}
        preguntas = []
        for original in banco['preguntas']:
            q = dict(original)
            q['seccion'] = q.get('curso', q.get('seccion', 'General'))
            if q.get('lectura_id'):
                q['lectura'] = lecturas[q['lectura_id']]
            if area == 'A':
                q['base_recursos'] = 'importaciones/unmsm-2026-i-a/'
            if q['correcta'] not in q['opciones'] or set(q['opciones']) != set('ABCDE'):
                raise ValueError(f'Clave u opciones inválidas: {area}/{q["id"]}')
            preguntas.append(q)
        if [q['id'] for q in preguntas] != list(range(1,101)):
            raise ValueError(f'Área {area}: se exigen IDs 1–100')
        preparados[area] = preguntas
    # Validar todos los destinos antes de sustituir cualquiera.
    for area in 'ABCDE':
        destino = carpeta / f'area_{area.lower()}.json'
        archivo = anteriores / destino.name
        if not archivo.exists():
            original = json.loads(destino.read_text(encoding='utf-8'))
            if len(original) != 10:
                raise ValueError(f'Falta el archivo histórico de diez preguntas: {area}')
    anteriores.mkdir(exist_ok=True)
    for area, preguntas in preparados.items():
        destino = carpeta / f'area_{area.lower()}.json'
        archivo = anteriores / destino.name
        if not archivo.exists():
            archivo.write_bytes(destino.read_bytes())
        destino.write_text(json.dumps(preguntas, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(f'{area}: 100 preguntas activas; banco histórico conservado.')


if __name__ == '__main__':
    activar()
