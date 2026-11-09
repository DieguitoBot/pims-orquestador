"""Catálogo externo. Registrado no significa integrado ni disponible."""
AGENTS = {
    "evidencias": {"nombre": "Evidencia y Auditoría", "repositorio": "https://github.com/jhuamaniCond/auditoria-agente-tif-2", "integracion": "pendiente", "protocolo": "MCP/HTTP (por adaptar)"},
    "consentimientos": {"nombre": "Supervisor de Consentimientos", "repositorio": "https://github.com/Dan-Ar5/Auditoria", "integracion": "pendiente", "protocolo": "MCP stdio (por adaptar)"},
    "dsar": {"nombre": "Derechos del Titular (DSAR)", "repositorio": "https://github.com/JeremyCruzGallegos/agente-dsar-iso27701", "integracion": "pendiente", "protocolo": "HTTP (por adaptar)"},
    "incidentes": {"nombre": "Gestión de Incidentes", "repositorio": "https://github.com/jherson2024/agente_privacidad", "integracion": "adaptador_inicial", "protocolo": "HTTP"},
    "privacy_coach": {"nombre": "Privacy Coach", "repositorio": "https://github.com/DrN25/Privacy-Coach-Agent-ISO-27701", "integracion": "pendiente", "protocolo": "HTTP/MCP (por adaptar)"},
    "riesgos": {"nombre": "Evaluación de Riesgos", "repositorio": "https://github.com/DieguitoBot/agente-riesgos-pims", "integracion": "adaptador_inicial", "protocolo": "HTTP"},
    "soa_studio": {"nombre": "SoA Studio (ISO/IEC 27001:2022)", "repositorio": "https://github.com/gcarrillov/SOA_estudio_agente_AUDITORIA", "integracion": "pendiente", "protocolo": "HTTP autenticado (por adaptar)"},
    "terceros": {"nombre": "Terceros y DPA", "repositorio": "https://github.com/S-kkipie/agente-terceros-dpa", "integracion": "pendiente", "protocolo": "HTTP/MCP (por adaptar)"},
}
