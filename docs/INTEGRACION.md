# Integración PIMS — arquitectura v0.3

## Una solicitud y cuatro contribuciones

El objetivo **Analizar incidente con proveedor** sigue este recorrido:

1. Incidentes recibe `descripcion_evento` y analiza el caso.
2. Terceros consulta la ficha del proveedor identificado, su DPA y su riesgo.
3. Evidencias consulta cobertura e integridad del expediente UNSA, sin modificarlo.
4. Riesgos recibe el escenario original y contexto atribuido de los servicios que
   respondieron; genera y guarda su evaluación con sus propias herramientas.
5. El orquestador reúne pasos, intercambios, pendientes e informe integrado.

El ID de proveedor debe elegirse del catálogo real; no se infiere por semejanza
de nombre. Las respuestas anteriores se etiquetan como contexto por contrastar,
no como nuevas verdades verificadas. Se limita el contexto enviado, señalando
truncamientos. Las respuestas completas se conservan en el resultado del flujo.

Si falla un grupo, Riesgos aún puede analizar el escenario y el contexto que sí
esté disponible. En ese caso el informe es **parcial**. Solo se marca completado
cuando las cuatro etapas terminaron correctamente. La revisión humana del
contenido sigue siendo necesaria incluso con estado completado.

## Adaptadores y contratos

| ID | Repositorio | Contrato | Estado |
|---|---|---|---|
| `riesgos` | [DieguitoBot/agente-riesgos-pims](https://github.com/DieguitoBot/agente-riesgos-pims) | POST `/api/evaluar`, GET `/api/status`; JSON de V3 | Implementado; prueba real individual previa en Ubuntu |
| `incidentes` | [jherson2024/agente_privacidad](https://github.com/jherson2024/agente_privacidad) | POST `/api/analizar` con `descripcion_evento` (máx. 2000) | Implementado; necesita prueba con el equipo del grupo |
| `terceros` | [S-kkipie/agente-terceros-dpa](https://github.com/S-kkipie/agente-terceros-dpa) | GET `/api/proveedores` para elegir ID, GET `/api/proveedores/<id>` devuelve DPA y riesgo | Implementado para consulta; no registra ni aprueba contratos |
| `evidencias` | [jhuamaniCond/auditoria-agente-tif-2](https://github.com/jhuamaniCond/auditoria-agente-tif-2) | GET `/api/agente/resumen` autenticado mediante sesión; MCP existe como alternativa | Implementado para cobertura/integridad; no registra evidencias |
| `dsar` | [JeremyCruzGallegos/agente-dsar-iso27701](https://github.com/JeremyCruzGallegos/agente-dsar-iso27701) | POST `/api/case-analysis`, X-API-Key | Puente preparado; adaptador de colaboración pendiente |
| `consentimientos` | [Dan-Ar5/Auditoria](https://github.com/Dan-Ar5/Auditoria) | POST `/api/auditar` devuelve NDJSON; alternativa MCP stdio | Puente preparado; adaptación especializada pendiente |
| `privacy_coach` | [DrN25/Privacy-Coach-Agent-ISO-27701](https://github.com/DrN25/Privacy-Coach-Agent-ISO-27701) | FastAPI/MCP para esquemas SQL y contratos | Sin operaciones de análisis expuestas por el puente todavía |
| `soa_studio` | [gcarrillov/SOA_estudio_agente_AUDITORIA](https://github.com/gcarrillov/SOA_estudio_agente_AUDITORIA) | Catálogo HTTP, JWT y ejecución agéntica | Solo catálogo en el puente; adaptación de ejecución pendiente |

El análisis de proveedor usa una matriz **4×4**. Riesgos conserva su **5×5**.
No sumar ni promediar sus puntuaciones. SoA parte de ISO/IEC 27001:2022, por lo
que necesita correspondencias justificadas antes de combinar sus conclusiones
con un PIMS ISO/IEC 27701:2025.

## Recursos distribuidos

Los agentes conservan modelos, corpus, datos y claves en sus propias computadoras.
Un puente mínimo escucha en localhost y permite solo rutas específicas con una
clave distinta de las credenciales internas. Tailscale Serve publica ese puente
dentro de la red privada del equipo. El orquestador consume esas URLs HTTPS;
no usa el `localhost` de Diego para localizar a sus compañeros.

Las claves del puente se importan mediante fichas privadas. Las contraseñas de
Evidencias y las claves internas de otros servicios permanecen en los grupos.
No se expone Ollama, PostgreSQL, pgAdmin ni rutas de reinicio/aprobación.

Comandos por grupo y por sistema operativo: [CONECTAR_GRUPOS.md](CONECTAR_GRUPOS.md).

## Progreso y retención

POST `/api/ejecuciones` inicia el objetivo y devuelve 202 con un ID. GET
`/api/ejecuciones/<id>` devuelve los estados reales de llamadas iniciadas y
terminadas. La pantalla consulta ese estado, sin inventar progreso de LLM/RAG.
Se permite un flujo coordinado activo a la vez. Su registro en memoria dura una
hora después de terminar; máximo 30 ejecuciones. Usar un solo worker de Uvicorn.
Al reiniciar, los historiales de los agentes permanecen pero este registro se pierde.
Antes de repetir un análisis interrumpido, consultar el historial de V3.

## Siguiente entrega

Después de la prueba distribuida de cuatro agentes: integrar DSAR y
Consentimientos para solicitudes específicas; luego Privacy Coach y SoA con sus
insumos y permisos. No ejecutar a los ocho sobre el mismo texto indiscriminadamente.
La gestión de evidencias del caso y las puertas de aprobación son un trabajo
posterior: el flujo actual consulta el expediente, no escribe en él.
