import unittest
import os
import sys

# Agregar la raíz del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.preguntas import (
    calcular_puntaje, cargar_preguntas_area, sanitizar_preguntas_para_cliente, AREAS_UNMSM
)

class TestPuntuacionUNMSM(unittest.TestCase):
    
    def setUp(self):
        # Preguntas ficticias de prueba
        self.preguntas_mock = [
            {'id': 1, 'seccion': 'RV', 'enunciado': 'P1', 'opciones': {'A': 'a', 'B': 'b'}, 'correcta': 'A'},
            {'id': 2, 'seccion': 'RM', 'enunciado': 'P2', 'opciones': {'A': 'a', 'B': 'b'}, 'correcta': 'B'},
            {'id': 3, 'seccion': 'BIO', 'enunciado': 'P3', 'opciones': {'A': 'a', 'B': 'b'}, 'correcta': 'C'},
            {'id': 4, 'seccion': 'FIS', 'enunciado': 'P4', 'opciones': {'A': 'a', 'B': 'b'}, 'correcta': 'D'},
        ]

    def test_todas_correctas(self):
        respuestas = {'1': 'A', '2': 'B', '3': 'C', '4': 'D'}
        res = calcular_puntaje(respuestas, self.preguntas_mock)
        self.assertEqual(res['correctas'], 4)
        self.assertEqual(res['incorrectas'], 0)
        self.assertEqual(res['blanco'], 0)
        self.assertEqual(res['puntaje'], 80.0)

    def test_todas_incorrectas_no_negativo(self):
        # 4 incorrectas darían 4 * -1.125 = -4.5. La regla UNMSM exige mínimo 0.0.
        respuestas = {'1': 'B', '2': 'A', '3': 'A', '4': 'A'}
        res = calcular_puntaje(respuestas, self.preguntas_mock)
        self.assertEqual(res['correctas'], 0)
        self.assertEqual(res['incorrectas'], 4)
        self.assertEqual(res['blanco'], 0)
        self.assertEqual(res['puntaje_bruto'], -4.5)
        self.assertEqual(res['puntaje'], 0.0)

    def test_mixto_correctas_incorrectas_blanco(self):
        # 2 correctas (+40.0), 1 incorrecta (-1.125), 1 en blanco (0.0)
        respuestas = {'1': 'A', '2': 'B', '3': 'A', '4': ''}
        res = calcular_puntaje(respuestas, self.preguntas_mock)
        self.assertEqual(res['correctas'], 2)
        self.assertEqual(res['incorrectas'], 1)
        self.assertEqual(res['blanco'], 1)
        self.assertAlmostEqual(res['puntaje'], 38.875, places=3)

    def test_todas_en_blanco(self):
        respuestas = {}
        res = calcular_puntaje(respuestas, self.preguntas_mock)
        self.assertEqual(res['correctas'], 0)
        self.assertEqual(res['incorrectas'], 0)
        self.assertEqual(res['blanco'], 4)
        self.assertEqual(res['puntaje'], 0.0)

    def test_carga_examenes_todas_las_areas(self):
        for area in ['A', 'B', 'C', 'D', 'E']:
            preguntas = cargar_preguntas_area(area)
            self.assertGreater(len(preguntas), 0, f"El área {area} no cargó preguntas.")
            self.assertIn(area, AREAS_UNMSM)
            for q in preguntas:
                self.assertIn('id', q)
                self.assertIn('enunciado', q)
                self.assertIn('opciones', q)
                self.assertIn('correcta', q)

    def test_sanitizar_preguntas_seguridad_cliente(self):
        preguntas = cargar_preguntas_area('A')
        sanitizadas = sanitizar_preguntas_para_cliente(preguntas)
        for q in sanitizadas:
            self.assertNotIn('correcta', q, "FALLA DE SEGURIDAD: La clave correcta no debe enviarse al cliente.")
            self.assertNotIn('explicacion', q, "FALLA DE SEGURIDAD: La explicación no debe enviarse al cliente.")
            self.assertIn('id', q)
            self.assertIn('enunciado', q)
            self.assertIn('opciones', q)

if __name__ == '__main__':
    unittest.main()
