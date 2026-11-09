import asyncio
import json
import os
import unittest
from unittest.mock import patch

import httpx

from app.adapters import ejecutar_http
from app.models import EvaluacionIncidente
from app.registry import AGENTS
from app.workflows import flujo_incidente_riesgo


class IntegracionSimulada(unittest.IsolatedAsyncioTestCase):
    async def test_catalogo_ocho(self):
        self.assertEqual(len(AGENTS), 8)
        self.assertEqual(sum(a["integracion"] == "adaptador_inicial" for a in AGENTS.values()), 2)

    async def test_flujo_secuencial(self):
        llamadas = []
        def handler(req):
            llamadas.append((req.url.path, json.loads(req.content)))
            if req.url.path == "/api/analizar":
                return httpx.Response(200, json={"categoria": "exposicion", "severidad": "alta"})
            if req.url.path == "/api/evaluar":
                return httpx.Response(200, json={"puntaje": 12, "nivel": "alto"})
            return httpx.Response(404)
        transport = httpx.MockTransport(handler)
        with patch.dict(os.environ, {"INCIDENTES_URL": "http://mock", "RIESGOS_URL": "http://mock"}):
            async with httpx.AsyncClient(transport=transport) as client:
                r = await flujo_incidente_riesgo(EvaluacionIncidente(
                    descripcion="Fuga de datos personales de estudiantes",
                    probabilidad=3, impacto=4), client)
        self.assertEqual(r["estado"], "completado")
        self.assertEqual([x[0] for x in llamadas], ["/api/analizar", "/api/evaluar"])
        self.assertEqual(llamadas[1][1]["probabilidad"], 3)
        self.assertIn("exposicion", llamadas[1][1]["descripcion"])

    async def test_falla_incidente_sin_activar_riesgos(self):
        llamadas = []
        def handler(req):
            llamadas.append(req.url.path)
            return httpx.Response(503, json={"error": "no disponible"})
        with patch.dict(os.environ, {"INCIDENTES_URL": "http://mock", "RIESGOS_URL": "http://mock"}):
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                r = await flujo_incidente_riesgo(EvaluacionIncidente(
                    descripcion="Fuga de datos personales de estudiantes",
                    probabilidad=3, impacto=4), client)
        self.assertEqual(r["estado"], "incompleto")
        self.assertEqual(llamadas, ["/api/analizar"])


if __name__ == "__main__":
    unittest.main()
