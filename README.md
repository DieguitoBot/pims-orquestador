# PIMS Orquestador — UNSA

Prototipo de **orquestación externa** de ocho proyectos agénticos para un sistema de gestión de privacidad (PIMS). Conserva los repositorios originales: este servicio solo conoce sus interfaces y coordina los resultados.

> **Estado v0.1:** catálogo de ocho agentes; adaptadores HTTP iniciales para Incidentes y Riesgos; un flujo secuencial; pruebas con servicios simulados. **No se ha validado una ejecución real de los ocho agentes**. Los otros seis están registrados, no integrados.

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

Abrir http://127.0.0.1:9000/docs. Al inicio no es obligatorio levantar los agentes: el catálogo funciona, pero las llamadas externas fallarán de forma controlada si sus servicios no están disponibles.

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

Se usan transportes HTTP simulados: las pruebas no llaman a las laptops de los demás grupos.

## Proyectos

Consulta `app/registry.py` y `docs/INTEGRACION.md`. El proyecto cuenta **ocho repositorios independientes**, incluso cuando algunos incluyen subagentes internos.

## Seguridad y alcance

- No subas `.env`, contraseñas, contratos reales ni datos personales a Git.
- Usa ejemplos ficticios para demostraciones.
- El flujo no autoriza decisiones jurídicas ni acciones de escritura en sistemas de terceros.
- La puntuación de riesgos requiere probabilidad e impacto aportados por el usuario/sistema, no estimaciones inventadas.
- Antes de hacer una demo real: validar entradas y salidas de cada API, red privada, autenticación, tiempos de espera, aprobaciones humanas y correspondencias normativas ISO/IEC 27001 vs 27701.
