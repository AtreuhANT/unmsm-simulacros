"""Transcribe el banco específico del área A y separa sus figuras del PDF.

Conserva claves y numeración. Las correcciones son de presentación, no soluciones.
"""

import argparse
import json
import re
from pathlib import Path

import pymupdf


RAIZ = Path(__file__).resolve().parents[1]
CARPETA = RAIZ / 'static/importaciones/unmsm-2026-i-a'

# Página (1-based) y región de la figura, sin enunciado ni alternativas.
FIGURAS = {
    21:(6,(235,422,423,489)), 26:(8,(34,244,222,435)),
    27:(8,(235,144,423,220)), 28:(8,(235,362,423,438)),
    29:(9,(48,154,236,261)), 30:(9,(249,143,437,233)),
    35:(10,(235,279,423,431)), 36:(11,(48,198,236,352)),
    37:(11,(48,479,236,574)), 41:(12,(34,290,222,401)),
    81:(20,(34,190,222,308)), 83:(20,(235,44,423,180)),
    84:(20,(235,416,423,514)), 91:(22,(235,285,423,420)),
}


def limpiar(texto: str) -> str:
    texto = texto.replace('\xad\n', '').replace('\xad', '').replace('\x08', '')
    texto = re.sub(r'\s+', ' ', texto).strip()
    texto = re.sub(r' (I{1,3}V?|IV|[a-d]|•)\.?(?= )',
                   lambda m: '\n\n' + m[0].strip(), texto) if '•' in texto else texto
    texto = re.sub(r' (IV|III|II|I|[a-d])\. ', r'\n\n\1. ', texto)
    return texto


def convertir(pdf: Path) -> None:
    documento = pymupdf.open(pdf)
    datos = json.loads((CARPETA / 'datos.json').read_text(encoding='utf-8'))
    edicion_path = RAIZ / 'data/examenes/edicion_area_a.json'
    edicion = json.loads(edicion_path.read_text(encoding='utf-8'))
    editadas = {q['id']:q for q in edicion['preguntas']}
    for pregunta in datos['preguntas']:
        numero = pregunta['id']
        if numero < 21:
            continue
        texto = pregunta['texto'].split('\n', 1)[1]
        # La 91 incluye la letra A dentro del dibujo; usar el último A) real.
        inicio = texto.rfind('A)')
        if numero == 50:
            inicio = re.search(r'\nA\s+expositivo', texto).start()
            texto = texto[:inicio] + re.sub(r'^\s*A\s+', 'A) ', texto[inicio:])
        cuerpo, alternativas = texto[:inicio], texto[inicio:]
        partes = re.split(r'([A-E])\)\s*', alternativas)
        opciones = {partes[i]:limpiar(partes[i+1]) for i in range(1,len(partes),2)}
        assert list(opciones) == list('ABCDE'), numero
        opciones['E'] = re.sub(r'\s+(Geometría|Álgebra|Trigonometría|Psicología|Historia del Perú|Historia Universal|Geografía|Filosofía|Química|Biología)$', '', opciones['E'])
        # Separar etiquetas y datos de figuras, que se mantienen en el recorte.
        if numero == 26: cuerpo = cuerpo.split('y así sucesivamente.')[0] + 'y así sucesivamente.'
        if numero == 28: cuerpo = cuerpo.split('latas que tumbó?')[0] + 'latas que tumbó?'
        if numero == 29: cuerpo = cuerpo.split('\nM\n')[0]
        if numero == 30: cuerpo = cuerpo.split('L (eje de simetría)')[0]
        if numero == 35: cuerpo = cuerpo.split('\nB\n')[0]
        if numero == 36: cuerpo = cuerpo.split('\nA\n')[0]
        if numero == 37: cuerpo = cuerpo.split('\nA\n')[0]
        if numero == 41: cuerpo = cuerpo.split('\nO\n')[0]
        if numero == 81: cuerpo = cuerpo.split('\nB\n')[0]
        if numero == 83: cuerpo = cuerpo.split('\nV\n')[0]
        if numero == 84: cuerpo = cuerpo.split('\na\n')[0]
        if numero == 91:
            cuerpo = cuerpo.split('\nOH\n')[0] + '\n\n' + cuerpo.split('Respecto de lo señalado,',1)[1]
            cuerpo = cuerpo.replace('\n\n determine', '\n\nRespecto de lo señalado, determine')
        nueva = {'id':numero, 'formato':'texto', 'enunciado':limpiar(cuerpo), 'opciones':opciones, 'figuras':[]}
        if numero in FIGURAS:
            pagina, region = FIGURAS[numero]
            nombre = f'figura-{numero:03}.png'
            documento[pagina-1].get_pixmap(matrix=pymupdf.Matrix(3,3), clip=pymupdf.Rect(region)).save(str(CARPETA / nombre))
            nueva['figuras'] = [{'imagen':nombre, 'descripcion':f'Figura original de la pregunta {numero}'}]
        if numero == 24:
            nueva['figuras'] = [{'tipo':'cuadricula-borde', 'descripcion':'Cuadrado con cinco casillas por lado y dieciséis casillas en su borde.'}]
        editadas[numero] = nueva

    def enunciado(numero: int, valor: str) -> None:
        editadas[numero]['enunciado'] = valor

    def opciones(numero: int, valores: list[str]) -> None:
        editadas[numero]['opciones'] = dict(zip('ABCDE', valores, strict=True))

    enunciado(34, editadas[34]['enunciado'].replace('aa0b5', 'a̅a̅0̅b̅5̅'))
    editadas[49]['subrayados'] = ['lisa', 'peón', 'raya', 'servía']
    enunciado(35, 'La figura representa una región de cultivo que tiene la forma de un círculo dividido en zonas de sembríos. Si la medida del arco BC es 50°, m∠BNC = 40° y O es circuncentro del triángulo ABC, halle la medida del ángulo AOC que forman los linderos AO y OC.')
    enunciado(36, 'La figura representa un adorno transparente en elaboración, que, inicialmente, parte de la forma de una esfera. Luego de retirar el segmento esférico inferior de altura HM, el adorno queda terminado y con una base. Si en una sección circular máxima de la esfera se inscribe una región triangular equilátera ABC de área 12√3 cm³ y HM = 1 cm, halle el volumen, en centímetros cúbicos, del sólido que fue retirado para terminar el adorno.\n\nNota: Considere O como centro de la esfera.')
    opciones(36, ['11π/2','11π/6','22π/3','11π/3','33π/2'])
    enunciado(37, 'La figura muestra parte de una estructura metálica en la que AB = 60 cm, BC = 30√2 cm, AD = 30√3 cm y DC = 30 cm. Halle la medida del ángulo BAD que forman las varillas AB y AD.')
    enunciado(38, 'Dados los números complejos z₁ = 3 + 2i y z₂ = 4 + i, determine el valor de verdad (V o F) de las siguientes proposiciones:\n\nI. El producto de ambos es z₁ · z₂ = 10 + 11i.\n\nII. El módulo de la diferencia de ellos es |z₂ − z₁| = |−1 − i| = √2.\n\nIII. La suma de sus conjugados es z̅₁ + z̅₂ = −7 − 3i.\n\nIV. El cociente de ambos es z₁/z₂ = 3/4 + 2i.')
    enunciado(39, 'En un día de descanso, Luis Alberto se sometió a una prueba para registrar la metabolización del azúcar en su sangre, la que se llevó a cabo en un intervalo de tiempo de seis a doce horas.\n\nSe observó que la cantidad de azúcar en la sangre (medida en mg/dL) podía ser modelada en función del tiempo t (medido en horas) por:\n\nF(t) = −0,5t² + 6t + 104, t ∈ [6; 12].\n\nDetermine la disminución de azúcar en la sangre, en mg/dL, que experimentó Luis Alberto, exactamente, cuatro horas después de iniciada la prueba.')
    enunciado(41, 'Juan Carlos le regaló a su hija un terreno, el cual tiene forma de sector circular con radio r = 20√7 m, tal como se muestra en la figura. Si Juan Carlos compró el terreno a razón de $10 por metro cuadrado, ¿cuántos dólares pagó en total?\n\nDato: π = 3,14.')
    enunciado(42, 'Un profesor de Matemática dijo a sus alumnos de la Escuela de Tecnología Médica que el precio, en soles, de un microscopio está dado por (40M + 1200), donde M es el valor que toma la función\n\nf(x) = (4 sec x − 2) / (1 − 4 sec² x), 2π/3 ≤ x ≤ 5π/4,\n\ncuando la sec(x) toma su máximo valor. Halle el valor, en soles, del microscopio.')
    enunciado(50, 'Ya aguijan a los caballos, ya les soltaron las [riendas.\nCuando salen de Vivar ven la corneja a la diestra,\npero al ir a entrar en Burgos la llevaban a su [izquierda.\nMovió Mio Cid los hombros y sacudió la cabeza:\n“¡Ánimo, Állvar Fáñez, ánimo, de nuestra tierra [nos echan,\npero cargados de honra hemos de volver a ella!”.\n\nEn los versos anteriores del Poema de Mio Cid se distinguen su carácter esencialmente heroico y la alusión a hechos pasados, lo cual enmarca al extracto citado en el género')
    enunciado(84, 'Una espira cuadrada de lados a = 10 cm rota en torno del eje z, que pasa por el centro de ella, con rapidez angular constante igual a ω = 1200 rad/s, como se muestra en la figura. En el espacio en el que se encuentra la espira existe un campo magnético B⃗ = 2 × 10⁻⁵ ĵ T. Teniendo en cuenta la situación anterior, halle el flujo magnético, en cualquier instante, sobre la espira. Considere que inicialmente el campo magnético es paralelo a la superficie de la espira.')
    opciones(83, ['(2√10 î − 10√2 ĵ) m/s','(2√2 î − 10√10 ĵ) m/s','(10√2 î − 2√10 ĵ) m/s','(2√10 î + 10√2 ĵ) m/s','(−2√10 î + 10√2 ĵ) m/s'])
    opciones(84, ['2,0 sen(1200t − π/2) µT · m²','0,2 cos(1200t + π/2) µT · m²','20 cos(1200t + π/4) µT · m²','2,0 cos(1200t − π/2) µT · m²','20 sen(1200t − π/3) µT · m²'])
    for numero in (29,):
        enunciado(numero, editadas[numero]['enunciado'].replace('40p', '40π').replace('figura Determine','figura. Determine'))
        for letra, valor in editadas[numero]['opciones'].items():
            editadas[numero]['opciones'][letra] = valor.replace('p cm','π cm')
    enunciado(85, editadas[85]['enunciado'].replace('10–15','10⁻¹⁵').replace('108 m/s','10⁸ m/s'))
    enunciado(83, editadas[83]['enunciado'].replace('m/s2', 'm/s²'))
    enunciado(87, 'De acuerdo con el proceso de la potabilización del agua, relacione correctamente ambas columnas.\n\nProceso\nI. Represamiento de aguas naturales\nII. Sedimentación de arenas y arcillas\nIII. Desinfección inicial y final\nIV. Eliminación de partículas coloidales\n\nActividad/acción\na. Cl₂(g) + H₂O(ℓ) ↔ HOCl(ac) + H⁺ + Cl⁻\nb. Acción de la gravedad y mayor densidad\nc. Al₂(SO₄)₃ · 14H₂O; FeSO₄ · 7H₂O\nd. Desviación del agua de su canal natural')
    enunciado(88, 'Relacione adecuadamente cada ecuación química con su tipo de reacción.\n\nEcuación química\nI. KOH(ac) + HCl(ac) → KCl(ac) + H₂O(ℓ)\nII. CH₃CH₂CH₂Br(s) + CH₃OH(ℓ) → CH₃CH₂CH₂OH(ℓ) + CH₃Br(ℓ)\nIII. NaHCO₃ + calor → Na₂CO₃(ac) + CO₂(g) + H₂O(ℓ)\nIV. AgNO₃(ac) + HCl(ac) → HNO₃(ac) + AgCl(s)\n\nTipo de reacción\na. Endotérmica\nb. De sustitución\nc. De precipitación\nd. Neutralización')
    enunciado(89, 'Un estudiante del nivel secundario intenta diseñar un dispositivo eléctrico para obtener electricidad. Él dispone de los metales litio y níquel y de las soluciones 1 M de los iones de cada metal. Determine la notación de la celda que debe construir y el voltaje que produciría al realizar la correcta asociación.\n\nPotencial de reducción:\nLi⁺(ac) + e⁻ → Li⁰(s), ε = −3,05 V\nNi²⁺(ac) + 2e⁻ → Ni⁰(s), ε = −0,28 V')
    opciones(89, ['Li⁰(s) / Li⁺(ac) // Ni⁰(s) / Ni²⁺(ac) y +2,77 V','Li⁺(ac) / Li⁰(s) // Ni²⁺(ac) / Ni⁰(s) y +3,33 V','Ni²⁺(ac) / Ni⁰(s) // Li⁺(ac) / Li⁰(s) y −2,77 V','Ni²⁺(ac) / Ni⁰(s) // Li⁰(s) / Li⁺(ac) y +5,72 V','Li⁰(s) / Li⁺(ac) // Ni²⁺(ac) / Ni⁰(s) y +2,77 V'])
    cuerpo90 = editadas[90]['enunciado']
    editadas[90]['tabla'] = {
        'columnas':['Líquido','Fórmula molecular','Masa molar (g/mol)'],
        'filas':[['Acetona','CH₃−CO−CH₃','58'],['Propionaldehido','CH₃−CH₂−CHO','58'],['Etanol','CH₃−CH₂−OH','46'],['Ácido acético','CH₃−COOH','60'],['n-pentano','CH₃−CH₂−CH₂−CH₂−CH₃','72'],['isopentano','CH₃−CH(CH₃)−CH₂−CH₃','72']],
    }
    enunciado(90, 'En la siguiente tabla se muestran sustancias orgánicas con su fórmula molecular y masa molar.')
    editadas[90]['texto_despues_figura'] = 'De acuerdo con la tabla anterior,' + cuerpo90.split('De acuerdo con la tabla anterior,',1)[1]
    cuerpo91 = editadas[91]['enunciado']
    enunciado(91, cuerpo91.split('Respecto de lo señalado,')[0].strip())
    editadas[91]['texto_despues_figura'] = 'Respecto de lo señalado,' + cuerpo91.split('Respecto de lo señalado,',1)[1]
    enunciado(92, 'El mineral apatita es el fluorfosfato de calcio, Ca₅(PO₄)₃F, o el clorofosfato de calcio, Ca₅(PO₄)₃Cl; mientras que la hidroxiapatita es el Ca₅(PO₄)₃OH. Este último le confiere a los huesos y a los dientes la resistencia y dureza para cumplir sus acciones fisiológicas. Si se mezcla 65 g de apatita, con 80% de pureza, y 10 gramos de hidróxido de calcio, 100% puro, ¿cuál es la masa de hidroxiapatita que se obtiene, en gramos, si el rendimiento de la reacción fue 75%?\n\nConsidere la siguiente ecuación química:\nCa₅(PO₄)₃Cl(s) + Ca(OH)₂(ac) → Ca₅(PO₄)₃OH(s) + Ca(OH)Cl(ac)\n\nDatos: masa molar, g/mol: ₁H = 1; ₈O = 16; ₁₅P = 31; ₁₇Cl = 35,5; ₂₀Ca = 40.')
    edicion.update(etapa='Todas las preguntas en texto; figuras independientes y tabla HTML', preguntas=sorted(editadas.values(),key=lambda q:q['id']))
    edicion_path.write_text(json.dumps(edicion, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Preparadas preguntas 21–100 en texto, 14 figuras recortadas y una cuadrícula SVG.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pdf', type=Path)
    convertir(parser.parse_args().pdf)
