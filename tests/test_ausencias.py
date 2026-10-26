"""Ausencias: solo en PostgreSQL aislado, sin fotografías de personas reales."""

import io
import tempfile
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from PIL import Image

# Este módulo valida identidad de la base ANTES de importar la aplicación.
from tests.test_supervision import app, get_db_cursor, crear_intento
from models import ausencia
from models.supervision import entregar_examen


class TestAusencias(unittest.TestCase):
    def setUp(self):
        app.config['TESTING']=True
        self.temporal=tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        parche=patch.object(ausencia,'DIRECTORIO',Path(self.temporal.name))
        parche.start()
        self.addCleanup(parche.stop)
        with get_db_cursor(commit=True) as cur:
            cur.execute("INSERT INTO usuarios (nombre,apellido,dni,password_hash,area,consentimiento_ausencia_version,consentimiento_celular_version) "
                        "VALUES ('Ausencia','Prueba',%s,'hash','A',%s,'celular-v2-fotos') RETURNING id",
                        (str(uuid.uuid4().int)[:12],ausencia.CONSENTIMIENTO))
            self.uid=cur.fetchone()['id']
        self.intento=crear_intento(self.uid,'A')
        self.episodio=str(uuid.uuid4())
        self.client=app.test_client()
        with self.client.session_transaction() as sesion:
            sesion.update(usuario_id=self.uid,es_admin=False,csrf_examen='ausencia-csrf',csrf_preparacion='prep-csrf',examen_area='A')
        self.headers={'X-CSRF-Token':'ausencia-csrf'}

    def foto(self,color='red'):
        salida=io.BytesIO()
        Image.new('RGB',(320,240),color).save(salida,format='JPEG')
        return salida.getvalue()

    def enviar(self,secuencia=1,estado='ausente',foto=None,**extra):
        data=dict(token_sesion=self.intento['token_sesion'],episodio_id=self.episodio,
                  secuencia=str(secuencia),estado=estado,**extra)
        if foto is not None:
            data['foto']=(io.BytesIO(foto),'ausencia.jpg')
        return self.client.post('/api/intento/ausencia',data=data,headers=self.headers)

    def adelantar_intervalo(self,segundos):
        with get_db_cursor(commit=True) as cur:
            cur.execute("UPDATE episodios_ausencia SET ultima_observacion=CURRENT_TIMESTAMP-(%s*INTERVAL '1 second') "
                        'WHERE intento_id=%s AND episodio_id=%s',(segundos,self.intento['id'],self.episodio))

    def episodio_bd(self):
        with get_db_cursor() as cur:
            cur.execute('SELECT * FROM episodios_ausencia WHERE intento_id=%s AND episodio_id=%s',
                        (self.intento['id'],self.episodio))
            return cur.fetchone()

    def test_foto_cifrada_duracion_retorno_y_revision_sin_anulacion(self):
        inicio=self.enviar(foto=self.foto(),duracion_segundos='99999')
        self.assertEqual(inicio.status_code,200)
        self.assertEqual(inicio.json['segundos_observados'],0)
        self.assertTrue(inicio.json['foto_guardada'])
        self.adelantar_intervalo(18)
        self.assertEqual(self.enviar(2).status_code,200)
        self.adelantar_intervalo(6)
        regreso=self.enviar(3,'presente')
        self.assertEqual(regreso.status_code,200)
        self.assertAlmostEqual(regreso.json['segundos_observados'],24,delta=.5)
        self.assertFalse(regreso.json['incompleto'])
        fila=self.episodio_bd()
        cifrada=(ausencia.DIRECTORIO/fila['archivo']).read_bytes()
        self.assertNotEqual(cifrada[:2],b'\xff\xd8')
        self.assertTrue(ausencia.leer_foto_ausencia(fila['id']).startswith(b'\xff\xd8'))
        with get_db_cursor() as cur:
            cur.execute('SELECT estado_academico,estado_supervision FROM intentos WHERE id=%s',(self.intento['id'],))
            estado=cur.fetchone()
            self.assertEqual((estado['estado_academico'],estado['estado_supervision']),('EN_CURSO','PENDIENTE'))
        resultado=entregar_examen(self.intento['token_sesion'],self.uid)
        with get_db_cursor() as cur:
            cur.execute('SELECT estado,revision,motivo_anulacion FROM resultados WHERE id=%s',(resultado['id'],))
            r=cur.fetchone()
            self.assertEqual((r['estado'],r['revision']),('COMPLETADO','PENDIENTE'))
            self.assertIn('Ausencia',r['motivo_anulacion'])
        alumno=self.client.get(f'/resultado/{resultado["id"]}')
        self.assertNotIn(b'/admin/evidencia-ausencia/',alumno.data)
        acceso_alumno=self.client.get(f'/admin/evidencia-ausencia/{fila["id"]}')
        self.assertIn(acceso_alumno.status_code,(302,403))
        with get_db_cursor(commit=True) as cur:
            cur.execute('UPDATE usuarios SET es_admin=TRUE WHERE id=%s',(self.uid,))
        with self.client.session_transaction() as sesion:
            sesion['es_admin']=True
        administrador=self.client.get(f'/resultado/{resultado["id"]}')
        self.assertIn(b'/admin/evidencia-ausencia/',administrador.data)
        self.assertIn(b'segundos observados en total',administrador.data)
        foto=self.client.get(f'/admin/evidencia-ausencia/{fila["id"]}')
        self.assertEqual(foto.status_code,200)
        self.assertIn('no-store',foto.headers['Cache-Control'])

    def test_reintentos_y_peticiones_simultaneas_no_duplican(self):
        datos=self.foto()
        def guardar():
            return ausencia.registrar_observacion(self.intento['token_sesion'],self.uid,self.episodio,1,'ausente',datos)
        with ThreadPoolExecutor(max_workers=2) as ejecutor:
            resultados=list(ejecutor.map(lambda _:guardar(),range(2)))
        self.assertEqual(resultados[0],resultados[1])
        archivo=self.episodio_bd()['archivo']
        self.adelantar_intervalo(6)
        segundo=self.enviar(2)
        repetido=self.enviar(2,foto=self.foto('blue'))
        anterior=self.enviar(1)
        self.assertEqual(segundo.json,repetido.json)
        self.assertEqual(segundo.json,anterior.json)
        self.assertEqual(archivo,self.episodio_bd()['archivo'])
        self.assertEqual(len(list(ausencia.DIRECTORIO.iterdir())),1)

    def test_camara_interrumpida_y_huecos_no_se_suman(self):
        self.assertEqual(self.enviar().status_code,200)
        self.adelantar_intervalo(120)
        hueco=self.enviar(2)
        self.assertEqual(hueco.json['segundos_observados'],0)
        self.assertTrue(hueco.json['incompleto'])
        self.adelantar_intervalo(6)
        interrumpido=self.enviar(3,'interrumpido')
        self.assertEqual(interrumpido.json['segundos_observados'],0)
        self.assertEqual(interrumpido.json['estado'],'interrumpido')
        self.assertEqual(self.enviar(4,'presente').status_code,400)

    def test_csrf_propiedad_consentimiento_y_jpeg(self):
        self.assertEqual(self.client.post('/api/intento/ausencia',data={'estado':'ausente'}).status_code,403)
        with self.client.session_transaction() as sesion:
            sesion['usuario_id']=self.uid+1_000_000
        self.assertEqual(self.enviar().status_code,403)
        with self.client.session_transaction() as sesion:
            sesion['usuario_id']=self.uid
        with get_db_cursor(commit=True) as cur:
            cur.execute('UPDATE usuarios SET consentimiento_ausencia_version=NULL WHERE id=%s',(self.uid,))
        self.assertEqual(self.enviar().status_code,403)
        consentimiento='/api/intento/consentimiento-ausencia'
        self.assertEqual(self.client.post(consentimiento,json={'acepta':True}).status_code,403)
        self.assertEqual(self.client.post(consentimiento,json={'acepta':False},headers={'X-CSRF-Token':'prep-csrf'}).status_code,400)
        self.assertEqual(self.client.post(consentimiento,json={'acepta':True},headers={'X-CSRF-Token':'prep-csrf'}).status_code,200)
        self.assertEqual(self.enviar(foto=b'no es jpeg').status_code,400)
        self.assertIsNone(self.episodio_bd())
        self.assertEqual(self.enviar(foto=b'x'*80_001).status_code,400)
        self.assertEqual(self.enviar(foto=self.foto()).status_code,200)

    def test_examen_cerrado_o_vencido_no_acepta_fotos(self):
        with get_db_cursor(commit=True) as cur:
            cur.execute("UPDATE intentos SET fecha_vencimiento=CURRENT_TIMESTAMP-INTERVAL '1 minute' WHERE id=%s",(self.intento['id'],))
        self.assertEqual(self.enviar(foto=self.foto()).status_code,403)
        self.assertIsNone(self.episodio_bd())

    def test_fin_examen_cierra_registro_y_caducidad_impide_lectura(self):
        self.assertEqual(self.enviar(foto=self.foto()).status_code,200)
        self.adelantar_intervalo(10)
        self.enviar(2)
        entregar_examen(self.intento['token_sesion'],self.uid)
        episodio=self.episodio_bd()
        self.assertEqual(episodio['estado'],'fin_examen')
        self.assertTrue(episodio['incompleto'])
        self.assertAlmostEqual(episodio['duracion_segundos'],10,delta=.5)
        self.assertEqual(self.enviar(3,'presente').status_code,403)
        with get_db_cursor(commit=True) as cur:
            cur.execute("UPDATE episodios_ausencia SET expira_en=CURRENT_TIMESTAMP-INTERVAL '1 day' WHERE id=%s",(episodio['id'],))
        self.assertIsNone(ausencia.leer_foto_ausencia(episodio['id']))


if __name__=='__main__':
    unittest.main()
