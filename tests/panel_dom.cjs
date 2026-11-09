/* Pruebas DOM opcionales: NODE_PATH=/tmp/pims-panel-dom/node_modules node tests/panel_dom.cjs */
const fs = require("node:fs");
const path = require("node:path");
const assert = require("node:assert/strict");
const { execFileSync } = require("node:child_process");
const { JSDOM, VirtualConsole } = require("jsdom");
const root = path.join(__dirname, "..");
const agents = JSON.parse(
  execFileSync(
    process.env.PYTHON || "python",
    [
      "-c",
      "import json; from app.status import catalogo; print(json.dumps(catalogo()))",
    ],
    {
      cwd: root,
      encoding: "utf8",
      env: {
        ...process.env,
        RIESGOS_URL: "http://127.0.0.1:8180",
        INCIDENTES_URL: "",
      },
    },
  ),
);
const errors = [];
const vc = new VirtualConsole();
vc.on("jsdomError", (e) => errors.push(e.message));
const dom = new JSDOM(
  fs.readFileSync(path.join(root, "app/web/index.html"), "utf8"),
  { url: "http://pims.local/", runScripts: "outside-only", virtualConsole: vc },
);
const w = dom.window;
w.scrollTo = () => {};
w.HTMLDialogElement.prototype.showModal = function () {
  this.open = true;
};
w.HTMLDialogElement.prototype.close = function () {
  this.open = false;
};
const calls = [];
let nextResponse = {
  agente: "riesgos",
  estado: "completado",
  resultado: {
    puntaje: 16,
    nivel: "Alto",
    modelo: "modelo-prueba",
    reporte_ia_generado: true,
    experimento_id: "id-prueba",
    reporte_texto: "Reporte de prueba",
    analisis_ia: {
      justificacion: "<img src=x onerror=alert(1)>",
      riesgos_identificados: [
        { riesgo: "Acceso público", medida_concreta: "Restringir acceso" },
      ],
    },
    fuentes_rag: [{ archivo: "fuente.md" }],
  },
};
w.fetch = async (url, options) => {
  if (!options || !options.method) {
    if (url.startsWith("/api/ejecuciones/"))
      return { ok: true, json: async () => nextResponse };
    if (url === "/api/agentes/estado")
      return {
        ok: true,
        json: async () => ({
          comprobado: new Date().toISOString(),
          agentes: agents.map((a) => ({
            ...a,
            conectividad:
              a.id === "riesgos"
                ? "responde"
                : a.id === "incidentes"
                  ? "sin_configurar"
                  : "pendiente",
          })),
        }),
      };
    return { ok: true, json: async () => agents };
  }
  calls.push({ url, body: JSON.parse(options.body) });
  if (url === "/api/ejecuciones")
    return {
      ok: true,
      json: async () => ({
        solicitud_id: "flujo-prueba",
        estado: "en_curso",
        pasos: [
          {
            agente: "incidentes",
            titulo: "Analizar incidente",
            estado: "en_curso",
          },
        ],
      }),
    };
  await new Promise((resolve) => setTimeout(resolve, 10));
  return { ok: true, json: async () => nextResponse };
};
const $ = (id) => w.document.getElementById(id);
const waitFor = async (predicate) => {
  for (let i = 0; i < 400; i++) {
    if (predicate()) return;
    await new Promise((r) => setTimeout(r, 5));
  }
  throw new Error("DOM condition timed out");
};
function submit() {
  $("request-form").dispatchEvent(
    new w.Event("submit", { bubbles: true, cancelable: true }),
  );
}
(async () => {
  w.eval(fs.readFileSync(path.join(root, "app/web/panel.js"), "utf8"));
  await waitFor(() => w.document.querySelectorAll(".agent-card").length === 8);
  assert.equal($("count-agents").textContent, "08");
  assert.equal($("count-adapters").textContent, "04");
  assert.equal($("count-online").textContent, "—");
  assert.equal(w.document.querySelectorAll(".plan-row").length, 8);
  $("check-connections").click();
  await waitFor(() => !$("check-connections").disabled);
  assert.equal($("count-online").textContent, "01");
  $("new-request").click();
  assert.equal($("view-evaluar").hidden, false);
  $("operation").value = "riesgos";
  $("operation").dispatchEvent(new w.Event("change"));
  $("example").click();
  submit();
  submit();
  await waitFor(() => !$("execute").disabled);
  assert.equal(calls.length, 1, "No duplicar una ejecución en curso");
  assert.equal(calls[0].url, "/api/agentes/riesgos/ejecutar");
  assert.equal(calls[0].body.entrada.probabilidad, 4);
  assert.equal(calls[0].body.entrada.exigir_ia, true);
  assert.equal($("result-title").textContent, "Solicitud completada");
  assert($("result-content").textContent.includes("Guardada en V3"));
  assert.equal(
    $("result-content").querySelectorAll("img").length,
    0,
    "La salida del modelo nunca se interpreta como HTML",
  );
  assert.equal($("download-report").hidden, false);
  assert(
    $("result-content")
      .querySelector("a")
      .href.startsWith("http://127.0.0.1:8180"),
  );
  $("operation").value = "incidentes";
  $("operation").dispatchEvent(new w.Event("change"));
  assert.equal($("risk-fields").hidden, true);
  assert.equal($("description").maxLength, 2000);
  nextResponse = {
    agente: "incidentes",
    estado: "no_configurado",
    error: "Falta URL del agente",
  };
  submit();
  await waitFor(() => !$("execute").disabled);
  assert.equal(calls[1].url, "/api/agentes/incidentes/ejecutar");
  assert.equal(typeof calls[1].body.entrada.descripcion_evento, "string");
  assert.equal("descripcion" in calls[1].body.entrada, false);
  assert($("result-content").textContent.includes("Falta URL del agente"));
  $("open-flow").click();
  assert.equal($("operation").value, "objetivo");
  assert.equal($("flow-caution").hidden, false);
  $("operation").value = "flujo";
  $("operation").dispatchEvent(new w.Event("change"));
  nextResponse = {
    estado: "incompleto",
    pasos: [
      { agente: "incidentes", estado: "error", error: "HTTP 503 del agente" },
    ],
    mensaje: "No se ejecutó Riesgos.",
  };
  submit();
  await waitFor(() => !$("execute").disabled);
  assert.equal(calls[2].url, "/api/flujos/incidente-riesgo");
  assert.equal(calls[2].body.probabilidad, 4);
  assert.equal(calls[2].body.exigir_ia, true);
  assert.equal($("result-title").textContent, "La solicitud necesita atención");
  assert($("result-content").textContent.includes("No se ejecutó Riesgos."));
  const pendingButton = [
    ...w.document.querySelectorAll(".agent-card button"),
  ].find((b) => b.textContent.includes("Ver detalle"));
  pendingButton.click();
  assert.equal($("agent-dialog").open, true);
  assert(
    $("agent-detail").querySelector("a").href.startsWith("https://github.com/"),
  );
  $("close-dialog").click();
  assert.equal($("agent-dialog").open, false);
  $("new-request").click();
  $("provider-id").value = "4";
  nextResponse = {
    solicitud_id: "flujo-prueba",
    objetivo: "incidente_proveedor",
    estado: "completado",
    pasos: [
      {
        agente: "incidentes",
        estado: "completado",
        resultado: { evento: "enlace abierto" },
      },
      {
        agente: "terceros",
        estado: "completado",
        resultado: { dpa: { estado: "vencido" } },
      },
      {
        agente: "evidencias",
        estado: "completado",
        resultado: { porcentaje_cobertura: 50 },
      },
      {
        agente: "riesgos",
        estado: "completado",
        resultado: { puntaje: 16, experimento_id: "id-guardado" },
      },
    ],
    resumen: {
      agentes_con_resultado: [
        "incidentes",
        "terceros",
        "evidencias",
        "riesgos",
      ],
      colaboracion_efectiva: true,
    },
    intercambios: [{ origen: "terceros", destino: "riesgos", uso: "contexto" }],
    pendientes: [{ agente: "revision_humana", accion: "Revisar" }],
    informe_integrado: "Reporte integrado de prueba",
  };
  submit();
  await waitFor(() => !$("execute").disabled);
  assert.equal(calls[3].url, "/api/ejecuciones");
  assert.equal(calls[3].body.proveedor_id, 4);
  assert.equal($("live-progress").hidden, false);
  assert.equal($("live-steps").querySelectorAll(".trace-step").length, 4);
  assert($("result-content").textContent.includes("4 de 4 agentes"));
  assert($("result-content").textContent.includes("terceros → riesgos"));
  assert.equal($("download-report").hidden, false);
  assert.deepEqual(errors, []);
  console.log(
    "DOM OK: catálogo, navegación, conexiones, formulario real, errores, flujo, modal y salida segura.",
  );
})()
  .catch((e) => {
    console.error(e);
    process.exitCode = 1;
  })
  .finally(() => dom.window.close());
