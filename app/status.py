"""Comprobaciones de conectividad HTTP; no ejecutan evaluaciones ni inician agentes."""
import asyncio
from datetime import datetime, timezone
from urllib.parse import urlsplit

import httpx

from .config import agent_url, agent_token
from .registry import AGENTS


def url_publica(agent_id):
    url = agent_url(agent_id)
    if not url: return None
    try:
        partes = urlsplit(url)
        if partes.scheme not in {"http", "https"} or not partes.hostname or partes.username or partes.password or partes.query or partes.fragment:
            return None
        return url
    except ValueError:
        return None


def catalogo():
    return [dict(id=id_, **datos, configurado=bool(agent_url(id_)),
                 interfaz_url=url_publica(id_), conectividad="sin_comprobar")
            for id_, datos in AGENTS.items()]


async def comprobar_agentes(client=None):
    async def comprobar(c, agente):
        if agente["integracion"] == "pendiente":
            return dict(agente, conectividad="pendiente", detalle="Adaptador pendiente de implementación.")
        if not agent_url(agente["id"]):
            return dict(agente, conectividad="sin_configurar", detalle="Configura la URL en el .env del orquestador.")
        if not agente["interfaz_url"]:
            return dict(agente, conectividad="error", detalle="URL HTTP de configuración no válida.")
        headers = {}
        token = agent_token(agente["id"])
        if token: headers["Authorization"] = f"Bearer {token}"
        ruta = {"riesgos":"/api/status", "terceros":"/api/estado", "evidencias":"/api/sesion"}.get(agente["id"], "/")
        try:
            respuesta = await c.get(agent_url(agente["id"]) + ruta, headers=headers, timeout=3)
            estado = "responde" if respuesta.is_success else "error"
            return dict(agente, conectividad=estado, detalle=f"HTTP {respuesta.status_code}. La conexión no verifica por sí sola el modelo ni el corpus.")
        except httpx.RequestError:
            return dict(agente, conectividad="no_responde", detalle="No se pudo contactar al servicio en 3 segundos. Comprueba su dirección y arranque.")
    if client is None:
        async with httpx.AsyncClient() as c:
            agentes = await asyncio.gather(*(comprobar(c, a) for a in catalogo()))
    else:
        agentes = await asyncio.gather(*(comprobar(client, a) for a in catalogo()))
    return {"comprobado": datetime.now(timezone.utc).isoformat(), "agentes": agentes}
