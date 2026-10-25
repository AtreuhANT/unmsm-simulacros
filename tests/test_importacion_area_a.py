"""Verificaciones del banco importado sin Flask, configuración ni base de datos."""

import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]


class TestImportacionAreaA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.publico = json.loads((RAIZ / 'static/importaciones/unmsm-2026-i-a/datos.json').read_text(encoding='utf-8'))
        cls.privado = json.loads((RAIZ / 'data/examenes/area_a_2026_i_revision.json').read_text(encoding='utf-8'))

    def test_cien_preguntas_sin_huecos_ni_duplicados(self):
        for datos in (self.publico, self.privado):
            self.assertEqual([q['id'] for q in datos['preguntas']], list(range(1, 101)))

    def test_claves_y_justificaciones_no_publicadas(self):
        texto = json.dumps(self.publico)
        for campo in ('correcta', 'explicacion', 'alternativas_coincidentes'):
            self.assertNotIn(f'"{campo}"', texto)
        js = (RAIZ / 'static/importaciones/unmsm-2026-i-a/datos.js').read_text(encoding='utf-8')
        datos_js = json.loads(js.removeprefix('window.EXAMEN_IMPORTADO = ').strip().removesuffix(';'))
        self.assertEqual(datos_js, self.publico)

    def test_originales_con_opciones_clave_y_justificacion(self):
        for pregunta in self.privado['preguntas'][:10]:
            self.assertEqual(set(pregunta['opciones']), set('ABCDE'))
            self.assertIn(pregunta['correcta'], pregunta['opciones'])
            self.assertTrue(pregunta['explicacion'])
            self.assertEqual(pregunta['origen'], 'Creación original para práctica')

    def test_imagenes_y_continuaciones_existentes(self):
        carpeta = RAIZ / 'static/importaciones/unmsm-2026-i-a'
        for pregunta in self.publico['preguntas'][10:]:
            for imagen in pregunta['imagenes']:
                self.assertTrue((carpeta / imagen).is_file(), imagen)

    def test_desfase_y_correcciones_acordadas(self):
        for pregunta in self.privado['preguntas'][10:]:
            numero = pregunta['id']
            self.assertEqual(pregunta['numero_respuesta_pdf'], numero if numero <= 20 else numero + 1)
            self.assertIn(pregunta['correcta'], 'ABCDE')
        for datos in (self.publico, self.privado):
            self.assertEqual(datos['preguntas'][46]['opciones']['D'], 'sé - mas - sí - mí')
            self.assertEqual(datos['preguntas'][70]['opciones']['B'], 'El efecto invernadero')
        for numero, clave in ((47, 'D'), (71, 'B')):
            pregunta = self.privado['preguntas'][numero - 1]
            self.assertEqual(pregunta['correcta'], clave)
            self.assertEqual(pregunta['estado_clave'], 'corregida')
            self.assertNotIn('alternativas_coincidentes', pregunta)
        self.assertEqual(self.privado['pendientes_revision'], [])
        self.assertTrue(self.privado['apto_calificacion'])

    def test_cursos_cubren_cien_preguntas_una_sola_vez(self):
        numeros = [n for grupo in self.publico['grupos'] for n in grupo['preguntas']]
        self.assertEqual(numeros, list(range(1, 101)))
        hlm = next(g for g in self.publico['grupos'] if g['nombre'] == 'H.L.M.')
        self.assertEqual(hlm['preguntas'], list(range(21, 31)))
        self.assertEqual(self.publico['grupos'][-1]['preguntas'], list(range(93, 101)))

    def test_hv_textual_comparte_tres_lecturas(self):
        lecturas = {l['id']: l for l in self.publico['lecturas']}
        self.assertEqual([l['preguntas'] for l in lecturas.values()],
                         [[11, 12, 13], [14, 15, 16, 17], [18, 19, 20]])
        for pregunta in self.publico['preguntas'][10:20]:
            self.assertEqual(pregunta['formato'], 'texto')
            self.assertEqual(set(pregunta['opciones']), set('ABCDE'))
            self.assertIn(pregunta['id'], lecturas[pregunta['lectura_id']]['preguntas'])
            self.assertNotIn('Texto A', pregunta['opciones']['E'])
        self.assertTrue(self.publico['preguntas'][17]['opciones']['E'].endswith('employment rates'))
        self.assertIn('\n\nIII.', self.publico['preguntas'][15]['enunciado'])
        self.assertEqual(len(lecturas['hv-2']['bloques']), 2)

    def test_figura_de_lectura_existe_y_no_hay_capturas_en_textos(self):
        carpeta = RAIZ / 'static/importaciones/unmsm-2026-i-a'
        figuras = [f for l in self.publico['lecturas'] for f in l['figuras']]
        self.assertEqual(len(figuras), 1)
        self.assertTrue((carpeta / figuras[0]['imagen']).is_file())
        self.assertNotIn('pasos', self.publico['lecturas'][0])
        for lectura in self.publico['lecturas']:
            self.assertTrue(lectura['bloques'][0]['parrafos'])
            self.assertNotIn('PREGUNTA N.', json.dumps(lectura['bloques']))

    def test_numeral_34_y_precio_41_no_se_confunden_con_formulas(self):
        preguntas = {q['id']: q for q in self.publico['preguntas']}
        self.assertIn(r'$\overline{\text{aa0b5}}$', preguntas[34]['enunciado_rico'])
        self.assertIn(r'\$10 por metro cuadrado', preguntas[41]['enunciado_rico'])
        self.assertIn(r'$\pi=3,14$', preguntas[41]['enunciado_rico'])

    def test_todo_el_banco_tiene_enunciado_y_alternativas_textuales(self):
        for pregunta in self.publico['preguntas']:
            self.assertTrue(pregunta['enunciado'], pregunta['id'])
            self.assertEqual(set(pregunta['opciones']), set('ABCDE'))
            self.assertTrue(all(pregunta['opciones'].values()))
            if pregunta['id'] >= 11:
                self.assertEqual(pregunta['formato'], 'texto')
            texto = pregunta['enunciado'] + ''.join(pregunta['opciones'].values())
            self.assertFalse(any(0xE000 <= ord(c) <= 0xF8FF for c in texto), pregunta['id'])

    def test_figuras_independientes_y_cuadricula_vectorial(self):
        esperadas = {21,24,26,27,28,29,30,35,36,37,41,81,83,84,91}
        con_figuras = {q['id'] for q in self.publico['preguntas'] if q.get('figuras')}
        self.assertEqual(con_figuras, esperadas)
        carpeta = RAIZ / 'static/importaciones/unmsm-2026-i-a'
        for pregunta in self.publico['preguntas']:
            for figura in pregunta.get('figuras', []):
                if pregunta['id'] == 24:
                    self.assertEqual(figura['tipo'], 'cuadricula-borde')
                else:
                    self.assertTrue((carpeta / figura['imagen']).is_file())

    def test_tabla_y_continuacion_de_vitaminas_completas(self):
        self.assertEqual(len(self.publico['preguntas'][89]['tabla']['filas']), 6)
        vitaminas = self.publico['preguntas'][90]
        self.assertNotIn('CH3', vitaminas['enunciado'])
        self.assertIn('IV. La vitamina D', vitaminas['texto_despues_figura'])
        self.assertIn('µT', self.publico['preguntas'][83]['opciones']['B'])
        self.assertIn('10⁻⁵', self.publico['preguntas'][83]['enunciado'])

    def test_vectores_con_datos_sin_raster_ni_capa_editorial(self):
        carpeta = RAIZ / 'static/importaciones/unmsm-2026-i-a'
        ns = '{http://www.w3.org/2000/svg}'
        for pregunta in self.publico['preguntas']:
            for figura in pregunta.get('figuras', []):
                if pregunta['id'] == 24:
                    continue
                self.assertTrue(figura['imagen'].endswith('.svg'))
                svg = (carpeta / figura['imagen']).read_text(encoding='utf-8')
                raiz = ET.fromstring(svg)
                self.assertFalse(list(raiz.iter(ns+'image')))
                self.assertNotIn('#d1e4f1', svg)
                self.assertNotIn('data:image', svg)
        domino = ET.parse(carpeta / 'figura-021.svg').getroot()
        self.assertEqual(len(list(domino.iter(ns+'circle'))), 26)
        moleculas = ET.parse(carpeta / 'figura-091.svg').getroot()
        etiquetas = ''.join(moleculas.itertext())
        for nombre in ('Retinol', 'Tiamina', 'Ácido ascórbico'):
            self.assertIn(nombre, etiquetas)

    def test_anotacion_matematica_y_fecha_64(self):
        q38 = self.publico['preguntas'][37]
        self.assertIn(r'\frac{z_1}{z_2}', q38['enunciado_rico'])
        self.assertIn(r'\overline{z_1}', q38['enunciado_rico'])
        q84 = self.publico['preguntas'][83]
        self.assertIn(r'\vec{B}', q84['enunciado_rico'])
        self.assertIn(r'10^{-5}', q84['enunciado_rico'])
        self.assertIn('2500 a. C. – 100 d. C.', self.publico['preguntas'][63]['enunciado'])


if __name__ == '__main__':
    unittest.main()
