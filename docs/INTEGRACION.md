# Integración PIMS — revisión 09/11/2026

## Arquitectura y alcance

La interfaz se sirve desde FastAPI en el puerto 9000. El navegador solo llama al
orquestador, que utiliza adaptadores para cada aplicación. No se copian LLM,
corpus ni tablas a una base central. Las claves se configuran en el servidor.

Riesgos V3 fue probado por el usuario: ejecución real con Ollama, recuperación
PostgreSQL y `experimento_id` de persistencia. Las pruebas de este cambio son
simuladas; no se dispone de conexión a sus equipos desde el entorno de revisión.
Los demás servicios requieren pruebas propias antes de considerarlos integrados.

## Inventario contrastado con los repositorios

| ID estable | Repositorio | Operación/transporte verificado | Próximo trabajo |
|---|---|---|---|
| `riesgos` | [DieguitoBot/agente-riesgos-pims](https://github.com/DieguitoBot/agente-riesgos-pims) | `POST /api/evaluar`, `GET /api/status`; V3 en 8180 | Adaptador existente y prueba real individual. Verificar historial desde V3. |
| `incidentes` | [jherson2024/agente_privacidad](https://github.com/jherson2024/agente_privacidad) | `app/routes/incidents.py`: `POST /api/analizar` recibe **descripcion_evento**, máximo 2000 caracteres | Se corrige el payload del flujo. Necesita URL accesible y prueba real con el grupo. |
| `evidencias` | [jhuamaniCond/auditoria-agente-tif-2](https://github.com/jhuamaniCond/auditoria-agente-tif-2) | `Entregable-2/agente/servidor_mcp.py`: stdio o streamable HTTP (`--http`, `/mcp`) | Cliente MCP; comenzar con estado_expediente y matriz_cobertura. No saltar aprobaciones ni registrar archivos sin confirmación. |
| `terceros` | [S-kkipie/agente-terceros-dpa](https://github.com/S-kkipie/agente-terceros-dpa) | GET `/api/tools/list_processors`, `/api/tools/check_dpa_status/<id>`, `/api/tools/evaluate_vendor/<id>` y MCP stdio | Adaptador de lectura y datos de prueba. Conservar su escala 4×4 separada de Riesgos (5×5). |
| `dsar` | [JeremyCruzGallegos/agente-dsar-iso27701](https://github.com/JeremyCruzGallegos/agente-dsar-iso27701) | README: `/api/case-analysis`, `/api/knowledge/status`; autenticación **X-API-Key** | Confirmar payload y configurar clave de servicio por entorno. No reutilizar Bearer sin adaptación. |
| `consentimientos` | [Dan-Ar5/Auditoria](https://github.com/Dan-Ar5/Auditoria) | `dashboard.py`: POST `/api/auditar` con `{texto,nombre}` produce **NDJSON**; también MCP stdio | Elegir MCP o parser NDJSON para eventos/resultado. Mantener la cola HITL sin aprobación automática. |
| `privacy_coach` | [DrN25/Privacy-Coach-Agent-ISO-27701](https://github.com/DrN25/Privacy-Coach-Agent-ISO-27701) | README: FastAPI y MCP para auditoría de esquemas/contratos | Acordar herramientas y autenticación; habilitar análisis, no `dspm_apply_remediation` ni `dspm_reset_repository` desde el orquestador. |
| `soa_studio` | [gcarrillov/SOA_estudio_agente_AUDITORIA](https://github.com/gcarrillov/SOA_estudio_agente_AUDITORIA) | Capa agéntica HTTP y JWT; base normativa ISO/IEC 27001:2022 | Validar contrato de `/api/agent/run`, permisos y correspondencias con 27701 antes de reutilizar resultados. |

No se infiere que los endpoints tengan el mismo contrato porque usen HTTP.
El número de ocho corresponde a repositorios, no a subagentes internos.

## Entregas sucesivas

1. **Panel y Riesgos:** formulario, fuentes, resultado y enlace al historial; no escribir IDs a mano.
2. **Incidentes → Riesgos:** prueba con dos aplicaciones reales. Mantener escenario original y etiquetar resultados anteriores como contexto, no como hechos independientes verificados.
3. **Terceros y Evidencias:** consultas de proveedor y cobertura. Para un incidente con proveedor, proponer el expediente y pedir aprobación antes de registrar documentos.
4. **DSAR y Consentimientos:** adaptadores autenticados y streaming; revisar las evidencias específicas necesarias.
5. **Privacy Coach y SoA:** análisis especializados solo con sus insumos y permisos; correspondencia normativa explícita.

Cada entrega se acepta con una llamada directa al agente, otra por el orquestador,
un caso de fallo, muestras JSON sin PII y una ejecución del flujo elegido.

## Despliegue de los grupos

Cada grupo mantiene su servicio encendido y entrega una dirección accesible desde
el equipo del orquestador. `localhost`/`127.0.0.1` se refiere al equipo que ejecuta
la llamada; no sirve para conectar automáticamente otra laptop. Se recomienda
red privada/VPN. Si corren varias aplicaciones en una PC, acordar puertos: varios
proyectos usan 5000 por defecto, y Consentimientos y MCP Evidencias usan 8765.
No cambiar todos los proyectos para compartir una única base ni levantar ocho
copias de los modelos en la misma laptop.

## Estado visual y trazabilidad

"Por integrar" significa que no existe adaptador. "Sin comprobar" no implica
conectividad. "HTTP responde" no verifica identidad del servicio, calidad del
análisis, Ollama ni PostgreSQL. El resultado real de cada ejecución determina su
éxito; un HTTP 200 con campo `error` se trata como fallo. La comprobación de
conexiones solo usa GET y tiene espera máxima de tres segundos por servicio.

El panel muestra duración real y los pasos devueltos al finalizar. No inventa
progreso interno de LLM/RAG. El historial y las aprobaciones siguen en los agentes;
la persistencia central y el streaming de flujos son futuras mejoras.

## Límites y datos

No publicar servicios locales sin autenticación. No incluir claves en el catálogo,
URLs con credenciales, Git, resultados de prueba o capturas. Usar datos ficticios.
La interfaz sirve sus recursos localmente y no usa CDN ni telemetría externa.
