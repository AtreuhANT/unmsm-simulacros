"""Completa la vista previa y conserva las claves fuera de static.

Las letras se cotejaron con las alternativas del examen y el texto del PDF
de respuestas. Este documento tiene una entrada 21 vacía: desde la 22,
el número publicado de respuesta es el de la pregunta más uno.
"""

import argparse
import hashlib
import json
from pathlib import Path


# Número del examen: alternativa correspondiente al texto publicado.
# Las preguntas 47 y 71 incorporan las correcciones acordadas con el usuario.
CLAVES = {
    11:'A', 12:'C', 13:'B', 14:'B', 15:'C', 16:'A', 17:'D', 18:'D', 19:'E', 20:'C',
    21:'E', 22:'A', 23:'D', 24:'B', 25:'C', 26:'E', 27:'B', 28:'C', 29:'A', 30:'D',
    31:'E', 32:'A', 33:'D', 34:'C', 35:'C', 36:'D', 37:'B', 38:'A', 39:'C', 40:'E',
    41:'A', 42:'B', 43:'B', 44:'C', 45:'D', 46:'A', 47:'D', 48:'A', 49:'E', 50:'D',
    51:'E', 52:'B', 53:'D', 54:'E', 55:'C', 56:'E', 57:'B', 58:'D', 59:'A', 60:'D',
    61:'A', 62:'B', 63:'B', 64:'E', 65:'C', 66:'C', 67:'D', 68:'A', 69:'C', 70:'B',
    71:'B', 72:'C', 73:'B', 74:'D', 75:'A', 76:'E', 77:'C', 78:'E', 79:'D', 80:'D',
    81:'E', 82:'C', 83:'A', 84:'B', 85:'C', 86:'A', 87:'B', 88:'A', 89:'E', 90:'B',
    91:'D', 92:'C', 93:'A', 94:'D', 95:'C', 96:'E', 97:'E', 98:'E', 99:'A', 100:'B',
}


def completar(pdf_respuestas: Path) -> None:
    raiz = Path(__file__).resolve().parents[1]
    carpeta = raiz / 'static/importaciones/unmsm-2026-i-a'
    ruta_datos = carpeta / 'datos.json'
    datos = json.loads(ruta_datos.read_text(encoding='utf-8'))
    academicas = [q for q in datos['preguntas'] if q['id'] >= 11]
    actitudinales = json.loads((raiz / 'data/examenes/actitudinales_area_a.json').read_text(encoding='utf-8'))
    assert [q['id'] for q in actitudinales] == list(range(1, 11))
    assert [q['id'] for q in academicas] == list(range(11, 101))
    assert set(CLAVES) == set(range(11, 101))
    privadas = []
    publicas = []
    for pregunta in actitudinales:
        pregunta = dict(pregunta, seccion='Preguntas actitudinales', origen='Creación original para práctica')
        assert set(pregunta['opciones']) == set('ABCDE')
        assert pregunta['correcta'] in pregunta['opciones']
        privadas.append(pregunta)
        publicas.append({k:v for k,v in pregunta.items() if k not in ('correcta', 'explicacion')})
    for pregunta in academicas:
        numero = pregunta['id']
        clave = {
            'id': numero, 'correcta': CLAVES[numero],
            'numero_respuesta_pdf': numero if numero <= 20 else numero + 1,
            'origen': 'PDF de respuestas Lumbreras / Academia ADUNI',
            'estado_clave': 'transcrita_del_documento',
        }
        if numero == 47:
            clave.update(estado_clave='corregida',
                         observacion='Corrección indicada por el usuario: D) sé - mas - sí - mí. Clave D.')
        if numero == 71:
            clave.update(estado_clave='corregida',
                         observacion='Corrección autorizada por el usuario: B) El efecto invernadero. Sustituye la respuesta repetida de la pregunta anterior.')
        privadas.append(dict(pregunta, **{k:v for k,v in clave.items() if k != 'id'}))
        publicas.append(dict(pregunta, origen='PDF del examen · Lumbreras / Academia ADUNI'))
    privado = {
        'titulo': 'Área A 2026-I · Banco de revisión',
        'fuente_respuestas': pdf_respuestas.name,
        'sha256_respuestas': hashlib.sha256(pdf_respuestas.read_bytes()).hexdigest(),
        'apto_calificacion': True,
        'pendientes_revision': [],
        'nota': 'Claves transcritas del documento con correcciones autorizadas en 47 y 71. Fuente del banco activo de 100 preguntas; sin auditoría académica independiente.',
        'preguntas': privadas,
    }
    ruta_edicion = raiz / 'data/examenes/edicion_area_a.json'
    if ruta_edicion.exists():
        edicion = json.loads(ruta_edicion.read_text(encoding='utf-8'))
        por_id = {q['id']: q for q in edicion['preguntas']}
        for lista in (publicas, privadas):
            for pregunta in lista:
                pregunta.update(por_id.get(pregunta['id'], {}))
                pregunta['curso'] = next(g['nombre'] for g in edicion['grupos'] if pregunta['id'] in g['preguntas'])
        for destino in (datos, privado):
            destino.update(lecturas=edicion['lecturas'], grupos=edicion['grupos'])
    (raiz / 'data/examenes/area_a_2026_i_revision.json').write_text(json.dumps(privado, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    datos.update(preguntas=publicas, faltantes=[], claves_disponibles=True,
                 estado='Vista previa de 100 preguntas; claves privadas con correcciones en 47 y 71')
    ruta_datos.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (carpeta / 'datos.js').write_text('window.EXAMEN_IMPORTADO = ' + json.dumps(datos, ensure_ascii=False) + ';\n', encoding='utf-8')
    lineas = ['# Preguntas actitudinales originales — Área A', '',
              'Material creado para práctica. No son preguntas oficiales ni un instrumento psicométrico validado. La clave señala la actuación más adecuada en cada situación.', '']
    for pregunta in actitudinales:
        lineas += [f"## {pregunta['id']}. {pregunta['competencia']}", '', pregunta['enunciado'], '']
        lineas += [f"- **{letra})** {texto}" for letra,texto in pregunta['opciones'].items()]
        lineas += ['', f"**Respuesta: {pregunta['correcta']}.** {pregunta['explicacion']}", '']
    (raiz / 'docs/PREGUNTAS_ACTITUDINALES_AREA_A.md').write_text('\n'.join(lineas), encoding='utf-8')
    print('100 preguntas: 10 originales + 90 del PDF. Claves privadas; 47 y 71 corregidas.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('respuestas_pdf', type=Path)
    completar(parser.parse_args().respuestas_pdf)
