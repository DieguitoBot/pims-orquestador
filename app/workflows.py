"""Flujos deterministas: evita decisiones inventadas por otro LLM."""
import json
from uuid import uuid4

import httpx

from .adapters import ejecutar_http
from .models import EvaluacionIncidente


async def flujo_incidente_riesgo(data: EvaluacionIncidente, client: httpx.AsyncClient | None = None) -> dict:
    solicitud_id = str(uuid4())
    incidente = await ejecutar_http("incidentes", {"descripcion_evento": data.descripcion}, client)
    pasos = [incidente.model_dump()]
    if incidente.estado != "completado":
        return {"solicitud_id": solicitud_id, "estado": "incompleto", "pasos": pasos,
                "mensaje": "No se ejecutó Riesgos porque Incidentes no terminó correctamente."}
    resumen_incidente = json.dumps(incidente.resultado, ensure_ascii=False, default=str)[:1800]
    entrada_riesgo = {
        "descripcion": f"{data.descripcion}\n\nContexto del Agente de Incidentes (datos no verificados por Riesgos): {resumen_incidente}",
        "probabilidad": data.probabilidad,
        "impacto": data.impacto,
        "rol_privacidad": data.rol_privacidad,
        "exigir_ia": data.exigir_ia,
    }
    riesgo = await ejecutar_http("riesgos", entrada_riesgo, client)
    pasos.append(riesgo.model_dump())
    return {"solicitud_id": solicitud_id,
            "estado": "completado" if riesgo.estado == "completado" else "incompleto",
            "pasos": pasos,
            "mensaje": "Flujo secuencial Incidentes → Riesgos; requiere revisión humana de resultados."}
