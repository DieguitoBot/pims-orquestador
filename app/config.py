"""Configuración no sensible y URLs de agentes por variables de entorno."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def agent_url(agent_id: str) -> str | None:
    name = {"riesgos": "RIESGOS_URL", "incidentes": "INCIDENTES_URL"}.get(agent_id)
    return os.getenv(name, "").rstrip("/") or None if name else None


def agent_token(agent_id: str) -> str | None:
    name = {"riesgos": "RIESGOS_TOKEN", "incidentes": "INCIDENTES_TOKEN"}.get(agent_id)
    return os.getenv(name, "") or None if name else None


def timeout_seconds() -> float:
    try:
        return max(1.0, min(float(os.getenv("AGENT_TIMEOUT_SECONDS", "90")), 300.0))
    except ValueError:
        return 90.0
