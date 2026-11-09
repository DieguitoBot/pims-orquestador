"""API central del PIMS: inicia un prototipo sin iniciar los agentes remotos."""
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .adapters import ejecutar_http
from .models import EvaluacionIncidente, LlamadaAgente, AnalisisIncidente, FlujoIncidente, ObjetivoProveedor
from .status import catalogo, comprobar_agentes
from .registry import AGENTS
from .workflows import flujo_incidente_riesgo

from . import executions
from .consultations import consultar


@asynccontextmanager
async def lifespan(app):
    yield
    await executions.cerrar()


app = FastAPI(lifespan=lifespan,title="PIMS Orquestador UNSA", version="0.3.0",
              description="Coordinación externa de proyectos agénticos independientes.")


@app.get("/health")
def health():
    return {"estado": "ok", "version": "0.3.0"}


@app.get("/api/agentes")
def listar_agentes():
    return catalogo()


@app.post("/api/agentes/{agente_id}/ejecutar")
async def ejecutar_agente(agente_id: str, body: LlamadaAgente):
    if agente_id not in AGENTS:
        raise HTTPException(404, "Agente no registrado. Usa su identificador exacto del catálogo; por ejemplo, riesgos (plural).")
    # Validar el contrato antes de llamar al servicio externo.
    from pydantic import ValidationError
    try:
        if agente_id == "riesgos":
            EvaluacionIncidente.model_validate(body.entrada)
        elif agente_id == "incidentes":
            AnalisisIncidente.model_validate(body.entrada)
    except ValidationError:
        raise HTTPException(422, "Revisa descripción y valoración: Riesgos requiere probabilidad e impacto 1–5; Incidentes recibe descripcion_evento (10–2000 caracteres).")
    return await ejecutar_http(agente_id, body.entrada)


@app.post("/api/flujos/incidente-riesgo")
async def ejecutar_flujo(body: FlujoIncidente):
    return await flujo_incidente_riesgo(body)


WEB = Path(__file__).resolve().parent / "web"
app.mount("/assets", StaticFiles(directory=WEB), name="assets")


@app.get("/", include_in_schema=False)
def panel():
    return FileResponse(WEB / "index.html", headers={"Cache-Control": "no-store"})


@app.get("/api/agentes/estado")
async def estado_agentes():
    return await comprobar_agentes()


@app.post("/api/ejecuciones", status_code=202)
async def iniciar_objetivo(body: ObjetivoProveedor):
    try:
        return await executions.iniciar(body)
    except ValueError as exc:
        raise HTTPException(409, str(exc))


@app.get("/api/ejecuciones/{solicitud_id}")
def obtener_objetivo(solicitud_id: str):
    executions.limpiar()
    data = executions.obtener(solicitud_id)
    if data is None:
        raise HTTPException(404, "Ejecución no disponible. El registro en memoria expira tras una hora o al reiniciar. Consulta el historial de los agentes antes de repetir.")
    return data


@app.get("/api/proveedores")
async def listar_proveedores():
    return await consultar("terceros", {"operacion":"listar_proveedores"})
