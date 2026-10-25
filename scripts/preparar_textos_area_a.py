"""Primera edición textual del área A: HV y organización de todos los cursos.

Usa las posiciones verificadas de este PDF específico. No inicia Flask.
"""

import argparse
import json
import re
from pathlib import Path

import pymupdf


RAIZ = Path(__file__).resolve().parents[1]
CARPETA = RAIZ / 'static/importaciones/unmsm-2026-i-a'


def limpiar(texto: str) -> str:
    texto = texto.replace('\xad\n', '').replace('\xad', '')
    return re.sub(r'\s+', ' ', texto).strip()


def parrafos(texto: str) -> list[str]:
    return [limpiar(p) for p in re.split(r'\n\s*\t\s*\n', texto) if limpiar(p)]


def bloque(pagina, prefijo: str) -> str:
    return next(b[4] for b in pagina.get_text('blocks') if isinstance(b[4], str) and b[4].startswith(prefijo))


def aplicar_edicion(datos: dict, edicion: dict) -> None:
    por_id = {q['id']: q for q in edicion['preguntas']}
    datos.update(lecturas=edicion['lecturas'], grupos=edicion['grupos'])
    for pregunta in datos['preguntas']:
        if pregunta['id'] in por_id:
            pregunta.update(por_id[pregunta['id']])
        grupo = next(g for g in edicion['grupos'] if pregunta['id'] in g['preguntas'])
        pregunta['curso'] = grupo['nombre']


def preparar(pdf: Path) -> None:
    documento = pymupdf.open(pdf)
    datos = json.loads((CARPETA / 'datos.json').read_text(encoding='utf-8'))
    texto1 = bloque(documento[2], 'Texto N.')
    texto1 = texto1.split('\n', 1)[1]
    texto_a = bloque(documento[3], 'Texto N.').split('Texto A', 1)[1]
    texto_a += '\n\t\n' + bloque(documento[4], 'Otro beneficio')
    texto_b = bloque(documento[4], 'Texto B').split('\n', 1)[1]
    texto3 = bloque(documento[5], 'Texto 3').split('\n', 1)[1]
    figura = 'lectura-1-infografia.png'
    documento[2].get_pixmap(matrix=pymupdf.Matrix(3, 3), clip=pymupdf.Rect(223.9, 185.2, 432.3, 479.6)).save(str(CARPETA / figura))
    lecturas = [
        {'id':'hv-1', 'titulo':'Texto N.º 1', 'preguntas':[11,12,13],
         'bloques':[{'parrafos':parrafos(texto1)}],
         'figuras':[{'imagen':figura, 'descripcion':'Infografía del texto: pasos para comprobar si una noticia es falsa.'}],
         'fuente':'Ubillos, J. (30 de agosto, 2023). Las noticias falsas en México: la otra pandemia. Periódico Claridad.',
         'url':'https://www.gob.mx/profeco/articulos/noticias-falsas-la-otra-pandemia?idiom=es'},
        {'id':'hv-2', 'titulo':'Texto N.º 2', 'preguntas':[14,15,16,17],
         'bloques':[{'titulo':'Texto A', 'parrafos':parrafos(texto_a)}, {'titulo':'Texto B', 'parrafos':parrafos(texto_b)}],
         'figuras':[],
         'fuente':'AICPA & CIMA (14 de septiembre, 2023). Ventajas y desventajas de las tarjetas de crédito.',
         'url':'https://www.aicpa-cima.com/resources/article/ventajas-y-desventajas-de-las-tarjetas-de-credito'},
        {'id':'hv-3', 'titulo':'Texto N.º 3', 'preguntas':[18,19,20], 'idioma':'en',
         'bloques':[{'parrafos':parrafos(texto3)}], 'figuras':[],
         'fuente':'Adapted from Where in the EU Do Most Young Adults Have a University Degree? Euronews. 12 September 2025.',
         'url':'https://www.euronews.com/my-europe/2025/09/12/where-in-the-eu-do-most-young-adults-have-a-university-degree'},
    ]
    rangos = [
        ('Actitudinales',1,10), ('HV',11,20), ('H.L.M.',21,30),
        ('Aritmética',31,34), ('Geometría',35,37), ('Álgebra',38,40),
        ('Trigonometría',41,42), ('Lenguaje',43,49), ('Literatura',50,53),
        ('Psicología',54,59), ('Educación Cívica',60,63), ('Historia del Perú',64,66),
        ('Historia Universal',67,68), ('Geografía',69,72), ('Economía',73,76),
        ('Filosofía',77,80), ('Física',81,85), ('Química',86,92), ('Biología',93,100),
    ]
    grupos = [{'nombre':nombre, 'preguntas':list(range(inicio,fin+1))} for nombre,inicio,fin in rangos]
    grupos[1]['nombre_completo'] = 'Habilidad Verbal'
    grupos[1]['lecturas'] = ['hv-1','hv-2','hv-3']
    grupos[2]['nombre_completo'] = 'Habilidad Lógico-Matemática'
    preguntas = []
    for pregunta in datos['preguntas']:
        numero = pregunta['id']
        if not 11 <= numero <= 20:
            continue
        texto = pregunta['texto'].split('\n', 1)[1]
        texto = re.split(r'Texto N[.º°\s]', texto)[0]
        texto = texto.split('Habilidad Lógico-Matemática')[0]
        partes = re.split(r'([A-E])\)\s*', texto)
        opciones = {partes[i]:limpiar(partes[i+1]) for i in range(1,len(partes),2)}
        if numero == 18:
            opciones['E'] = 'Higher levels of education and increased employment rates'
        assert list(opciones) == list('ABCDE'), numero
        lectura = next(l for l in lecturas if numero in l['preguntas'])
        enunciado = re.sub(r' (I{1,3}\.) ', r'\n\n\1 ', limpiar(partes[0]))
        preguntas.append({'id':numero, 'formato':'texto', 'enunciado':enunciado,
                          'opciones':opciones, 'lectura_id':lectura['id']})
    ruta_edicion = RAIZ / 'data/examenes/edicion_area_a.json'
    if ruta_edicion.exists():
        anterior = json.loads(ruta_edicion.read_text(encoding='utf-8'))
        preguntas.extend(q for q in anterior['preguntas'] if q['id'] > 20)
        preguntas.sort(key=lambda q: q['id'])
    edicion = {'etapa':'Edición textual por cursos',
               'grupos':grupos, 'lecturas':lecturas, 'preguntas':preguntas}
    (RAIZ / 'data/examenes/edicion_area_a.json').write_text(json.dumps(edicion, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    aplicar_edicion(datos, edicion)
    (CARPETA / 'datos.json').write_text(json.dumps(datos, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (CARPETA / 'datos.js').write_text('window.EXAMEN_IMPORTADO = ' + json.dumps(datos, ensure_ascii=False) + ';\n', encoding='utf-8')
    privado_path = RAIZ / 'data/examenes/area_a_2026_i_revision.json'
    privado = json.loads(privado_path.read_text(encoding='utf-8'))
    aplicar_edicion(privado, edicion)
    privado_path.write_text(json.dumps(privado, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('HV 11–20 en texto, tres lecturas compartidas, una infografía y 19 cursos sin huecos.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pdf', type=Path)
    preparar(parser.parse_args().pdf)
