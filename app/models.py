"""Contratos externos del prototipo."""
from typing import Any

from pydantic import BaseModel, Field


class EvaluacionIncidente(BaseModel):
    descripcion: str = Field(min_length=10, max_length=5000)
    probabilidad: int = Field(ge=1, le=5)
    impacto: int = Field(ge=1, le=5)
    rol_privacidad: str = "responsable"


class LlamadaAgente(BaseModel):
    entrada: dict[str, Any] = Field(default_factory=dict)


class ResultadoAgente(BaseModel):
    agente: str
    estado: str
    resultado: Any = None
    error: str | None = None
