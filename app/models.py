"""Contratos externos del prototipo."""
from typing import Any, Literal

from pydantic import BaseModel, Field


class EvaluacionIncidente(BaseModel):
    descripcion: str = Field(min_length=10, max_length=5000)
    probabilidad: int = Field(ge=1, le=5, strict=True)
    impacto: int = Field(ge=1, le=5, strict=True)
    rol_privacidad: Literal["responsable", "encargado", "ambos", "no_definido"] = "responsable"
    exigir_ia: bool = True


class LlamadaAgente(BaseModel):
    entrada: dict[str, Any] = Field(default_factory=dict)


class ResultadoAgente(BaseModel):
    agente: str
    estado: str
    resultado: Any = None
    error: str | None = None


class AnalisisIncidente(BaseModel):
    descripcion_evento: str = Field(min_length=10, max_length=2000)


class FlujoIncidente(EvaluacionIncidente):
    descripcion: str = Field(min_length=10, max_length=2000)


class ObjetivoProveedor(FlujoIncidente):
    proveedor_id: int | None = Field(default=None, ge=1, strict=True)
    objetivo: Literal["incidente_proveedor"] = "incidente_proveedor"
