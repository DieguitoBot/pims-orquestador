"""API central del PIMS: inicia un prototipo sin iniciar los agentes remotos."""
from fastapi import FastAPI, HTTPException

from .adapters import ejecutar_http
from .models import EvaluacionIncidente, LlamadaAgente
from .registry import AGENTS
from .workflows import flujo_incidente_riesgo

app = FastAPI(title="PIMS Orquestador UNSA", version="0.1.0",
              description="Coordinación externa de proyectos agénticos independientes.")


@app.get("/health")
def health():
    return {"estado": "ok", "version": "0.1.0"}


@app.get("/api/agentes")
def listar_agentes():
    return [{"id": id_, **datos} for id_, datos in AGENTS.items()]


@app.post("/api/agentes/{agente_id}/ejecutar")
async def ejecutar_agente(agente_id: str, body: LlamadaAgente):
    if agente_id not in AGENTS:
        raise HTTPException(404, "Agente no registrado")
    return await ejecutar_http(agente_id, body.entrada)


@app.post("/api/flujos/incidente-riesgo")
async def ejecutar_flujo(body: EvaluacionIncidente):
    return await flujo_incidente_riesgo(body)
