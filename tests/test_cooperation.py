import asyncio
import json
import os
import unittest
from copy import deepcopy
from unittest.mock import patch, AsyncMock
import httpx
from fastapi.testclient import TestClient
from app.cooperation import coordinar
from app.models import ObjetivoProveedor
from app.main import app
from app import executions
from scripts.puente_grupo import app as bridge, permitido

CONFIG={'INCIDENTES_URL':'http://incidentes','TERCEROS_URL':'http://terceros','EVIDENCIAS_URL':'http://evidencias','RIESGOS_URL':'http://riesgos','EVIDENCIAS_USUARIO':'servicio','EVIDENCIAS_CLAVE':'CLAVE_INTERNA'}
CASO=ObjetivoProveedor(descripcion='Proveedor publica enlace abierto con datos de estudiantes.',probabilidad=4,impacto=4,proveedor_id=4)

class TestCooperacion(unittest.IsolatedAsyncioTestCase):
    async def test_cuatro_agentes_pasan_contexto_real_a_riesgos(self):
        llamadas=[];progreso=[]
        def handler(req):
            llamadas.append((req.method,str(req.url),req.content.decode()))
            if req.url.host=='incidentes':return httpx.Response(200,json={'evento':'enlace abierto'})
            if req.url.host=='terceros':return httpx.Response(200,json={'id':4,'nombre':'Nube ficticia','contacto':'NO_PROPAGAR','dpa':{'estado':'vencido'},'riesgo':{'nivel':'alto'}})
            if req.url.path=='/login':return httpx.Response(302,headers={'set-cookie':'sesion=privada; Path=/'})
            if req.url.host=='evidencias':return httpx.Response(200,json={'porcentaje_cobertura':40,'integridad':{'integro':True},'evidencias':3})
            if req.url.host=='riesgos':
                d=json.loads(req.content)
                self.assertIn('enlace abierto',d['descripcion']);self.assertIn('vencido',d['descripcion']);self.assertIn('porcentaje_cobertura',d['descripcion'])
                self.assertNotIn('CLAVE_INTERNA',d['descripcion']);self.assertNotIn('NO_PROPAGAR',d['descripcion'])
                self.assertLessEqual(len(d['descripcion']),5000)
                return httpx.Response(200,json={'experimento_id':'guardado','reporte_texto':'Reporte de riesgo','puntaje':16})
            self.fail(str(req.url))
        async def avisar(p):progreso.append(deepcopy(p))
        with patch.dict(os.environ,CONFIG):
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as c:
                r=await coordinar(CASO,c,avisar)
        self.assertEqual(r['estado'],'completado');self.assertEqual(len(r['intercambios']),3)
        self.assertTrue(r['resumen']['colaboracion_efectiva']);self.assertEqual(r['resumen']['evaluacion_id'],'guardado')
        self.assertEqual([p['agente'] for p in r['pasos']],['incidentes','terceros','evidencias','riesgos'])
        self.assertEqual(progreso[0][0]['estado'],'en_curso');self.assertEqual(progreso[0][1]['estado'],'pendiente')
        self.assertIn('Reporte de riesgo',r['informe_integrado'])
        self.assertNotIn('CLAVE_INTERNA',json.dumps(r))
        self.assertEqual([x[0] for x in llamadas],['POST','GET','POST','GET','POST'])

    async def test_fallos_no_se_convierten_en_hechos_del_contexto(self):
        entradas=[]
        def handler(req):
            if req.url.host=='riesgos':
                entradas.append(json.loads(req.content)['descripcion']);return httpx.Response(200,json={'experimento_id':'id'})
            return httpx.Response(503,json={'error':'no disponible'})
        with patch.dict(os.environ,{**CONFIG,'EVIDENCIAS_URL':'','EVIDENCIAS_USUARIO':'','EVIDENCIAS_CLAVE':''}):
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as c:r=await coordinar(CASO,c)
        self.assertEqual(r['estado'],'parcial');self.assertFalse(r['resumen']['colaboracion_efectiva'])
        self.assertEqual(entradas,[CASO.descripcion]);self.assertEqual(r['intercambios'],[])
        self.assertGreaterEqual(len(r['pendientes']),3)

    async def test_proveedor_ausente_se_pide_no_se_inventa(self):
        from app.consultations import consultar
        with patch.dict(os.environ,CONFIG):
            async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r:self.fail('No consultar un ID inventado'))) as c:
                r=await consultar('terceros',{'proveedor_id':None},c)
        self.assertEqual(r.estado,'requiere_datos')

    async def test_registro_publica_progreso_y_no_duplica_flujos(self):
        executions.REGISTRO.clear();bloqueo=asyncio.Event()
        async def lento(data,notificar):
            await bloqueo.wait();return {'estado':'completado','pasos':[]}
        with patch('app.executions.coordinar',side_effect=lento):
            r=await executions.iniciar(CASO)
            self.assertEqual(executions.obtener(r['solicitud_id'])['estado'],'en_curso')
            with self.assertRaises(ValueError):await executions.iniciar(CASO)
            bloqueo.set();await asyncio.gather(*list(executions.TAREAS))
            self.assertEqual(executions.obtener(r['solicitud_id'])['estado'],'completado')
        executions.REGISTRO.clear()

class TestPuente(unittest.TestCase):
    def test_no_publica_operaciones_destructivas(self):
        for grupo,path in [('terceros','/api/aprobaciones/1'),('evidencias','/api/agente/base/vaciar'),('privacy_coach','/api/reset')]:
            self.assertFalse(permitido(grupo,'POST',path))
        with patch.dict(os.environ,{'PIMS_GROUP_AGENT':'terceros','PIMS_GROUP_TOKEN':'TOKEN_PRUEBA'}):
            with TestClient(bridge) as c:
                self.assertEqual(c.get('/api/proveedores').status_code,401)
                self.assertEqual(c.post('/api/aprobaciones/1',headers={'Authorization':'Bearer TOKEN_PRUEBA'},json={}).status_code,403)

    def test_token_del_puente_no_se_reenvia_al_agente(self):
        calls=[]
        def handler(req):
            calls.append(req)
            self.assertNotIn('authorization',req.headers)
            return httpx.Response(200,json=[{'id':4,'nombre':'Proveedor de prueba'}])
        native=httpx.AsyncClient(transport=httpx.MockTransport(handler))
        with patch.dict(os.environ,{'PIMS_GROUP_AGENT':'terceros','PIMS_GROUP_TOKEN':'TOKEN_PRUEBA','PIMS_GROUP_TARGET':'http://127.0.0.1:5000','PIMS_UPSTREAM_API_KEY':'','PIMS_UPSTREAM_BEARER':''}),patch('scripts.puente_grupo.httpx.AsyncClient',return_value=native):
            with TestClient(bridge) as c:
                r=c.get('/api/proveedores',headers={'Authorization':'Bearer TOKEN_PRUEBA'})
        self.assertEqual(r.status_code,200);self.assertEqual(len(calls),1)
        self.assertEqual(str(calls[0].url),'http://127.0.0.1:5000/api/proveedores')

    def test_target_remoto_no_permitido(self):
        with patch.dict(os.environ,{'PIMS_GROUP_AGENT':'terceros','PIMS_GROUP_TOKEN':'TOKEN_PRUEBA','PIMS_GROUP_TARGET':'http://otro-equipo:5000'}):
            with TestClient(bridge) as c:
                r=c.get('/api/proveedores',headers={'Authorization':'Bearer TOKEN_PRUEBA'})
        self.assertEqual(r.status_code,503)

class TestAPIObjetivo(unittest.TestCase):
    def test_iniciar_y_recuperar_resultado_sin_servicios(self):
        executions.REGISTRO.clear()
        with patch.dict(os.environ,{'INCIDENTES_URL':'','RIESGOS_URL':'','EVIDENCIAS_URL':'','TERCEROS_URL':''}):
            with TestClient(app) as c:
                r=c.post('/api/ejecuciones',json=CASO.model_dump())
                self.assertEqual(r.status_code,202)
                id_=r.json()['solicitud_id']
                # Las tareas sin servicios configurados terminan sin operaciones de red.
                data=c.get('/api/ejecuciones/'+id_).json()
                self.assertIn(data['estado'],['en_curso','error'])
                self.assertEqual(len(data['pasos']),4)
                self.assertEqual(c.get('/api/ejecuciones/no-existe').status_code,404)
        executions.REGISTRO.clear()

    def test_ficha_privada_no_necesita_password_del_grupo(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        import scripts.preparar_grupo as setup
        import scripts.conectar_grupo as connect
        from dotenv import dotenv_values
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            with patch.object(setup,'RAIZ',base),patch('sys.argv',['preparar','incidentes','--puerto','5000','--url-publicada','https://grupo.example.ts.net:8443']):
                setup.main()
            ficha=base/'.conexion-grupo.json'
            data=json.loads(ficha.read_text())
            self.assertEqual(data['agente'],'incidentes');self.assertGreaterEqual(len(data['token']),32)
            self.assertNotIn('password',data)
            # Test the importer against an isolated project root.
            with patch.object(connect,'__file__',str(base/'scripts/conectar_grupo.py')),patch('sys.argv',['conectar',str(ficha)]):
                connect.main()
            config=dotenv_values(base/'.env')
            self.assertEqual(config['INCIDENTES_URL'],data['url'])
            self.assertEqual(config['INCIDENTES_TOKEN'],data['token'])
