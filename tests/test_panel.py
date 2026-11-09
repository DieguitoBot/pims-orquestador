"""Panel y conectividad probados sin agentes ni modelos externos."""
import os
import unittest
from unittest.mock import AsyncMock, patch

import httpx
from fastapi.testclient import TestClient
from app.main import app
from app.models import ResultadoAgente
from app.status import comprobar_agentes, catalogo
from app.adapters import ejecutar_http


class TestPanel(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_panel_y_recursos_se_sirven_desde_la_api(self):
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertIn('Centro de agentes', r.text)
        self.assertIn('request-form', r.text)
        for path in ('/assets/panel.css', '/assets/panel.js', '/docs'):
            self.assertEqual(self.client.get(path).status_code, 200)

    def test_catalogo_no_expone_credenciales(self):
        with patch.dict(os.environ, {'RIESGOS_URL': 'http://usuario:secreto@localhost:8180', 'RIESGOS_TOKEN': 'token-privado'}):
            r = self.client.get('/api/agentes')
        self.assertEqual(len(r.json()), 8)
        self.assertNotIn('secreto', r.text)
        self.assertNotIn('token-privado', r.text)
        riesgo = next(a for a in r.json() if a['id'] == 'riesgos')
        self.assertIsNone(riesgo['interfaz_url'])

    def test_singular_no_ejecuta_y_explica_identificador(self):
        r = self.client.post('/api/agentes/riesgo/ejecutar', json={'entrada': {}})
        self.assertEqual(r.status_code, 404)
        self.assertIn('riesgos (plural)', r.json()['detail'])

    def test_formulario_invoca_riesgos_con_contrato_real(self):
        retorno = ResultadoAgente(agente='riesgos', estado='completado', resultado={'experimento_id':'prueba','puntaje':16})
        body = {'descripcion':'Escenario de prueba ficticio','probabilidad':4,'impacto':4,'exigir_ia':True}
        with patch('app.main.ejecutar_http', new_callable=AsyncMock, return_value=retorno) as ejecutar:
            r = self.client.post('/api/agentes/riesgos/ejecutar', json={'entrada':body})
        self.assertEqual(r.json()['estado'], 'completado')
        ejecutar.assert_awaited_once_with('riesgos', body)

    def test_incidente_rechaza_clave_erronea_antes_de_la_red(self):
        with patch('app.main.ejecutar_http', new_callable=AsyncMock) as ejecutar:
            r = self.client.post('/api/agentes/incidentes/ejecutar', json={'entrada':{'descripcion':'Escenario ficticio de prueba'}})
        self.assertEqual(r.status_code, 422)
        ejecutar.assert_not_awaited()

    def test_no_ejecuta_valoraciones_invalidas_o_flujos_demasiado_largos(self):
        with patch('app.main.ejecutar_http', new_callable=AsyncMock) as ejecutar:
            r = self.client.post('/api/agentes/riesgos/ejecutar', json={'entrada':{'descripcion':'Caso de prueba ficticio','probabilidad':True,'impacto':4}})
        self.assertEqual(r.status_code, 422)
        ejecutar.assert_not_awaited()
        r = self.client.post('/api/flujos/incidente-riesgo',json={'descripcion':'x'*2001,'probabilidad':4,'impacto':4})
        self.assertEqual(r.status_code, 422)


class TestConectividad(unittest.IsolatedAsyncioTestCase):
    async def test_comprobacion_solo_usa_get_y_no_ejecuta_agentes_pendientes(self):
        urls = []
        def handler(req):
            self.assertEqual(req.method,'GET')
            self.assertNotIn('TOKEN', str(req.url))
            urls.append(str(req.url))
            if req.url.host == 'riesgos': return httpx.Response(200,json={'ollama':True})
            raise httpx.ConnectError('offline',request=req)
        with patch.dict(os.environ, {'RIESGOS_URL':'http://riesgos','INCIDENTES_URL':'http://incidentes','RIESGOS_TOKEN':'TOKEN'}):
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                r = await comprobar_agentes(client)
        por_id = {a['id']:a for a in r['agentes']}
        self.assertEqual(len(urls),2)
        self.assertEqual(por_id['riesgos']['conectividad'],'responde')
        self.assertEqual(por_id['incidentes']['conectividad'],'no_responde')
        self.assertEqual(por_id['evidencias']['conectividad'],'sin_configurar')

    async def test_url_no_configurada_no_simula_conexion(self):
        with patch.dict(os.environ, {'RIESGOS_URL':'','INCIDENTES_URL':''}):
            async with httpx.AsyncClient(transport=httpx.MockTransport(lambda req: self.fail('No debe llamar a la red'))) as client:
                r = await comprobar_agentes(client)
        self.assertEqual(next(a for a in r['agentes'] if a['id']=='riesgos')['conectividad'],'sin_configurar')

    async def test_respuesta_200_con_error_no_se_marca_completada(self):
        with patch.dict(os.environ, {'RIESGOS_URL':'http://riesgos'}):
            async with httpx.AsyncClient(transport=httpx.MockTransport(lambda req:httpx.Response(200,json={'error':'Falló el modelo'}))) as client:
                r=await ejecutar_http('riesgos',{},client)
        self.assertEqual(r.estado,'error')
