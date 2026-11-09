# PIMS Orquestador — UNSA

Prototipo de **orquestación externa** de ocho proyectos agénticos para un sistema de gestión de privacidad (PIMS). Conserva los repositorios originales: este servicio solo conoce sus interfaces y coordina los resultados.

> **Estado v0.2:** interfaz central en `/`, catálogo de ocho agentes, formulario de Riesgos/Incidentes, flujo secuencial y conectividad bajo demanda. Riesgos V3 ya fue probado por el usuario a través del orquestador en Ubuntu; los otros agentes no se han validado en ejecución conjunta. Seis adaptadores siguen pendientes.

## Arquitectura

```text
Cliente -> FastAPI (puerto 9000) -> registro + adaptadores
                                   |-> Incidentes /api/analizar (HTTP)
                                   |-> Riesgos /api/evaluar (HTTP)
                                   |-> seis agentes pendientes (HTTP/MCP)
```

La coordinación interna de cada agente (LLM, RAG, LangGraph, MCP, base de datos, aprobaciones) no se reemplaza.

## Inicio rápido (Ubuntu)

```bash
git clone https://github.com/DieguitoBot/pims-orquestador.git
cd pims-orquestador
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 127.0.0.1 --port 9000
```

Abrir **http://127.0.0.1:9000/** para el panel visual o http://127.0.0.1:9000/docs para Swagger. Al inicio no es obligatorio levantar los agentes: el catálogo funciona, pero las llamadas externas fallarán de forma controlada si sus servicios no están disponibles.

Configura las URLs reales de `RIESGOS_URL` e `INCIDENTES_URL` en `.env`. **127.0.0.1 es la computadora donde corre el orquestador**, no la PC de un compañero. Si los agentes corren en máquinas distintas, usa direcciones accesibles por VPN privada y autenticación. No expongas Ollama, PostgreSQL o paneles de administración.

## API

- `GET /health`: estado del orquestador.
- `GET /api/agentes`: ocho agentes, su función y estado de integración.
- `POST /api/agentes/{agente_id}/ejecutar`: llama a `incidentes` o `riesgos`, únicamente cuando están configurados.
- `POST /api/flujos/incidente-riesgo`: ejecuta primero Incidentes y después Riesgos.

Ejemplo de solicitud para el flujo:

```json
{
  "descripcion": "Acceso no autorizado a registros de estudiantes",
  "probabilidad": 3,
  "impacto": 4,
  "rol_privacidad": "responsable"
}
```

Ejemplo de prueba:

```bash
curl -X POST http://127.0.0.1:9000/api/flujos/incidente-riesgo \
  -H 'Content-Type: application/json' \
  -d '{"descripcion":"Acceso no autorizado a registros de estudiantes","probabilidad":3,"impacto":4}'
```

Si Incidentes no responde, se registra el error y el flujo se detiene (no inventa su resultado). El adaptador de Riesgos incluye la respuesta previa como contexto textual de la evaluación, delimitado en longitud. La compatibilidad precisa con cada versión de los proyectos deberá verificarse con sus responsables.

## Pruebas

```bash
python -m unittest discover -s tests -v
```

Las pruebas de Python usan transportes HTTP simulados: no llaman a las laptops de los demás grupos. La interfaz no requiere Node ni un servidor adicional para ejecutarse.

## Proyectos

Consulta `app/registry.py` y `docs/INTEGRACION.md`. El proyecto cuenta **ocho repositorios independientes**, incluso cuando algunos incluyen subagentes internos.

## Seguridad y alcance

- No subas `.env`, contraseñas, contratos reales ni datos personales a Git.
- Usa ejemplos ficticios para demostraciones.
- El flujo no autoriza decisiones jurídicas ni acciones de escritura en sistemas de terceros.
- La puntuación de riesgos requiere probabilidad e impacto aportados por el usuario/sistema, no estimaciones inventadas.
- Antes de hacer una demo real: validar entradas y salidas de cada API, red privada, autenticación, tiempos de espera, aprobaciones humanas y correspondencias normativas ISO/IEC 27001 vs 27701.


## Usar el panel central

1. Inicia Riesgos V3 en 8180 y configura `RIESGOS_URL=http://127.0.0.1:8180`.
2. Inicia el orquestador y abre http://127.0.0.1:9000/.
3. En **Vista general**, comprueba conexiones. "HTTP responde" solo verifica conectividad; no comprueba modelo, corpus ni persistencia.
4. **Nueva solicitud → Evaluación de Riesgos → Usar ejemplo ficticio → Ejecutar**.
5. Consulta el resumen, riesgos, medidas, fuentes y respuesta completa. Descarga el reporte o JSON.
6. Abre V3 desde el enlace del resultado para editar planes y verificar la evaluación en su historial.
7. **Flujos de trabajo** prepara Incidentes → Riesgos. Requiere ambos servicios configurados; Incidentes recibe `descripcion_evento` (máx. 2000 caracteres).
8. **Plan de integración** explica las dependencias de los ocho proyectos con enlaces reales a GitHub.

No hay historial central persistente ni aprobaciones en este panel: los datos continúan en cada agente. No se guardan resultados en localStorage. Las descargas solo se realizan al pulsar sus botones.

Al actualizar un clon existente, conserva tu `.env` y reinicia Uvicorn para leer los cambios. Si tu configuración aún usa el puerto 5000 para Riesgos, cámbiala a 8180 (o al puerto real de V3). Un `.env` existente no se sobrescribe al hacer `git pull`.


### Comprobar las interacciones de la interfaz (opcional)

Node no es necesario para usar el panel. Para repetir las pruebas DOM con Node 20.19+:

```bash
npm install --prefix /tmp/pims-panel-dom --no-audit --no-fund jsdom
NODE_PATH=/tmp/pims-panel-dom/node_modules node tests/panel_dom.cjs
```

Esta prueba comprueba formularios, navegación, catálogo, errores, selección de flujos,
salida segura y la prevención de envíos duplicados; usa respuestas simuladas y no
sustituye una prueba visual en Firefox ni una ejecución con los agentes reales.
