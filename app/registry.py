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

# Capacidades revisadas en los repositorios; no equivalen a disponibilidad en red.
DETALLES = {
    "riesgos": {"sigla": "RI", "descripcion": "Evalúa riesgos de privacidad y organiza sus planes de tratamiento.", "entrada": "Escenario, probabilidad, impacto y rol de privacidad.", "salida": "Valoración, análisis con fuentes e identificador de evaluación guardada.", "siguiente_paso": "Comprobar conexión a V3 y su base documental.", "operacion": "Evaluar riesgos", "fase": 1},
    "incidentes": {"sigla": "IN", "descripcion": "Analiza eventos e incidentes de privacidad reportados.", "entrada": "Descripción del evento (máximo 2000 caracteres).", "salida": "Análisis del incidente según el contrato propio del agente.", "siguiente_paso": "Acordar URL accesible y validar con el servicio real del grupo.", "operacion": "Analizar incidente", "fase": 2},
    "evidencias": {"sigla": "EV", "descripcion": "Reúne evidencias, verifica integridad y prepara auditorías.", "entrada": "Proyecto, referencias de controles y evidencias autorizadas.", "salida": "Integridad, cobertura y propuestas preliminares para el auditor.", "siguiente_paso": "Cliente MCP streamable HTTP; empezar con estado_expediente y matriz_cobertura. El registro de archivos requiere acceso a la máquina del servidor.", "operacion": None, "fase": 3},
    "terceros": {"sigla": "DP", "descripcion": "Revisa proveedores, contratos DPA y subencargados.", "entrada": "Identificador de proveedor, contrato o categoría de brecha.", "salida": "Estado del DPA y riesgo del proveedor; decisiones de Legal separadas.", "siguiente_paso": "Adaptar herramientas GET de consulta. Mantener su matriz 4×4 separada de la matriz 5×5 de Riesgos.", "operacion": None, "fase": 3},
    "dsar": {"sigla": "DS", "descripcion": "Apoya solicitudes de derechos y consultas normativas trazables.", "entrada": "Caso normativo y credencial de servicio configurada en el servidor.", "salida": "Evidencia recuperada y conclusión con citas.", "siguiente_paso": "Adaptar /api/case-analysis y configurar X-API-Key. Confirmar fuentes verificadas antes de analizar.", "operacion": None, "fase": 4},
    "consentimientos": {"sigla": "CO", "descripcion": "Revisa evidencias de consentimiento y deriva observaciones al auditor.", "entrada": "Texto de evidencia documental y nombre del caso.", "salida": "Dictámenes por dominio, evidencias y revisión humana pendiente.", "siguiente_paso": "Elegir MCP stdio o HTTP /api/auditar (NDJSON). No tratar el streaming como un único JSON ni aprobar tickets automáticamente.", "operacion": None, "fase": 4},
    "privacy_coach": {"sigla": "PC", "descripcion": "Analiza esquemas y contratos para detectar brechas técnicas de privacidad.", "entrada": "Esquemas SQL y contratos autorizados.", "salida": "Hallazgos y propuestas de remediación.", "siguiente_paso": "Elegir herramientas de consulta y análisis. Excluir aplicación de parches y reinicios automáticos del repositorio.", "operacion": None, "fase": 5},
    "soa_studio": {"sigla": "SO", "descripcion": "Gestiona controles, brechas y la Declaración de Aplicabilidad.", "entrada": "Tarea, controles y contexto con sesión autorizada.", "salida": "Informe, traza de ejecución y análisis de controles.", "siguiente_paso": "Configurar JWT y /api/agent/run. Su núcleo es ISO/IEC 27001:2022; no equiparar sus controles automáticamente con 27701.", "operacion": None, "fase": 5},
}
for identificador, detalle in DETALLES.items():
    AGENTS[identificador].update(detalle)

# Operaciones de consulta integradas al objetivo incidente_proveedor.
for identificador in ("terceros", "evidencias"):
    AGENTS[identificador]["integracion"] = "adaptador_lectura"
    AGENTS[identificador]["protocolo"] = "HTTP de consulta"
AGENTS["terceros"]["siguiente_paso"] = "Configurar TERCEROS_URL y elegir un proveedor real del catálogo. El objetivo integrado consulta su ficha, DPA y riesgo 4×4."
AGENTS["evidencias"]["siguiente_paso"] = "Configurar EVIDENCIAS_URL, EVIDENCIAS_USUARIO y EVIDENCIAS_CLAVE. Se consulta cobertura e integridad; no se registran ni aprueban evidencias automáticamente."
