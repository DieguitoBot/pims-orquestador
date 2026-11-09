# Validación de colaboración distribuida — 09/11/2026

## Estado actual v0.3

- 21 pruebas Python aprobadas.
- Prueba DOM aprobada con inicio del objetivo, consulta de progreso, cuatro
  resultados, intercambios de contexto e informe integrado.
- La prueba HTTP simulada comprueba que Riesgos recibe datos de Incidentes,
  Terceros y Evidencias, sin claves internas ni contactos del proveedor.
- Se comprueban fallos parciales, datos ausentes, no duplicación de flujos,
  contratos de proveedores y acceso autorizado del puente.
- El puente rechaza operaciones destructivas y destinos que no sean localhost.
- Las fichas de conexión se crean e importan en directorios temporales; los
  tests no modifican la configuración de ningún compañero.

No se han conectado las laptops reales mediante Tailscale ni se han ejecutado
los agentes de los compañeros desde este entorno. La prueba distribuida real se
realiza siguiendo [la guía del equipo](CONECTAR_GRUPOS.md). El entorno no permite
iniciar Chromium: continúa pendiente una revisión visual de los nuevos estados.

## Aceptación en la red del equipo

1. Incidentes, Terceros, Evidencias y Riesgos activos en sus respectivas máquinas.
2. Los puentes remotos responden y sus fichas están importadas en el orquestador.
3. El catálogo de proveedores se consulta desde el formulario central.
4. Una solicitud produce cuatro etapas reales y tres intercambios hacia Riesgos.
5. El informe conserva el ID que puede recuperarse en el historial de V3.
6. Al apagar un compañero, la siguiente ejecución queda parcial y señala ese
   servicio; no lo marca como completado ni inventa su resultado.
7. Los documentos y decisiones siguen en sus agentes; Evidencias no registra el
   informe automáticamente y los contratos no se aprueban desde este flujo.

## Base visual anterior

Se mantienen Newsreader y Public Sans locales con sus licencias, el directorio
en filas y la navegación horizontal. Las pruebas DOM no sustituyen inspección
visual en Firefox ni una evaluación de accesibilidad completa.
