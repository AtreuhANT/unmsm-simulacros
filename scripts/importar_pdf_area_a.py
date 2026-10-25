"""Genera una vista previa fiel al PDF, sin modificar bancos calificados.

Requiere PyMuPDF, solo para ejecutar la importación. No importa la aplicación.
"""

import argparse
import hashlib
import json
import re
from pathlib import Path

import pymupdf


def importar(origen: Path, destino: Path) -> None:
    destino.mkdir(parents=True, exist_ok=True)
    documento = pymupdf.open(origen)
    preguntas = []
    paginas = []
    encabezados = {}
    for indice in range(2, len(documento) - 1):
        pagina = documento[indice]
        nombre_pagina = f"pagina-{indice + 1:02}.png"
        pix = pagina.get_pixmap(matrix=pymupdf.Matrix(2, 2))
        # PNG evita dependencias adicionales de codificación de imágenes.
        pix.save(str(destino / nombre_pagina))
        paginas.append({"numero": indice + 1, "imagen": nombre_pagina})
        lineas = []
        for bloque in pagina.get_text('dict')['blocks']:
            for linea in bloque.get('lines', []):
                texto = ''.join(span['text'] for span in linea['spans'])
                coincidencia = re.search(r'PREGUNTA\s+N[.º°\s]*\s*(\d+)', texto)
                if coincidencia:
                    lineas.append((int(coincidencia[1]), pymupdf.Rect(linea['bbox'])))
        encabezados[indice] = lineas
        for numero, caja in lineas:
            izquierda = caja.x0 < pagina.rect.width / 2
            # Las páginas pares e impares tienen márgenes diferentes.
            # Anclar el recorte al encabezado real evita cortar A), D) o el enunciado.
            x0, x1 = caja.x0 - 2, caja.x0 + 186.5
            siguientes = [r.y0 for n, r in lineas
                          if (r.x0 < pagina.rect.width / 2) == izquierda
                          and r.y0 > caja.y0 + 1]
            fondo = min(siguientes) - 6 if siguientes else pagina.rect.height - 30
            region = pymupdf.Rect(x0, caja.y0 - 3, x1, fondo)
            # Ajustar el final al último texto de la región; conservar los gráficos intermedios.
            palabras = pagina.get_text('words', clip=region)
            texto_region = pagina.get_text(clip=region)
            if palabras and re.search(r'E\)', texto_region):
                region.y1 = min(region.y1, max(p[3] for p in palabras) + 8)
            nombre = f"pregunta-{numero:03}.png"
            pagina.get_pixmap(matrix=pymupdf.Matrix(3, 3), clip=region).save(str(destino / nombre))
            preguntas.append({
                'id': numero, 'pagina': indice + 1, 'imagen': nombre,
                'imagenes': [nombre], 'texto': pagina.get_text(clip=region),
                '_izquierda': izquierda,
            })
    for pregunta in preguntas:
        if re.search(r'E\)', pregunta['texto']):
            continue
        indice = pregunta['pagina'] - 1
        siguiente_izquierda = not pregunta['_izquierda']
        if siguiente_izquierda:
            indice += 1
        pagina = documento[indice]
        siguientes = [r for n, r in encabezados[indice]
                      if (r.x0 < pagina.rect.width / 2) == siguiente_izquierda]
        if not siguientes:
            raise ValueError(f"No se encontró continuación de {pregunta['id']}")
        primero = min(siguientes, key=lambda r: r.y0)
        region = pymupdf.Rect(primero.x0 - 2, 40, primero.x0 + 186.5, primero.y0 - 6)
        texto = pagina.get_text(clip=region)
        if not re.search(r'E\)', texto):
            raise ValueError(f"Continuación incompleta: {pregunta['id']}")
        nombre = f"pregunta-{pregunta['id']:03}-continuacion.png"
        pagina.get_pixmap(matrix=pymupdf.Matrix(3, 3), clip=region).save(str(destino / nombre))
        pregunta['imagenes'].append(nombre)
        pregunta['texto'] += '\n' + texto
    for pregunta in preguntas:
        del pregunta['_izquierda']
    preguntas.sort(key=lambda q: q['id'])
    ids = [q['id'] for q in preguntas]
    if ids != list(range(11, 101)):
        raise ValueError(f'Numeración inesperada: {ids}')
    datos = {
        'titulo': 'UNMSM 2026-I · Área A',
        'fuente': origen.name,
        'sha256': hashlib.sha256(origen.read_bytes()).hexdigest(),
        'preguntas': preguntas, 'paginas': paginas,
        'faltantes': list(range(1, 11)), 'claves_disponibles': False,
    }
    (destino / 'datos.json').write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding='utf-8')
    (destino / 'datos.js').write_text('window.EXAMEN_IMPORTADO = ' + json.dumps(datos, ensure_ascii=False) + ';\n', encoding='utf-8')
    print(f'Importadas {len(preguntas)} preguntas (11–100), {len(paginas)} páginas de referencia. Sin claves.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pdf', type=Path)
    argumentos = parser.parse_args()
    importar(argumentos.pdf, Path(__file__).resolve().parents[1] / 'static' / 'importaciones' / 'unmsm-2026-i-a')
