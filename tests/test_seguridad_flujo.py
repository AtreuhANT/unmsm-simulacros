import unittest
import json
import uuid
import time
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.database import init_db
from models.usuario import crear_usuario, obtener_usuario_por_dni
from models.resultado import guardar_resultado, obtener_resultado_por_token, obtener_ranking

class TestSeguridadYFlujo(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.app = create_app('development')
        cls.app.config['TESTING'] = True
        cls.app.config['WTF_CSRF_ENABLED'] = False
        cls.client = cls.app.test_client()
        with cls.app.app_context():
            init_db()

    def test_01_registro_y_login_postulante(self):
        dni_test = f"88{int(time.time()) % 1000000:06d}"
        vectores_mock = [[0.1] * 128, [0.12] * 128] # Simulación de 2 descriptores de 128 floats
        
        # 1. Registro sin cámara con contraseña personalizada
        clave_segura = 'password_segura_123'
        res_reg = self.client.post('/register', data={
            'nombre': 'Carlos',
            'apellido': 'Mendoza',
            'dni': dni_test,
            'area': 'C',
            'carrera': 'Ingeniería de Sistemas',
            'password': clave_segura,
            'password_confirm': clave_segura
        }, follow_redirects=True)
        
        self.assertEqual(res_reg.status_code, 200)

        # 2. Login con DNI y contraseña elegida
        res_login = self.client.post('/login', data={
            'dni': dni_test,
            'password': clave_segura
        }, follow_redirects=True)
        
        self.assertEqual(res_login.status_code, 200)
        self.assertIn(b'Hola, Carlos Mendoza', res_login.data)

    def test_02_seguridad_temporal_e_idempotencia(self):
        dni_test = f"77{int(time.time()) % 1000000:06d}"
        vectores_mock = [[0.05] * 128]
        
        user = crear_usuario('Ana', 'Ramos', dni_test, dni_test, 'Medicina Humana', 'A', vectores_mock)
        user_id = user['id']
        token_uuid = str(uuid.uuid4())

        # 1. Guardar resultado legítimo
        res1 = guardar_resultado(
            usuario_id=user_id,
            area='A',
            puntaje=160.0,
            correctas=8,
            incorrectas=0,
            blanco=2,
            tiempo_segundos=1500,
            token_sesion=token_uuid,
            estado='COMPLETADO'
        )
        self.assertIsNotNone(res1)
        self.assertEqual(res1['puntaje'], 160.0)

        # 2. Reintento con el mismo token_sesion (Anti-Replay / Idempotencia)
        res2 = guardar_resultado(
            usuario_id=user_id,
            area='A',
            puntaje=200.0, # Intento de alterar nota
            correctas=10,
            incorrectas=0,
            blanco=0,
            tiempo_segundos=800,
            token_sesion=token_uuid,
            estado='COMPLETADO'
        )
        # Debe devolver el registro existente original con 160.0, no el alterado
        self.assertEqual(res2['id'], res1['id'])
        self.assertEqual(res2['puntaje'], 160.0)

    def test_03_anulacion_por_falta_grave(self):
        dni_test = f"66{int(time.time()) % 1000000:06d}"
        vectores_mock = [[0.2] * 128]
        user = crear_usuario('Pedro', 'Gomez', dni_test, dni_test, 'Derecho', 'E', vectores_mock)
        token_uuid = str(uuid.uuid4())

        res_anulado = guardar_resultado(
            usuario_id=user['id'],
            area='E',
            puntaje=0.0,
            correctas=5,
            incorrectas=2,
            blanco=3,
            tiempo_segundos=600,
            token_sesion=token_uuid,
            estado='ANULADO',
            motivo_anulacion='Detección sostenida de múltiples personas en cámara (>10 segundos)'
        )
        self.assertEqual(res_anulado['estado'], 'ANULADO')
        self.assertEqual(res_anulado['puntaje'], 0.0)
        self.assertIn('múltiples personas', res_anulado['motivo_anulacion'])

    def test_04_ranking_desempate_unmsm(self):
        # Desempate: A igual puntaje, gana el de menor tiempo
        dni_a = f"51{int(time.time()) % 1000000:06d}"
        dni_b = f"52{int(time.time()) % 1000000:06d}"
        
        user_a = crear_usuario('AlumnoRapido', 'Test', dni_a, dni_a, 'Química', 'B', [[0.1]*128])
        user_b = crear_usuario('AlumnoLento', 'Test', dni_b, dni_b, 'Física', 'B', [[0.1]*128])
        
        # Mismo puntaje (1990.0), AlumnoRapido tardó 500s, AlumnoLento tardó 900s
        guardar_resultado(user_a['id'], 'B', 1990.0, 5, 0, 5, 500, str(uuid.uuid4()), 'COMPLETADO')
        guardar_resultado(user_b['id'], 'B', 1990.0, 5, 0, 5, 900, str(uuid.uuid4()), 'COMPLETADO')

        ranking_b = obtener_ranking(area='B', limite=50)
        
        # Buscar las posiciones de user_a y user_b
        pos_a = next(i for i, r in enumerate(ranking_b) if r['dni'] == dni_a)
        pos_b = next(i for i, r in enumerate(ranking_b) if r['dni'] == dni_b)
        
        self.assertLess(pos_a, pos_b, "CRITERIO UNMSM FALLIDO: El alumno con menor tiempo debe ubicarse antes en el ranking.")

if __name__ == '__main__':
    unittest.main()
