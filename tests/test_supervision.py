"""Pruebas HTTP exclusivas de una base PostgreSQL aislada de pruebas."""

import os
import unittest
import uuid
import io
import tempfile
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from PIL import Image

import psycopg2
from psycopg2.extensions import parse_dsn


def _validar_base_de_pruebas():
    dsn = os.environ.get('DATABASE_URL', '')
    partes = parse_dsn(dsn) if dsn else {}
    if (partes.get('dbname'), partes.get('host'), partes.get('port')) != (
        'unmsm_proctor_test', '127.0.0.1', '5432'
    ):
        raise RuntimeError('Se exige DATABASE_URL de la base aislada unmsm_proctor_test')
    with psycopg2.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute('SELECT current_database(), host(inet_server_addr()), inet_server_port()')
        if cur.fetchone() != ('unmsm_proctor_test', '127.0.0.1', 5432):
            raise RuntimeError('Identidad de base de pruebas no confirmada')


_validar_base_de_pruebas()  # Obligatorio antes de importar app: su importación inicializa el esquema.

from app import app  # noqa: E402
from models.database import get_db_cursor  # noqa: E402
from models.intento import crear_intento, iniciar_o_recuperar_intento_atomico, guardar_respuesta_incremental  # noqa: E402
from models.supervision import entregar_examen  # noqa: E402
import models.evidencia_celular as evidencia_celular  # noqa: E402
from utils.preguntas import cargar_preguntas_area  # noqa: E402


class TestSupervision(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        cls.client = app.test_client()

    def setUp(self):
        self.dni = str(uuid.uuid4().int)[:12]
        with get_db_cursor(commit=True) as cur:
            cur.execute(
                "INSERT INTO usuarios (nombre,apellido,dni,password_hash,carrera,area,es_admin) "
                "VALUES ('Alumno','Prueba',%s,'hash','Administracion','A',false) RETURNING id",
                (self.dni,),
            )
            self.uid = cur.fetchone()['id']
        self.intento = crear_intento(self.uid, 'A')
        with self.client.session_transaction() as sesion:
            sesion['usuario_id'] = self.uid
            sesion['es_admin'] = False
            sesion['csrf_examen'] = 'token-de-prueba'
        self.headers = {'X-CSRF-Token': 'token-de-prueba'}

    def test_tercera_salida_y_deduplicacion(self):
        url = '/api/intento/salida-foco'
        base = {'token_sesion': self.intento['token_sesion'], 'tipo': 'cambio_pestana'}
        uno = self.client.post(url, json={**base, 'id_cliente': 'episodio-1'}, headers=self.headers)
        self.assertEqual(uno.status_code, 200)
        self.assertEqual(uno.json['salidas'], 1)
        repetido = self.client.post(url, json={**base, 'id_cliente': 'episodio-1'}, headers=self.headers)
        self.assertEqual(repetido.json['salidas'], 1)
        self.client.post(url, json={**base, 'id_cliente': 'episodio-2'}, headers=self.headers)
        tercero = self.client.post(url, json={**base, 'id_cliente': 'episodio-3'}, headers=self.headers)
        self.assertTrue(tercero.json['cerrado'])
        self.assertIn('Tres salidas', tercero.json['motivo'])
        with get_db_cursor() as cur:
            cur.execute('SELECT estado, revision, puntaje FROM resultados WHERE token_sesion = %s',
                        (self.intento['token_sesion'],))
            resultado = cur.fetchone()
        self.assertEqual((resultado['estado'], resultado['revision'], resultado['puntaje']),
                         ('ANULADO', 'PENDIENTE', 0.0))
        with self.assertRaises(ValueError):
            guardar_respuesta_incremental(self.intento['id'], 1, 'A')

    def test_entrega_ignora_estado_puntaje_y_respuestas_cliente(self):
        pregunta = cargar_preguntas_area('A')[0]
        guardar_respuesta_incremental(self.intento['id'], pregunta['id'], pregunta['correcta'])
        response = self.client.post('/api/guardar-resultado', headers=self.headers, json={
            'token_sesion': self.intento['token_sesion'], 'area': 'E', 'estado': 'ANULADO',
            'motivo_anulacion': 'falso', 'tiempo_segundos': 0, 'respuestas': {},
        })
        self.assertEqual(response.status_code, 200)
        with get_db_cursor() as cur:
            cur.execute('SELECT area, estado, puntaje FROM resultados WHERE token_sesion = %s',
                        (self.intento['token_sesion'],))
            resultado = cur.fetchone()
        self.assertEqual(resultado['area'], 'A')
        self.assertEqual(resultado['estado'], 'COMPLETADO')
        self.assertEqual(resultado['puntaje'], 20.0)
        repetido = self.client.post('/api/guardar-resultado', headers=self.headers,
                                    json={'token_sesion': self.intento['token_sesion'], 'estado': 'ANULADO'})
        self.assertEqual(repetido.status_code, 200)
        self.assertEqual(repetido.json['resultado_id'], response.json['resultado_id'])

    def test_csrf_de_sancion(self):
        response = self.client.post('/api/intento/salida-foco', json={
            'token_sesion': self.intento['token_sesion'], 'tipo': 'cambio_pestana',
            'id_cliente': 'sin-csrf',
        })
        self.assertEqual(response.status_code, 403)

    def test_reto_ocular_no_confirmado_solo_pide_revision(self):
        payload = {'token_sesion': self.intento['token_sesion'], 'id_cliente': str(uuid.uuid4())}
        self.assertEqual(self.client.post('/api/intento/presencia-no-confirmada', json=payload).status_code, 403)
        respuesta = self.client.post('/api/intento/presencia-no-confirmada', json=payload, headers=self.headers)
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.json['revision_pendiente'])
        self.client.post('/api/intento/presencia-no-confirmada', json=payload, headers=self.headers)
        with get_db_cursor() as cur:
            cur.execute("SELECT estado_academico, estado_supervision FROM intentos WHERE id = %s", (self.intento['id'],))
            intento = cur.fetchone()
            cur.execute("SELECT count(*) AS total FROM eventos_monitoreo WHERE intento_id = %s "
                        "AND tipo = 'presencia_no_confirmada'", (self.intento['id'],))
            total = cur.fetchone()['total']
        self.assertEqual((intento['estado_academico'], intento['estado_supervision']),
                         ('EN_CURSO', 'PENDIENTE'))
        self.assertEqual(total, 1)
        cierre = entregar_examen(self.intento['token_sesion'], self.uid)
        with get_db_cursor() as cur:
            cur.execute('SELECT revision, motivo_anulacion FROM resultados WHERE id = %s', (cierre['id'],))
            resultado = cur.fetchone()
        self.assertEqual(resultado['revision'], 'PENDIENTE')
        self.assertIn('reto ocular', resultado['motivo_anulacion'])

    def test_pantalla_examen_entrega_csrf_y_detector_local(self):
        preparacion = self.client.get('/preparacion/A')
        self.assertEqual(preparacion.status_code, 200)
        with self.client.session_transaction() as sesion:
            csrf = sesion['csrf_preparacion']
        consentimiento = self.client.post('/api/intento/consentimiento-celular',
                                         headers={'X-CSRF-Token': csrf}, json={'acepta': True})
        self.assertEqual(consentimiento.status_code, 200)
        response = self.client.get('/examen/A')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'phone_monitor.js', response.data)
        self.assertIn(b'csrfToken:', response.data)

    def test_reloj_y_preguntas_comienzan_al_activar_examen(self):
        with get_db_cursor(commit=True) as cur:
            cur.execute("UPDATE intentos SET estado_academico = 'ENTREGADO' WHERE id = %s", (self.intento['id'],))
            cur.execute("UPDATE usuarios SET consentimiento_celular_version = 'celular-v2-fotos' WHERE id = %s",
                        (self.uid,))
        pantalla = self.client.get('/examen/A')
        self.assertEqual(pantalla.status_code, 200)
        self.assertNotIn(cargar_preguntas_area('A')[0]['enunciado'].encode(), pantalla.data)
        with get_db_cursor() as cur:
            cur.execute("SELECT count(*) AS total FROM intentos WHERE usuario_id = %s AND estado_academico = 'EN_CURSO'",
                        (self.uid,))
            self.assertEqual(cur.fetchone()['total'], 0)
        self.assertEqual(self.client.post('/api/intento/iniciar', json={'area': 'A'}).status_code, 403)
        with self.client.session_transaction() as sesion:
            headers_inicio = {'X-CSRF-Token': sesion['csrf_examen']}
        primero = self.client.post('/api/intento/iniciar', headers=headers_inicio,
                                   json={'area': 'A', 'duracion_minutos': 999})
        self.assertEqual(primero.status_code, 200)
        self.assertTrue(primero.json['preguntas'])
        self.assertEqual(primero.json['status'], 'iniciado')
        self.assertLessEqual(primero.json['segundos_restantes'], 60 * 60)
        repetido = self.client.post('/api/intento/iniciar', headers=headers_inicio, json={'area': 'A'})
        self.assertEqual(repetido.json['status'], 'recuperado')
        self.assertEqual(repetido.json['intento']['id'], primero.json['intento']['id'])

    def test_activacion_simultanea_conserva_un_solo_reloj(self):
        with get_db_cursor(commit=True) as cur:
            cur.execute("UPDATE intentos SET estado_academico = 'ENTREGADO' WHERE id = %s", (self.intento['id'],))
        with ThreadPoolExecutor(max_workers=2) as ejecutor:
            futuros = [ejecutor.submit(iniciar_o_recuperar_intento_atomico, self.uid, 'A', 60)
                       for _ in range(2)]
            inicios = [f.result(timeout=10) for f in futuros]
        self.assertEqual(inicios[0][0]['id'], inicios[1][0]['id'])
        self.assertEqual(sorted(nuevo for _, nuevo in inicios), [False, True])

    def test_entregas_simultaneas_son_idempotentes(self):
        with ThreadPoolExecutor(max_workers=2) as ejecutor:
            futuros = [ejecutor.submit(entregar_examen, self.intento['token_sesion'], self.uid)
                       for _ in range(2)]
            resultados = [futuro.result(timeout=10) for futuro in futuros]
        self.assertEqual(resultados[0]['id'], resultados[1]['id'])
        with get_db_cursor() as cur:
            cur.execute('SELECT count(*) AS total FROM resultados WHERE token_sesion = %s',
                        (self.intento['token_sesion'],))
            self.assertEqual(cur.fetchone()['total'], 1)

    def test_celular_sostenido_pasa_a_revision_sin_anulacion_automatica(self):
        with get_db_cursor(commit=True) as cur:
            cur.execute("UPDATE usuarios SET consentimiento_celular_version = 'celular-v2-fotos' WHERE id = %s",
                        (self.uid,))
            for numero, segundos in enumerate((10, 8, 6, 4, 2), start=1):
                cur.execute(
                    "INSERT INTO eventos_monitoreo "
                    "(usuario_id,intento_id,modulo,tipo,id_cliente,registrado_en) "
                    "VALUES (%s,%s,'object_detector','celular_detectado',%s, "
                    "CURRENT_TIMESTAMP - (%s * INTERVAL '1 second'))",
                    (self.uid, self.intento['id'], f'fixture-{numero}', segundos),
                )
        respuesta = self.client.post('/api/intento/celular', headers=self.headers, json={
            'token_sesion': self.intento['token_sesion'], 'id_cliente': 'observacion-final'
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.json['revision_pendiente'])
        entrega = self.client.post('/api/guardar-resultado', headers=self.headers,
                                   json={'token_sesion': self.intento['token_sesion']})
        self.assertEqual(entrega.status_code, 200)
        with get_db_cursor() as cur:
            cur.execute('SELECT estado, revision, motivo_anulacion FROM resultados WHERE id = %s',
                        (entrega.json['resultado_id'],))
            resultado = cur.fetchone()
        self.assertEqual((resultado['estado'], resultado['revision']), ('COMPLETADO', 'PENDIENTE'))
        self.assertIn('celular', resultado['motivo_anulacion'])
        with get_db_cursor(commit=True) as cur:
            cur.execute("INSERT INTO usuarios (nombre,apellido,dni,password_hash,carrera,area,es_admin) "
                        "VALUES ('Admin','Prueba',%s,'hash','Administracion','A',true) RETURNING id",
                        (str(uuid.uuid4().int)[:12],))
            admin_id = cur.fetchone()['id']
        with self.client.session_transaction() as sesion:
            sesion['usuario_id'] = admin_id
            sesion['es_admin'] = True
            sesion['csrf_revision'] = 'revision-celular'
        revision = self.client.post(f"/admin/revision/{entrega.json['resultado_id']}", data={
            'csrf_revision': 'revision-celular', 'decision': 'confirmar',
            'nota': 'Revisión humana del incidente documentado. <script>alert(1)</script>'
        })
        self.assertEqual(revision.status_code, 302)
        with get_db_cursor() as cur:
            cur.execute('SELECT estado, revision, puntaje FROM resultados WHERE id = %s',
                        (entrega.json['resultado_id'],))
            confirmado = cur.fetchone()
        self.assertEqual((confirmado['estado'], confirmado['revision'], confirmado['puntaje']),
                         ('ANULADO', 'ANULACION_CONFIRMADA', 0.0))
        with self.client.session_transaction() as sesion:
            sesion['usuario_id'] = self.uid
            sesion['es_admin'] = False
        vista_alumno = self.client.get(f"/resultado/{entrega.json['resultado_id']}")
        self.assertEqual(vista_alumno.status_code, 200)
        self.assertIn('Revisión humana del incidente documentado.'.encode(), vista_alumno.data)
        self.assertIn(b'&lt;script&gt;alert(1)&lt;/script&gt;', vista_alumno.data)
        self.assertNotIn(b'<script>alert(1)</script>', vista_alumno.data)
        self.assertIn('Anulación confirmada'.encode(), vista_alumno.data)
        self.assertNotIn('Examen anulado provisionalmente'.encode(), vista_alumno.data)

    def test_evidencia_fotografica_cifrada_y_solo_admin(self):
        with get_db_cursor(commit=True) as cur:
            cur.execute("UPDATE usuarios SET consentimiento_celular_version = 'celular-v2-fotos' WHERE id = %s",
                        (self.uid,))
        imagen = Image.new('RGB', (320, 240), 'blue')
        memoria = io.BytesIO()
        imagen.save(memoria, format='JPEG')
        foto = memoria.getvalue()
        episodio = str(uuid.uuid4())
        campos = {'token_sesion': self.intento['token_sesion'], 'episodio_id': episodio,
                  'segundo_objetivo': '1'}
        url = '/api/intento/evidencia-celular'
        with tempfile.TemporaryDirectory() as directorio, patch.object(evidencia_celular, 'DIRECTORIO',
                                                                       evidencia_celular.Path(directorio)):
            sin_evento = self.client.post(url, data={**campos, 'foto': (io.BytesIO(foto), 'foto.jpg')},
                                          headers=self.headers)
            self.assertEqual(sin_evento.status_code, 400)
            evento = self.client.post('/api/intento/celular', headers=self.headers,
                                      json={'token_sesion': self.intento['token_sesion'],
                                            'id_cliente': f'{episodio}:{uuid.uuid4()}'})
            self.assertEqual(evento.status_code, 200)
            prematura = self.client.post(url, data={**campos, 'segundo_objetivo': '10',
                                                    'foto': (io.BytesIO(foto), 'foto.jpg')},
                                         headers=self.headers)
            self.assertEqual(prematura.status_code, 400)
            sin_csrf = self.client.post(url, data={**campos, 'foto': (io.BytesIO(foto), 'foto.jpg')})
            self.assertEqual(sin_csrf.status_code, 403)
            corrupta = self.client.post(url, data={**campos, 'foto': (io.BytesIO(b'no-es-jpeg'), 'foto.jpg')},
                                        headers=self.headers)
            self.assertEqual(corrupta.status_code, 400)
            creada = self.client.post(url, data={**campos, 'foto': (io.BytesIO(foto), 'foto.jpg')},
                                      headers=self.headers)
            self.assertEqual(creada.status_code, 200)
            evidencia_id = creada.json['evidencia_id']
            repetida = self.client.post(url, data={**campos, 'foto': (io.BytesIO(foto), 'foto.jpg')},
                                        headers=self.headers)
            self.assertEqual(repetida.json['evidencia_id'], evidencia_id)
            archivos = list(evidencia_celular.DIRECTORIO.glob('*.bin'))
            self.assertEqual(len(archivos), 1)
            self.assertNotIn(foto[:20], archivos[0].read_bytes())
            ruta_admin = f'/admin/evidencia-celular/{evidencia_id}'
            alumno = self.client.get(ruta_admin)
            self.assertNotEqual(alumno.status_code, 200)
            resultado = entregar_examen(self.intento['token_sesion'], self.uid)
            informe_alumno = self.client.get(f"/resultado/{resultado['id']}")
            self.assertNotIn(b'Fotograf', informe_alumno.data)
            with get_db_cursor(commit=True) as cur:
                cur.execute("INSERT INTO usuarios (nombre,apellido,dni,password_hash,carrera,area,es_admin) "
                            "VALUES ('Admin','Prueba',%s,'hash','Administracion','A',true) RETURNING id",
                            (str(uuid.uuid4().int)[:12],))
                admin_id = cur.fetchone()['id']
            with self.client.session_transaction() as sesion:
                sesion['usuario_id'] = admin_id
                sesion['es_admin'] = True
            vista = self.client.get(f"/resultado/{resultado['id']}")
            self.assertIn(b'Fotograf', vista.data)
            respuesta = self.client.get(ruta_admin)
            self.assertEqual((respuesta.status_code, respuesta.mimetype), (200, 'image/jpeg'))
            self.assertEqual(respuesta.headers['Cache-Control'], 'no-store, private')
            self.assertTrue(respuesta.data.startswith(b'\xff\xd8'))
            with get_db_cursor(commit=True) as cur:
                cur.execute("UPDATE evidencias_celular SET expira_en = CURRENT_TIMESTAMP - INTERVAL '1 day' "
                            "WHERE id = %s", (evidencia_id,))
            self.assertEqual(self.client.get(ruta_admin).status_code, 404)

    def test_token_ajeno_rechazado(self):
        with self.client.session_transaction() as sesion:
            sesion['usuario_id'] = -1
        response = self.client.post('/api/intento/salida-foco', headers=self.headers, json={
            'token_sesion': self.intento['token_sesion'], 'tipo': 'cambio_pestana',
            'id_cliente': 'ajeno',
        })
        self.assertEqual(response.status_code, 404)

    def test_revision_humana_repone_y_audita(self):
        pregunta = cargar_preguntas_area('A')[0]
        guardar_respuesta_incremental(self.intento['id'], pregunta['id'], pregunta['correcta'])
        base = {'token_sesion': self.intento['token_sesion'], 'tipo': 'cambio_pestana'}
        for numero in range(1, 4):
            respuesta = self.client.post('/api/intento/salida-foco', headers=self.headers,
                                        json={**base, 'id_cliente': f'episodio-{numero}'})
        resultado_id = respuesta.json['resultado_id']
        with get_db_cursor(commit=True) as cur:
            cur.execute("INSERT INTO usuarios (nombre,apellido,dni,password_hash,carrera,area,es_admin) "
                        "VALUES ('Admin','Prueba',%s,'hash','Administracion','A',true) RETURNING id",
                        (str(uuid.uuid4().int)[:12],))
            admin_id = cur.fetchone()['id']
        with self.client.session_transaction() as sesion:
            sesion['usuario_id'] = admin_id
            sesion['es_admin'] = True
            sesion['csrf_revision'] = 'revision-de-prueba'
        respuesta = self.client.post(f'/admin/revision/{resultado_id}', data={
            'csrf_revision': 'revision-de-prueba', 'decision': 'reponer',
            'nota': 'El episodio se debió a un fallo comprobado de la cámara.'
        })
        self.assertEqual(respuesta.status_code, 302)
        with get_db_cursor() as cur:
            cur.execute('SELECT estado, revision, puntaje FROM resultados WHERE id = %s', (resultado_id,))
            resultado = cur.fetchone()
            cur.execute('SELECT decision FROM auditoria_revision WHERE resultado_id = %s', (resultado_id,))
            auditoria = cur.fetchone()
        self.assertEqual((resultado['estado'], resultado['revision'], resultado['puntaje']),
                         ('COMPLETADO', 'REPUESTO', 20.0))
        self.assertEqual(auditoria['decision'], 'reponer')
        with self.client.session_transaction() as sesion:
            sesion['usuario_id'] = self.uid
            sesion['es_admin'] = False
        vista_alumno = self.client.get(f'/resultado/{resultado_id}')
        self.assertEqual(vista_alumno.status_code, 200)
        self.assertIn('El episodio se debió a un fallo comprobado de la cámara.'.encode(), vista_alumno.data)
        self.assertIn('Examen repuesto tras revisión'.encode(), vista_alumno.data)


if __name__ == '__main__':
    unittest.main()
