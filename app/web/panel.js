"use strict";
const $ = (id) => document.getElementById(id);
const state = { agents: [], response: null, report: null, busy: false };
const views = {
  panel: "Vista general",
  evaluar: "Nueva solicitud",
  flujos: "Flujos de trabajo",
  integracion: "Plan de integración",
};
const statuses = {
  sin_comprobar: ["Sin comprobar", "muted"],
  pendiente: ["Por integrar", "muted"],
  sin_configurar: ["Sin configurar", "amber"],
  responde: ["HTTP responde", "green"],
  no_responde: ["No responde", "red"],
  error: ["Revisar conexión", "red"],
};
const sample =
  "Caso ficticio: una oficina universitaria comparte DNI y correos de estudiantes mediante un enlace público sin restricciones de acceso.";
function el(tag, text, cls) {
  const n = document.createElement(tag);
  if (text !== undefined && text !== null) n.textContent = String(text);
  if (cls) n.className = cls;
  return n;
}
function link(label, url) {
  try {
    const u = new URL(url, location.origin);
    if (!["http:", "https:"].includes(u.protocol)) return el("span", label);
    const a = el("a", label);
    a.href = u.href;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    return a;
  } catch {
    return el("span", label);
  }
}
function badge(agent) {
  const key =
    agent.integracion === "pendiente" ? "pendiente" : agent.conectividad;
  const [label, cls] = statuses[key] || statuses.sin_comprobar;
  return el("span", label, "pill " + cls);
}
function activate(view, focus = true) {
  if (!views[view]) view = "panel";
  document
    .querySelectorAll(".view")
    .forEach((n) => (n.hidden = n.id !== "view-" + view));
  document.querySelectorAll(".nav-item").forEach((n) => {
    const yes = n.dataset.view === view;
    n.classList.toggle("active", yes);
    if (yes) n.setAttribute("aria-current", "page");
    else n.removeAttribute("aria-current");
  });
  $("breadcrumb").textContent = views[view];
  if (location.hash !== "#" + view) history.replaceState(null, "", "#" + view);
  if (focus) {
    const h = $("view-" + view).querySelector("h1");
    h.tabIndex = -1;
    h.focus({ preventScroll: true });
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
}
function choose(id) {
  $("operation").value = id;
  updateOperation();
  activate("evaluar");
}
function renderAgents() {
  const grid = $("agent-grid");
  grid.replaceChildren();
  const ordered = [...state.agents].sort((a, b) =>
    a.id === "riesgos" ? -1 : b.id === "riesgos" ? 1 : 0,
  );
  for (const a of ordered) {
    const card = el(
      "article",
      null,
      "agent-card" + (a.id === "riesgos" ? " highlight" : ""),
    );
    const top = el("div", null, "card-top");
    top.append(el("span", a.sigla, "agent-icon"), badge(a));
    card.append(top, el("h3", a.nombre), el("p", a.descripcion));
    const bottom = el("div", null, "card-bottom");
    bottom.append(
      el("span", a.operacion ? "Adaptador HTTP" : "Adaptador pendiente"),
    );
    const b = el(
      "button",
      a.operacion ? "Preparar solicitud ↗" : "Ver integración →",
      "text-button",
    );
    b.type = "button";
    b.addEventListener("click", () => (a.operacion ? choose(a.id) : detail(a)));
    bottom.append(b);
    card.append(bottom);
    grid.append(card);
  }
  $("count-agents").textContent = String(state.agents.length).padStart(2, "0");
  $("count-adapters").textContent = String(
    state.agents.filter((a) => a.operacion).length,
  ).padStart(2, "0");
  if (
    state.agents.some(
      (a) => !["sin_comprobar", "pendiente"].includes(a.conectividad),
    )
  )
    $("count-online").textContent = String(
      state.agents.filter((a) => a.conectividad === "responde").length,
    ).padStart(2, "0");
  renderPlan();
}
function detail(a) {
  const root = $("agent-detail");
  root.replaceChildren(
    el("span", a.sigla, "agent-icon"),
    el("h2", a.nombre),
    badge(a),
    el("p", a.descripcion),
  );
  const dl = el("dl");
  for (const [label, value] of [
    ["Recibe", a.entrada],
    ["Devuelve", a.salida],
    ["Siguiente conexión", a.siguiente_paso],
  ])
    dl.append(el("dt", label), el("dd", value));
  root.append(dl, link("Revisar repositorio ↗", a.repositorio));
  $("agent-dialog").showModal();
}
function renderPlan() {
  const titles = {
    1: "01 · Consolidar Riesgos V3",
    2: "02 · Validar Incidentes y el primer flujo",
    3: "03 · Incorporar evidencias y proveedores",
    4: "04 · Derechos y consentimientos",
    5: "05 · Revisión técnica y aplicabilidad",
  };
  const root = $("integration-plan");
  root.replaceChildren();
  for (const phase of [1, 2, 3, 4, 5]) {
    const section = el("section", null, "plan-phase");
    section.append(el("h2", titles[phase]));
    for (const a of state.agents.filter((a) => a.fase === phase)) {
      const row = el("article", null, "plan-row");
      const title = el("div");
      title.append(el("h3", a.nombre), badge(a));
      row.append(
        title,
        el("p", a.siguiente_paso),
        link("Repositorio ↗", a.repositorio),
      );
      section.append(row);
    }
    root.append(section);
  }
}
async function loadCatalog() {
  try {
    const r = await fetch("/api/agentes");
    if (!r.ok) throw Error();
    state.agents = await r.json();
    renderAgents();
    $("server-dot").className = "ok";
    $("server-label").textContent = "Orquestador activo";
  } catch {
    $("server-dot").className = "error";
    $("server-label").textContent = "Sin conexión";
    $("connection-notice").textContent =
      "No se pudo cargar el catálogo. Comprueba el servidor y recarga la página.";
  }
}
async function checkConnections() {
  const b = $("check-connections");
  b.disabled = true;
  b.textContent = "Comprobando…";
  try {
    const r = await fetch("/api/agentes/estado");
    if (!r.ok) throw Error();
    const data = await r.json();
    state.agents = data.agentes;
    renderAgents();
    $("connection-notice").textContent =
      "Comprobado a las " +
      new Date(data.comprobado).toLocaleTimeString("es-PE") +
      ". HTTP responde confirma conectividad; prueba una evaluación para verificar modelo y persistencia.";
  } catch {
    $("connection-notice").textContent =
      "No se pudo comprobar la conectividad. Verifica que el orquestador siga activo.";
  } finally {
    b.disabled = false;
    b.textContent = "↻ Comprobar conexiones";
  }
}
function updateOperation() {
  const op = $("operation").value;
  $("risk-fields").hidden = op === "incidentes";
  $("flow-caution").hidden = op !== "flujo";
  $("description").maxLength = op === "riesgos" ? 5000 : 2000;
  const help = {
    riesgos:
      "Envía el caso a V3 y devuelve su evaluación. El agente conserva el resultado en su propia base.",
    incidentes:
      "Envía la descripción al servicio de Incidentes. Debe estar ejecutándose y configurado en el orquestador.",
    flujo:
      "Coordina Incidentes → Riesgos: la respuesta del primer agente se añade como contexto a la evaluación.",
  };
  $("operation-help").textContent = help[op];
  const routes = {
    riesgos: [
      ["Orquestador", "Valida y envía tu solicitud."],
      [
        "Riesgos V3",
        "Consulta fuentes, analiza y guarda la evaluación con IA.",
      ],
      ["Resultado", "Devuelve el análisis para tu revisión."],
    ],
    incidentes: [
      ["Orquestador", "Envía el escenario al servicio de Incidentes."],
      ["Incidentes", "Analiza el evento con sus propias herramientas."],
      ["Resultado", "Devuelve la respuesta del agente."],
    ],
    flujo: [
      ["Incidentes", "Primer análisis del evento."],
      ["Riesgos V3", "Recibe el escenario y el contexto de Incidentes."],
      ["Consolidación", "Reúne los resultados; se detiene si falla un paso."],
    ],
  };
  $("route-list").replaceChildren(
    ...routes[op].map(([title, subtitle]) => {
      const li = el("li", title);
      li.append(el("small", subtitle));
      return li;
    }),
  );
}
function addList(root, title, values) {
  if (!Array.isArray(values) || !values.length) return;
  const box = el("section", null, "result-block");
  box.append(el("h3", title));
  const ul = el("ul");
  values.forEach((v) =>
    ul.append(el("li", typeof v === "string" ? v : JSON.stringify(v))),
  );
  box.append(ul);
  root.append(box);
}
function renderResult(response, seconds) {
  state.response = response;
  state.report = null;
  const root = $("result-content");
  root.replaceChildren();
  $("result-panel").hidden = false;
  $("raw-result").textContent = JSON.stringify(response, null, 2);
  const steps = Array.isArray(response.pasos) ? response.pasos : [response];
  $("result-title").textContent =
    response.estado === "completado"
      ? "Solicitud completada"
      : "La solicitud necesita atención";
  root.append(
    el(
      "p",
      "Duración: " +
        seconds +
        " s" +
        (response.solicitud_id ? " · Solicitud " + response.solicitud_id : ""),
      "quiet",
    ),
  );
  for (const s of steps) {
    const row = el("div", null, "trace-step");
    const a = state.agents.find((a) => a.id === s.agente);
    row.append(
      el("strong", a ? a.nombre : s.agente || "Servicio"),
      el(
        "span",
        s.estado || "error",
        "pill " + (s.estado === "completado" ? "green" : "red"),
      ),
    );
    root.append(row);
    if (s.error) root.append(el("p", s.error, "result-alert"));
  }
  if (response.mensaje) root.append(el("p", response.mensaje, "quiet"));
  const rs = steps.find(
    (s) => s.agente === "riesgos" && s.estado === "completado",
  );
  const q = rs && rs.resultado;
  if (q && typeof q === "object" && !Array.isArray(q)) {
    const summary = el("div", null, "result-summary");
    for (const [value, label] of [
      [
        q.puntaje !== undefined ? q.puntaje + "/25" : "Sin cifra",
        "Valoración inicial · " + (q.nivel || "Sin nivel"),
      ],
      [
        q.reporte_ia_generado ? "Generado con IA" : "Sin reporte IA",
        q.modelo || "Consulta la respuesta completa",
      ],
      [
        q.experimento_id ? "Guardada en V3" : "Sin ID de guardado",
        q.experimento_id || "Verifica la persistencia",
      ],
    ]) {
      const cell = el("div");
      cell.append(el("strong", value), el("span", label));
      summary.append(cell);
    }
    root.append(summary);
    const ia = q.analisis_ia || {};
    if (ia.justificacion) {
      const box = el("section", null, "result-block");
      box.append(el("h3", "Justificación"), el("p", ia.justificacion, "quiet"));
      root.append(box);
    }
    if (Array.isArray(ia.riesgos_identificados)) {
      const box = el("section", null, "result-block");
      box.append(el("h3", "Riesgos y medidas propuestas"));
      for (const risk of ia.riesgos_identificados) {
        const item = el("article", null, "finding");
        if (typeof risk === "string") item.append(el("strong", risk));
        else if (risk) {
          item.append(el("strong", risk.riesgo || "Riesgo identificado"));
          for (const [label, key] of [
            ["Hecho declarado", "evidencia"],
            ["Medida propuesta", "medida_concreta"],
            ["Verificación", "verificacion"],
          ])
            if (risk[key]) item.append(el("p", label + ": " + risk[key]));
        }
        box.append(item);
      }
      root.append(box);
    }
    addList(root, "Recomendaciones", ia.recomendaciones);
    addList(root, "Aspectos pendientes de revisión", q.avisos_revision);
    addList(root, "Alertas de contenido", q.alertas_contenido);
    root.append(
      el(
        "p",
        "Distingue hechos descritos de supuestos del modelo. Una cita cotejada acredita su procedencia textual, no confirma por sí sola un incumplimiento.",
        "result-alert",
      ),
    );
    if (Array.isArray(q.fuentes_rag) && q.fuentes_rag.length) {
      const d = el("details");
      d.append(el("summary", q.fuentes_rag.length + " fuentes recuperadas"));
      const ul = el("ul");
      q.fuentes_rag.forEach((f) =>
        ul.append(
          el(
            "li",
            (f.archivo || "Fuente") + (f.pagina ? " · página " + f.pagina : ""),
          ),
        ),
      );
      d.append(ul);
      root.append(d);
    }
    const a = state.agents.find((a) => a.id === "riesgos");
    if (a && a.interfaz_url)
      root.append(
        link(
          "Abrir V3 para consultar historial y editar planes ↗",
          a.interfaz_url,
        ),
      );
    if (typeof q.reporte_texto === "string" && q.reporte_texto)
      state.report = q.reporte_texto;
  } else if (steps.some((s) => s.estado === "completado"))
    root.append(
      el(
        "p",
        "El agente respondió. Su resultado especializado está disponible en la respuesta JSON completa y en la descarga.",
        "quiet",
      ),
    );
  $("download-report").hidden = !state.report;
}
async function execute(event) {
  event.preventDefault();
  if (state.busy) return;
  const op = $("operation").value;
  const description = $("description").value.trim();
  if (
    description.length < 10 ||
    description.length > $("description").maxLength
  ) {
    $("description").setCustomValidity(
      "Escribe un escenario dentro del límite indicado.",
    );
    $("description").reportValidity();
    return;
  }
  $("description").setCustomValidity("");
  const risk = {
    descripcion: description,
    probabilidad: Number($("probability").value),
    impacto: Number($("impact").value),
    rol_privacidad: $("privacy-role").value,
    exigir_ia: $("require-ai").checked,
  };
  const url =
    op === "flujo"
      ? "/api/flujos/incidente-riesgo"
      : "/api/agentes/" + op + "/ejecutar";
  const payload =
    op === "flujo"
      ? risk
      : {
          entrada:
            op === "riesgos" ? risk : { descripcion_evento: description },
        };
  state.busy = true;
  $("execute").disabled = true;
  $("execute").textContent = "Solicitud en curso…";
  $("result-panel").hidden = true;
  const started = performance.now();
  const status = $("execution-status");
  status.hidden = false;
  status.className = "execution-status";
  const update = () => {
    status.textContent =
      "Solicitud enviada. Esperando respuesta " +
      (op === "flujo" ? "de los agentes" : "del agente") +
      "… " +
      Math.round((performance.now() - started) / 1000) +
      " s. No cierres esta página.";
  };
  update();
  const ticker = setInterval(update, 1000);
  const controller = new AbortController();
  const timeout = setTimeout(
    () => controller.abort(),
    op === "flujo" ? 620000 : 310000,
  );
  try {
    const r = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });
    const response = await r.json();
    if (!r.ok)
      throw Error(
        typeof response.detail === "string"
          ? response.detail
          : "El servidor rechazó la solicitud. Revisa los datos o la conexión.",
      );
    const seconds = Math.round((performance.now() - started) / 1000);
    renderResult(response, seconds);
    status.className =
      "execution-status" + (response.estado === "completado" ? "" : " error");
    status.textContent =
      response.estado === "completado"
        ? "Respuesta recibida en " +
          seconds +
          " s. Revisa el resultado antes de utilizarlo."
        : "La ejecución no se completó. Consulta el paso y el error que aparecen debajo.";
  } catch (error) {
    status.className = "execution-status error";
    status.textContent =
      error.name === "AbortError"
        ? "Se agotó la espera del navegador. El agente podría seguir procesando; revisa el historial de V3 antes de repetir la solicitud."
        : error instanceof TypeError
          ? "Se perdió la conexión con el orquestador. Revisa su terminal y el historial del agente antes de repetir."
          : error.message;
  } finally {
    clearInterval(ticker);
    clearTimeout(timeout);
    state.busy = false;
    $("execute").disabled = false;
    $("execute").textContent = "Ejecutar solicitud →";
  }
}
function download(content, filename, type) {
  if (!content) return;
  const url = URL.createObjectURL(new Blob([content], { type }));
  const a = el("a");
  a.href = url;
  a.download = filename;
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
document
  .querySelectorAll("[data-view]")
  .forEach((b) => b.addEventListener("click", () => activate(b.dataset.view)));
window.addEventListener("hashchange", () => activate(location.hash.slice(1)));
$("new-request").addEventListener("click", () => choose("riesgos"));
$("open-flow").addEventListener("click", () => choose("flujo"));
$("operation").addEventListener("change", updateOperation);
$("example").addEventListener("click", () => {
  $("description").value = sample;
  $("description").setCustomValidity("");
});
$("description").addEventListener("input", () =>
  $("description").setCustomValidity(""),
);
$("request-form").addEventListener("submit", execute);
$("check-connections").addEventListener("click", checkConnections);
$("close-dialog").addEventListener("click", () => $("agent-dialog").close());
$("download-result").addEventListener("click", () =>
  download(
    JSON.stringify(state.response, null, 2),
    "pims-resultado.json",
    "application/json;charset=utf-8",
  ),
);
$("download-report").addEventListener("click", () =>
  download(state.report, "pims-reporte.txt", "text/plain;charset=utf-8"),
);
activate(location.hash.slice(1), false);
updateOperation();
loadCatalog();
