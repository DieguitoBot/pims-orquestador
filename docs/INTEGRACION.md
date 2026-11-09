# Plan de integración con los ocho agentes

## Estado
- **Registrados**: ocho repositorios identificados.
- **Adaptadores HTTP preliminares**: Incidentes y Riesgos; contratos sujetos a validación en ejecución.
- **Pendientes**: Evidencia y Auditoría, Consentimientos, DSAR, Privacy Coach, SoA Studio y Terceros.
- No afirmar integración real hasta superar pruebas extremo a extremo.

## Contrato mínimo requerido a cada grupo

1. Identificador y función del agente.
2. Mecanismo de acceso (URL HTTP autenticada o comando MCP).
3. Operaciones seguras de lectura/evaluación disponibles.
4. Un JSON de entrada y otro de salida **reales**, sin datos personales.
5. Estado de servicio y tiempos de respuesta esperados.
6. Qué tareas necesitan aprobación humana y cómo reanudarlas.
7. Referencia normativa y versión.

## Orden sugerido de trabajo
1. Probar Incidentes y Riesgos por separado con datos ficticios.
2. Validar el flujo conjunto Incidentes → Riesgos.
3. Añadir evidencia de auditoría mediante MCP/HTTP con aprobación humana.
4. Integrar Terceros (DPA) y su flujo de brechas.
5. Integrar DSAR, Consentimientos y Privacy Coach por sus operaciones específicas.
6. Integrar SoA Studio con cuidado: su núcleo es ISO/IEC 27001:2022, no debe equipararse automáticamente a ISO/IEC 27701:2025.
7. Definir un caso de extremo a extremo con métricas, auditoría y fallos controlados.

## Política de seguridad
No publicar servicios locales directamente en Internet. Preferir VPN privada, API keys por entorno y HTTPS. No compartir `.env` ni datasets con PII. Revisar derechos de acceso y políticas de conservación. Las aprobaciones humanas de agentes independientes se respetan: ningún orquestador puede saltarlas.

## Advertencia
`POST /api/analizar` y `POST /api/evaluar` son las rutas identificadas en la revisión inicial; sus *payloads* deben validarse con las implementaciones ejecutándose. Las pruebas de este repositorio usan respuestas simuladas y no demuestran compatibilidad real.
