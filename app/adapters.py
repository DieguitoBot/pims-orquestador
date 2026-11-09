"""Adaptadores HTTP de prueba. Contratos definitivos sujetos a validación."""
from typing import Any

import httpx

from .config import agent_token, agent_url, timeout_seconds
from .models import ResultadoAgente

PATHS = {"incidentes": "/api/analizar", "riesgos": "/api/evaluar"}


async def ejecutar_http(
    agent_id: str, entrada: dict[str, Any], client: httpx.AsyncClient | None = None
) -> ResultadoAgente:
    if agent_id in {"terceros", "evidencias"}:
        from .consultations import consultar
        return await consultar(agent_id, entrada, client)
    if agent_id not in PATHS:
        return ResultadoAgente(agente=agent_id, estado="no_integrado", error="Adaptador no implementado")
    url = agent_url(agent_id)
    if not url:
        return ResultadoAgente(agente=agent_id, estado="no_configurado", error="Falta URL del agente")
    headers = {}
    if agent_token(agent_id):
        headers["Authorization"] = f"Bearer {agent_token(agent_id)}"
    async def enviar(c: httpx.AsyncClient):
        return await c.post(url + PATHS[agent_id], json=entrada, headers=headers)
    try:
        if client is None:
            async with httpx.AsyncClient(timeout=timeout_seconds()) as c:
                response = await enviar(c)
        else:
            response = await enviar(client)
        response.raise_for_status()
        try:
            data = response.json()
        except ValueError:
            return ResultadoAgente(agente=agent_id, estado="error", error="El agente no devolvió JSON")
        if isinstance(data, dict) and data.get("error"):
            return ResultadoAgente(agente=agent_id, estado="error", resultado=data,
                                   error="El agente informó un error en su respuesta.")
        return ResultadoAgente(agente=agent_id, estado="completado", resultado=data)
    except httpx.TimeoutException:
        return ResultadoAgente(agente=agent_id, estado="error", error="Tiempo de espera agotado")
    except httpx.HTTPStatusError as e:
        return ResultadoAgente(agente=agent_id, estado="error", error=f"HTTP {e.response.status_code} del agente")
    except httpx.RequestError as e:
        return ResultadoAgente(agente=agent_id, estado="error", error=f"Conexión fallida: {type(e).__name__}")
