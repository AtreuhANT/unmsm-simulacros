"""Reconstruye figuras como trazos SVG y añade notación matemática estructurada.

Opera sobre la edición revisada; no resuelve preguntas ni cambia sus claves.
"""

import argparse
import html
import json
import re
from pathlib import Path

import pymupdf

from convertir_area_a_texto import FIGURAS


RAIZ = Path(__file__).resolve().parents[1]
CARPETA = RAIZ / 'static/importaciones/unmsm-2026-i-a'
COLOR_EDITORIAL = (0.820, 0.895, 0.946)


def numero(valor: float) -> str:
    return f'{valor:.4f}'.rstrip('0').rstrip('.')


def color(rgb) -> str:
    return 'none' if rgb is None else '#' + ''.join(f'{max(0,min(255,round(v*255))):02x}' for v in rgb)


def trazar_detalles(pagina, caja) -> list[str]:
    """Convierte pequeños detalles y sombreados inline en superficies vectoriales.

    El PDF guarda algunos puntos y brillos como mapas inline. Los SVG finales
    no contienen imágenes ni referencias de datos raster.
    """
    superficies = []
    agua = caja == pymupdf.Rect(235,44,423,180)
    if agua:
        superficies.append('<defs><linearGradient id="agua" x2="0" y2="1"><stop stop-color="#f3fbff"/><stop offset="1" stop-color="#99c9e5"/></linearGradient></defs><path fill="url(#agua)" d="M252 66H338V106C380 108 407 133 416 176H406C398 141 381 118 340 115V162Q340 175 330 175H260Q252 175 252 167Z"/>')
    for bloque in pagina.get_text('dict')['blocks']:
        if bloque['type'] != 1:
            continue
        r = pymupdf.Rect(bloque['bbox'])
        if not caja.contains(r) or max(r.width,r.height) <= 6:
            continue
        if agua and max(r.width,r.height) > 20:
            continue
        pix = pymupdf.Pixmap(bloque['image'])
        if pix.colorspace.n != 3: pix = pymupdf.Pixmap(pymupdf.csRGB,pix)
        muestras = pix.samples
        dx,dy = r.width/pix.width,r.height/pix.height
        caminos = {}
        for y in range(pix.height):
            x = 0
            while x < pix.width:
                pos = (y*pix.width+x)*pix.n
                rgb = tuple(min(255,round(v/12)*12) for v in muestras[pos:pos+3])
                inicio = x
                x += 1
                while x < pix.width:
                    pos = (y*pix.width+x)*pix.n
                    siguiente = tuple(min(255,round(v/12)*12) for v in muestras[pos:pos+3])
                    if siguiente != rgb: break
                    x += 1
                if min(rgb) >= 248: continue
                izquierda,arriba = r.x0+inicio*dx,r.y0+y*dy
                ancho,alto = (x-inicio)*dx,dy
                caminos.setdefault(rgb,[]).append(f'M{numero(izquierda)} {numero(arriba)}h{numero(ancho)}v{numero(alto)}h-{numero(ancho)}Z')
        for rgb,caminos_color in caminos.items():
            superficies.append('<path fill="#' + ''.join(f'{v:02x}' for v in rgb) + '" d="' + ''.join(caminos_color) + '"/>')
    return superficies


def vectorizar(pagina, region: tuple, titulo: str) -> str:
    caja = pymupdf.Rect(region)
    partes = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{caja.x0} {caja.y0} {caja.width} {caja.height}" role="img" aria-label="{html.escape(titulo)}">',
              f'<title>{html.escape(titulo)}</title>',
              f'<defs><clipPath id="limite"><rect x="{caja.x0}" y="{caja.y0}" width="{caja.width}" height="{caja.height}"/></clipPath></defs>',
              '<g clip-path="url(#limite)">']
    partes.extend(trazar_detalles(pagina,caja))
    for dibujo in pagina.get_drawings():
        # Un segmento horizontal/vertical tiene bbox de área cero: expandirlo
        # antes de probar intersección para conservar ejes, divisiones y cotas.
        if not (dibujo['rect'] + (-0.5,-0.5,0.5,0.5)).intersects(caja):
            continue
        # En este PDF la capa editorial usa un color plano específico; no forma
        # parte de la geometría ni de los datos del ejercicio.
        if dibujo.get('fill') and tuple(round(v,3) for v in dibujo['fill']) == COLOR_EDITORIAL:
            continue
        comandos = []
        actual = None
        for item in dibujo['items']:
            tipo = item[0]
            if tipo in ('l','c'):
                inicio = item[1]
                if actual != inicio:
                    comandos.append(f'M {numero(inicio.x)} {numero(inicio.y)}')
                if tipo == 'l':
                    comandos.append(f'L {numero(item[2].x)} {numero(item[2].y)}')
                else:
                    comandos.append('C ' + ' '.join(f'{numero(p.x)} {numero(p.y)}' for p in item[2:]))
                actual = item[-1]
            elif tipo == 're':
                r = item[1]
                comandos.append(f'M {r.x0} {r.y0} L {r.x1} {r.y0} L {r.x1} {r.y1} L {r.x0} {r.y1} Z')
                actual = None
            elif tipo == 'qu':
                q = item[1]
                comandos.append('M ' + ' L '.join(f'{p.x} {p.y}' for p in (q.ul,q.ur,q.lr,q.ll)) + ' Z')
                actual = None
        if dibujo.get('closePath'):
            comandos.append('Z')
        atributos = {
            'd':' '.join(comandos), 'fill':color(dibujo.get('fill')),
            'stroke':color(dibujo.get('color')), 'stroke-width':str(dibujo.get('width') or 0.5),
            'fill-rule':'evenodd' if dibujo.get('even_odd') else 'nonzero',
            'fill-opacity':str(dibujo.get('fill_opacity',1)),
            'stroke-opacity':str(dibujo.get('stroke_opacity',1)),
            'stroke-linecap':{0:'butt',1:'round',2:'square'}.get(max(dibujo.get('lineCap') or (0,)), 'butt'),
            'stroke-linejoin':{0:'miter',1:'round',2:'bevel'}.get(dibujo.get('lineJoin'), 'round'),
        }
        for clave in ('fill-opacity','stroke-opacity'):
            if atributos[clave] == 'None': atributos[clave] = '1'
        guiones = dibujo.get('dashes') or ''
        patron = re.search(r'\[([^]]+)\]\s*([-\d.]+)', guiones)
        if patron:
            atributos.update({'stroke-dasharray':patron[1], 'stroke-dashoffset':patron[2]})
        partes.append('<path ' + ' '.join(f'{k}="{html.escape(v)}"' for k,v in atributos.items()) + '/>')
    # Los puntos del dominó son diminutos mapas inline en el PDF. Reconstruir
    # cada uno como círculo, conservando número y posición, sin incrustar raster.
    for imagen in pagina.get_image_info():
        r = pymupdf.Rect(imagen['bbox'])
        if not caja.contains(r):
            continue
        if r.width > 6 or r.height > 6:
            continue
        partes.append(f'<circle cx="{(r.x0+r.x1)/2}" cy="{(r.y0+r.y1)/2}" r="{min(r.width,r.height)/3}" fill="#343434"/>')
    for bloque in pagina.get_text('dict')['blocks']:
        for linea in bloque.get('lines', []):
            for span in linea['spans']:
                b = pymupdf.Rect(span['bbox'])
                if not caja.contains(b) or not span['text'].strip():
                    continue
                x,y = span['origin']
                estilo = 'italic' if 'Ita' in span['font'] else 'normal'
                texto = html.escape(span['text'])
                partes.append(f'<text x="{x}" y="{y}" font-family="Georgia,serif" font-size="{span["size"]}" font-style="{estilo}" fill="#{span["color"]:06x}" textLength="{b.width}" lengthAdjust="spacingAndGlyphs">{texto}</text>')
    partes.append('</g></svg>')
    return '\n'.join(partes)


def refinar(pdf: Path) -> None:
    documento = pymupdf.open(pdf)
    ruta = RAIZ / 'data/examenes/edicion_area_a.json'
    edicion = json.loads(ruta.read_text(encoding='utf-8'))
    preguntas = {q['id']:q for q in edicion['preguntas']}
    for n,(pagina,region) in FIGURAS.items():
        nombre = f'figura-{n:03}.svg'
        svg = vectorizar(documento[pagina-1], region, f'Esquema de la pregunta {n}')
        (CARPETA / nombre).write_text(svg, encoding='utf-8')
        preguntas[n]['figuras'] = [{'imagen':nombre, 'descripcion':f'Esquema vectorial de la pregunta {n}', 'formato':'svg'}]
    preguntas[64]['enunciado'] = preguntas[64]['enunciado'].replace('2500\n\na. C. - 100\n\nd. C.', '2500 a. C. – 100 d. C.')

    # Fórmulas anotadas explícitamente para distinguir variables de prosa.
    cambios = {
        23:{'XY':'$XY$', 'A(–2; 3)':'$A(-2;3)$', 'x=3':'$x=3$', '(7; 3)':'$(7;3)$', 'B(–3; –5)':'$B(-3;-5)$', 'y=x':'$y=x$', '(–5; –3)':'$(-5;-3)$', 'C(3; 5)':'$C(3;5)$', 'y=2':'$y=2$', '(3; –1)':'$(3;-1)$'},
        29:{'40π':'$40\\pi$', 'M y N':'$M$ y $N$'},
        34:{'a̅a̅0̅b̅5̅':r'$\overline{\text{aa0b5}}$'},
        35:{'m∠BNC = 40°':r'$\angle BNC=40°$', '50°':'$50°$', 'AOC':'$AOC$'},
        36:{'12√3 cm³':r'$12\sqrt{3}\;\mathrm{cm}^{3}$'.replace('\\;',' '), 'HM = 1 cm':r'$\overline{HM}=1\mathrm{cm}$'},
        37:{'AB = 60 cm':r'$AB=60\mathrm{cm}$', 'BC = 30√2 cm':r'$BC=30\sqrt{2}\mathrm{cm}$', 'AD = 30√3 cm':r'$AD=30\sqrt{3}\mathrm{cm}$', 'DC = 30 cm':r'$DC=30\mathrm{cm}$'},
        39:{'F(t) = −0,5t² + 6t + 104, t ∈ [6; 12].':r'$F(t)=-0,5t^{2}+6t+104,\quad t\in[6;12]$'.replace('\\quad',' ')},
        41:{'$10':r'\$10', 'r = 20√7 m':r'$r=20\sqrt{7}\mathrm{m}$', 'π = 3,14':r'$\pi=3,14$'},
        42:{'(40M + 1200)':'$(40M+1200)$', 'f(x) = (4 sec x − 2) / (1 − 4 sec² x), 2π/3 ≤ x ≤ 5π/4,':r'$f(x)=\frac{4\sec x-2}{1-4\sec^{2}x}$, $\frac{2\pi}{3}\le x\le\frac{5\pi}{4}$,', 'sec(x)':'$\\sec(x)$'},
        81:{'v = 8 m/s':r'$v=8\mathrm{m/s}$', 'R = 2 m':r'$R=2\mathrm{m}$', 'g = 10 m/s²':r'$g=10\mathrm{m/s}^{2}$'},
        83:{'H=12 m':r'$H=12\mathrm{m}$', 'h=2 m':r'$h=2\mathrm{m}$', 'g=10 m/s²':r'$g=10\mathrm{m/s}^{2}$'},
        84:{'a = 10 cm':r'$a=10\mathrm{cm}$', 'eje z':'eje $z$', 'ω = 1200 rad/s':r'$\omega=1200\mathrm{rad/s}$', 'B⃗ = 2 × 10⁻⁵ ĵ T':r'$\vec{B}=2\times10^{-5}\hat{j}\mathrm{T}$'},
        85:{'h=4,14×10⁻¹⁵ eV · s':r'$h=4,14\times10^{-15}\mathrm{eV}\cdot\mathrm{s}$', 'c=3×10⁸ m/s':r'$c=3\times10^{8}\mathrm{m/s}$'},
    }
    for n,reemplazos in cambios.items():
        texto = preguntas[n]['enunciado']
        for antes,despues in reemplazos.items(): texto = texto.replace(antes,despues)
        preguntas[n]['enunciado_rico'] = texto
    preguntas[38]['enunciado_rico'] = r'''Dados los números complejos $z_1=3+2i$ y $z_2=4+i$, determine el valor de verdad (V o F) de las siguientes proposiciones:

I. El producto de ambos es $z_1\cdot z_2=10+11i$.

II. El módulo de la diferencia de ellos es $\lVert z_2-z_1\rVert=\lVert-1-i\rVert=\sqrt{2}$.

III. La suma de sus conjugados es $\overline{z_1}+\overline{z_2}=-7-3i$.

IV. El cociente de ambos es $\frac{z_1}{z_2}=\frac{3}{4}+2i$.'''
    for n in (29,36):
        preguntas[n]['opciones_rico'] = {}
        for letra,texto in preguntas[n]['opciones'].items():
            if n == 36:
                numerador,denominador = texto.split('/')
                formula = r'\frac{' + numerador.replace('π',r'\pi') + '}{' + denominador + '}'
            else: formula = texto.replace('π',r'\pi').replace(' cm',r'\mathrm{cm}')
            preguntas[n]['opciones_rico'][letra] = '$' + formula + '$'
    vectores = [r'2\sqrt{10}\hat{i}-10\sqrt{2}\hat{j}', r'2\sqrt{2}\hat{i}-10\sqrt{10}\hat{j}', r'10\sqrt{2}\hat{i}-2\sqrt{10}\hat{j}', r'2\sqrt{10}\hat{i}+10\sqrt{2}\hat{j}', r'-2\sqrt{10}\hat{i}+10\sqrt{2}\hat{j}']
    preguntas[83]['opciones_rico'] = {k:'$(' + f + r')\mathrm{m/s}$' for k,f in zip('ABCDE',vectores)}
    flujos = [r'2,0\sen(1200t-\frac{\pi}{2})',r'0,2\cos(1200t+\frac{\pi}{2})',r'20\cos(1200t+\frac{\pi}{4})',r'2,0\cos(1200t-\frac{\pi}{2})',r'20\sen(1200t-\frac{\pi}{3})']
    preguntas[84]['opciones_rico'] = {k:'$'+f+r'\mu\mathrm{T}\cdot\mathrm{m}^{2}$' for k,f in zip('ABCDE',flujos)}
    # Imagen aportada por el usuario, compartida por las preguntas 11–13.
    lectura = edicion['lecturas'][0]
    lectura['figuras'] = [{'imagen':'lectura-1-infografia-legible.png', 'descripcion':'Cómo detectar noticias falsas: infografía compartida por las preguntas 11, 12 y 13.'}]
    lectura.pop('pasos', None)
    edicion['etapa'] = 'Figuras SVG y fórmulas MathML nativas'
    ruta.write_text(json.dumps(edicion, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print('14 esquemas SVG, infografía accesible y fórmulas estructuradas; fecha de la 64 corregida.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pdf', type=Path)
    refinar(parser.parse_args().pdf)
