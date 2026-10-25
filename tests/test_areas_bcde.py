"""Comprueba contenido y separación de claves sin Flask ni PostgreSQL."""

import json
import math
import unittest
from pathlib import Path

from scripts.generar_areas_bcde import matematicas


RAIZ = Path(__file__).resolve().parents[1]


class TestAreasBCDE(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.privados = {}
        cls.publicos = {}
        for area in 'BCDE':
            cls.privados[area] = json.loads((RAIZ / f'data/examenes/area_{area.lower()}_practica.json').read_text(encoding='utf-8'))
            cls.publicos[area] = json.loads((RAIZ / f'static/practica/area_{area.lower()}.json').read_text(encoding='utf-8'))

    def test_cien_preguntas_por_area_con_clave_unica_y_explicacion(self):
        for area, datos in self.privados.items():
            with self.subTest(area=area):
                self.assertEqual([q['id'] for q in datos['preguntas']], list(range(1,101)))
                for q in datos['preguntas']:
                    self.assertTrue(q['enunciado'])
                    self.assertEqual(set(q['opciones']), set('ABCDE'))
                    self.assertEqual(len(set(q['opciones'].values())), 5, q['id'])
                    self.assertIn(q['correcta'], q['opciones'])
                    self.assertTrue(q['explicacion'])

    def test_datos_publicos_coinciden_y_excluyen_claves_recursivamente(self):
        def revisar(valor):
            if isinstance(valor, dict):
                self.assertFalse(set(valor) & {'correcta','explicacion','alternativas_coincidentes'})
                for v in valor.values():
                    revisar(v)
            elif isinstance(valor, list):
                for v in valor:
                    revisar(v)
        for area in 'BCDE':
            publico = self.publicos[area]
            revisar(publico)
            esperado = [{k:v for k,v in q.items() if k not in ('correcta','explicacion')} for q in self.privados[area]['preguntas']]
            self.assertEqual(publico['preguntas'], esperado)

    def test_tres_lecturas_diez_preguntas_y_cero_imagenes_en_hv(self):
        textos = set()
        for area, datos in self.publicos.items():
            self.assertEqual(len(datos['lecturas']), 3)
            self.assertEqual([n for l in datos['lecturas'] for n in l['preguntas']], list(range(11,21)))
            ids = {l['id'] for l in datos['lecturas']}
            for lectura in datos['lecturas']:
                self.assertEqual(lectura['figuras'], [])
                self.assertGreaterEqual(len(lectura['bloques'][0]['parrafos']), 2)
                texto = ' '.join(lectura['bloques'][0]['parrafos'])
                self.assertNotIn(texto, textos)
                textos.add(texto)
            for q in datos['preguntas'][10:20]:
                self.assertEqual(q['curso'], 'HV')
                self.assertIn(q['lectura_id'], ids)
                self.assertFalse(set(q) & {'imagen','imagenes','figura','figuras'})
        self.assertEqual(len(textos), 12)

    def test_diecinueve_cursos_cobertura_unica_y_figuras_fuera_de_hv(self):
        for datos in self.publicos.values():
            self.assertEqual(len(datos['grupos']), 19)
            self.assertEqual([n for g in datos['grupos'] for n in g['preguntas']], list(range(1,101)))
            figuras = [q for q in datos['preguntas'] if q.get('figura')]
            self.assertTrue(figuras)
            for q in figuras:
                self.assertEqual(q['curso'], 'Geometría')
                self.assertIn(q['figura'], ('triangulo', 'rectangulo'))

    def test_soluciones_numericas_con_calculo_independiente(self):
        for area in 'BCDE':
            k = 'BCDE'.index(area) + 1
            for indice, q in enumerate(matematicas(area)):
                if indice < 10:
                    i = indice + 1
                    n = 2*i+k
                    esperado = 6*n if i <= 3 else 2*n+3 if i <= 6 else math.comb(n,2) if i <= 8 else math.perm(n,2)
                elif indice < 18:
                    i = indice - 9
                    n = 10+2*i+k
                    esperado = (10*n)*80//100 if i % 2 else 4*(n+2) - ((n-4)+n+(n+4))
                elif indice < 26:
                    i = indice-17
                    n = 3*i+k
                    esperado = (4*n-n)//3 if i % 2 else (2*n+1)**2-2*n*(n+1)
                elif indice < 34:
                    i = indice-25
                    n = i+k+2
                    esperado = round(math.hypot(3*n,4*n)) if i % 2 else n*(n+3)
                else:
                    i = indice-33
                    n = i+k+2
                    theta = math.atan2(3*n,4*n)
                    razones = [math.sin(theta),math.cos(theta),math.tan(theta),1/math.tan(theta),1/math.cos(theta),1/math.sin(theta)]
                    factores = [10*n,10*n,4*n,3*n,4*n,3*n]
                    esperado = round(factores[i-1]*razones[i-1])
                self.assertEqual(q['opciones'][q['correcta']], str(esperado), (area, indice))


if __name__ == '__main__':
    unittest.main()
