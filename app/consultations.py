"""Operaciones de consulta contrastadas con los proyectos originales."""
import os
import httpx
from .config import agent_url, agent_token
from .models import ResultadoAgente


async def consultar(agent_id, entrada, client=None):
    if agent_id == "terceros" and entrada.get("operacion") != "listar_proveedores" and entrada.get("proveedor_id") is None:
        return ResultadoAgente(agente=agent_id, estado="requiere_datos", error="Selecciona el ID del proveedor registrado por el grupo de Terceros.")
    url = agent_url(agent_id)
    if not url:
        return ResultadoAgente(agente=agent_id, estado="no_configurado", error="Configura la URL privada del grupo en el orquestador.")
    async def operar(c):
        headers = {}
        token = agent_token(agent_id)
        if token: headers["Authorization"] = "Bearer " + token
        async def get(path):
            response = await c.get(url + path, headers=headers, timeout=15, follow_redirects=False)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict) and data.get("error"):
                raise ValueError("El agente informó un error")
            return data
        if agent_id == "terceros":
            if entrada.get("operacion") == "listar_proveedores":
                data = await get("/api/proveedores")
                if not isinstance(data, list): raise ValueError("Contrato de proveedores no reconocido")
                return [{"id": p["id"], "nombre": p["nombre"]} for p in data if isinstance(p, dict) and "id" in p and "nombre" in p]
            pid = entrada.get("proveedor_id")
            if type(pid) is not int or pid < 1:
                return ResultadoAgente(agente=agent_id, estado="requiere_datos", error="Selecciona el ID del proveedor registrado por el grupo de Terceros.")
            proveedor = await get(f"/api/proveedores/{pid}")
            if not isinstance(proveedor, dict) or proveedor.get("id") != pid:
                raise ValueError("La ficha del proveedor no coincide con el ID solicitado")
            # Esta ruta devuelve DPA + riesgo y evita consultar dos veces la matriz.
            return {"proveedor_id": pid, "nombre": proveedor.get("nombre"),
                    "dpa": proveedor.get("dpa"), "riesgo_proveedor": proveedor.get("riesgo"),
                    "escala_proveedor": "4×4; no comparable directamente con la matriz 5×5 de Riesgos"}
        if agent_id == "evidencias":
            usuario, clave = os.getenv("EVIDENCIAS_USUARIO"), os.getenv("EVIDENCIAS_CLAVE")
            if usuario and clave:
                login = await c.post(url + "/login", data={"usuario":usuario,"clave":clave}, timeout=15, follow_redirects=False)
                if login.status_code not in (302, 303):
                    return ResultadoAgente(agente=agent_id, estado="error", error="No se pudo autenticar con Evidencias. Revisa las credenciales de servicio.")
            data = await get("/api/agente/resumen")
            if not isinstance(data, dict) or "porcentaje_cobertura" not in data or "integridad" not in data:
                raise ValueError("Contrato de Evidencias no reconocido")
            return {"alcance":"Expediente general UNSA; esta cobertura no demuestra por sí sola los controles del incidente descrito.",
                    **{k:data.get(k) for k in ("porcentaje_cobertura","controles_aplicables","conteo_estados","integridad","evidencias","fecha_corte")}}
        raise ValueError("Operación no implementada")
    try:
        if client is None:
            async with httpx.AsyncClient() as c:
                data = await operar(c)
        else:
            data = await operar(client)
        if isinstance(data, ResultadoAgente): return data
        return ResultadoAgente(agente=agent_id, estado="completado", resultado=data)
    except httpx.HTTPStatusError as exc:
        code = exc.response.status_code
        error = "HTTP " + str(code) + " del agente"
        if code in (401,403): error += ": falta autorización de servicio."
        if code == 404 and agent_id == "terceros": error += ": confirma el ID con el grupo de Terceros."
        return ResultadoAgente(agente=agent_id, estado="error", error=error)
    except httpx.RequestError:
        return ResultadoAgente(agente=agent_id, estado="error", error="El servicio no responde; comprueba red privada, URL y proceso del grupo.")
    except (ValueError, KeyError, TypeError):
        return ResultadoAgente(agente=agent_id, estado="error", error="Respuesta no compatible con el contrato del agente. Revisa su versión.")
