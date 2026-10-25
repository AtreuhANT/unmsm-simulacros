"""Contenido activo, material visual y puntuación de los cinco bancos."""

import json
import unittest
from pathlib import Path

from config import Config
from utils.preguntas import cargar_preguntas_area, calcular_puntaje, sanitizar_preguntas_para_cliente


RAIZ = Path(__file__).resolve().parents[1]


class TestBancosActivos(unittest.TestCase):
    def test_cinco_bancos_de_cien_preguntas_y_puntaje_maximo(self):
        self.assertEqual(Config.DURACION_EXAMEN_MINUTOS,180)
        for area in 'ABCDE':
            with self.subTest(area=area):
                preguntas=cargar_preguntas_area(area)
                self.assertEqual([q['id'] for q in preguntas],list(range(1,101)))
                respuestas={str(q['id']):q['correcta'] for q in preguntas}
                calculo=calcular_puntaje(respuestas,preguntas)
                self.assertEqual((calculo['total'],calculo['correctas'],calculo['puntaje']),(100,100,2000))
                self.assertEqual(len(cargar_preguntas_area(area,historico=True)),10)

    def test_lecturas_figuras_y_formulas_llegan_sin_claves(self):
        for area in 'ABCDE':
            publico=sanitizar_preguntas_para_cliente(cargar_preguntas_area(area))
            texto=json.dumps(publico)
            self.assertNotIn('"correcta"',texto)
            self.assertNotIn('"explicacion"',texto)
            hv=publico[10:20]
            self.assertEqual(len({q['lectura']['id'] for q in hv}),3)
            if area != 'A':
                self.assertTrue(all(not q['lectura']['figuras'] for q in hv))
                self.assertTrue(any(q.get('figura') for q in publico))
            else:
                self.assertTrue(publico[37]['enunciado_rico'])
                self.assertEqual(len(publico[89]['tabla']['filas']),6)
                self.assertTrue(publico[90]['texto_despues_figura'])
                for q in publico:
                    for figura in q.get('figuras',[]) + q.get('lectura',{}).get('figuras',[]):
                        if figura.get('imagen'):
                            self.assertTrue((RAIZ/'static'/q['base_recursos']/figura['imagen']).is_file())


if __name__=='__main__':
    unittest.main()
