const roleSelect = document.getElementById("role");
const loginButton = document.getElementById("login");
const kpis = document.getElementById("kpis");
const content = document.getElementById("content");
const title = document.getElementById("view-title");
const note = document.getElementById("view-note");
const updated = document.getElementById("updated");
const roleButtons = Array.from(document.querySelectorAll(".role-button"));
const supportRegion = document.getElementById("support-region");
const visualGrid = document.getElementById("visual-grid");
const filtersRegion = document.getElementById("filters");
const API_BASE = "http://127.0.0.1:8770";

const filters = {
  search: document.getElementById("search"),
  incident: document.getElementById("incident-filter"),
  type: document.getElementById("type-filter"),
  verification: document.getElementById("verification-filter"),
  legal: document.getElementById("legal-filter"),
  access: document.getElementById("access-filter"),
  safety: document.getElementById("safety-filter")
};

const notes = {
  leadership: "Strategic readiness, risk, and operational posture.",
  investigations: "Working queue for verification, custody repair, and case analysis.",
  legal: "Items ready or waiting for legal review and controlled disclosure decisions.",
  partners: "Partner-facing process improvements for collection, transfer, and custody logging.",
  data_protection: "Restricted records, source risk, retention, access, and DPIA triggers.",
  ai: "Assistive GenAI pilot lanes, backlog acceleration, controls, and human review requirements.",
  media: "NoSQL media catalog with scanned synthetic sample objects.",
  monitoring: "Operational, security, performance, and data-skew monitoring."
};

let activeRole = "leadership";
let latestData = null;
let latestSource = "waiting";
let accessToken = "";
let tokenRole = "";

loginButton.addEventListener("click", () => {
  activeRole = roleSelect.value;
  syncRoleNav();
  authenticateAndLoad();
});

roleButtons.forEach(button => {
  button.addEventListener("click", () => {
    activeRole = button.dataset.role;
    roleSelect.value = activeRole;
    syncRoleNav();
    authenticateAndLoad();
  });
});

document.getElementById("clear-filters").addEventListener("click", () => {
  Object.values(filters).forEach(filter => { filter.value = ""; });
  render();
});

Object.values(filters).forEach(filter => {
  filter.addEventListener("input", render);
  filter.addEventListener("change", render);
});

async function load() {
  try {
    if (!accessToken || tokenRole !== activeRole) {
      await authenticateRole(activeRole);
    }
    const loaded = await loadDashboardSnapshot();
    latestData = loaded.data;
    latestSource = loaded.source;
    populateFilters(latestData.investigations || []);
    render();
    renderUpdatedStatus();
  } catch (error) {
    latestSource = "auth-error";
    renderUpdatedStatus();
    content.innerHTML = `<div class="empty">Access failed. Check that the API is running and the demo password is correct.</div>`;
  }
}

async function authenticateAndLoad() {
  accessToken = "";
  tokenRole = "";
  await load();
}

async function authenticateRole(role) {
  const response = await fetch(`${API_BASE}/api/auth/demo-login`, {
    method: "POST",
    cache: "no-store",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      role,
      password: document.getElementById("password").value
    })
  });
  if (!response.ok) throw new Error(`Demo login returned ${response.status}`);
  const payload = await response.json();
  accessToken = payload.access_token || "";
  tokenRole = payload.role || "";
}

async function loadDashboardSnapshot() {
  try {
    const timestamp = Date.now();
    const authHeaders = { Authorization: `Bearer ${accessToken}` };
    const [snapshotResponse, roleResponse] = await Promise.all([
      fetch(`${API_BASE}/api/dashboard?ts=${timestamp}`, { cache: "no-store", headers: authHeaders }),
      fetch(`${API_BASE}/api/dashboard/${activeRole}?ts=${timestamp}`, { cache: "no-store", headers: authHeaders })
    ]);
    if ([401, 403].includes(roleResponse.status)) {
      throw new Error(`AUTH_BLOCKED:${roleResponse.status}`);
    }
    if (!roleResponse.ok) throw new Error(`API role view returned ${roleResponse.status}`);
    const roleView = await roleResponse.json();
    if ([401, 403].includes(snapshotResponse.status)) {
      return { data: roleOnlySnapshot(roleView), source: "role-api" };
    }
    if (!snapshotResponse.ok) throw new Error(`API snapshot returned ${snapshotResponse.status}`);
    const snapshot = await snapshotResponse.json();
    return { data: mergeRoleView(snapshot, roleView), source: "role-api" };
  } catch (error) {
    if (String(error.message || "").startsWith("AUTH_BLOCKED:")) {
      throw error;
    }
    const response = await fetch(`/dashboard/data.json?ts=${Date.now()}`, { cache: "no-store" });
    if (!response.ok) throw new Error(`Fallback snapshot returned ${response.status}`);
    return { data: await response.json(), source: "fallback" };
  }
}

function roleOnlySnapshot(roleView) {
  const rows = Array.isArray(roleView.data) ? roleView.data : [];
  return {
    generated_at: roleView.generated_at,
    kpis: roleView.kpis || {},
    charts: roleView.charts || {},
    leadership: roleView.role === "leadership" ? rows : [],
    investigations: roleView.role === "investigations" ? rows : [],
    legal: roleView.role === "legal" ? rows : [],
    partners: roleView.role === "partners" ? rows : [],
    data_protection: roleView.role === "data_protection" ? rows : [],
    ai: roleView.role === "ai" ? rows : [],
    media: roleView.role === "media" ? rows : [],
    monitoring: roleView.role === "monitoring" ? rows : [],
    ai_recommendations: roleView.ai_recommendations || {},
    notifications: roleView.notifications || {}
  };
}

function mergeRoleView(snapshot, roleView) {
  if (!roleView?.role || !Array.isArray(roleView.data)) return snapshot;
  return {
    ...snapshot,
    generated_at: roleView.generated_at || snapshot.generated_at,
    kpis: roleView.kpis || snapshot.kpis,
    charts: roleView.charts || snapshot.charts,
    ai_recommendations: roleView.ai_recommendations || snapshot.ai_recommendations,
    notifications: roleView.notifications || snapshot.notifications,
    [roleView.role]: roleView.data
  };
}

function renderUpdatedStatus() {
  const generatedAt = latestData?.generated_at ? new Date(latestData.generated_at).toLocaleString() : "unknown";
  const sourceLabels = {
    "role-api": "Role API online",
    api: "API online",
    fallback: "API offline fallback",
    "auth-error": "Access error",
    waiting: "Waiting for data"
  };
  const sourceClass = ["api", "role-api"].includes(latestSource) ? "online" : latestSource === "fallback" ? "fallback" : "waiting";
  updated.innerHTML = `
    <span class="source-badge ${sourceClass}">${sourceLabels[latestSource] || "Unknown source"}</span>
    <span>Updated ${generatedAt}</span>
  `;
}

function render() {
  if (!latestData) return;
  document.body.dataset.role = activeRole;
  syncRoleNav();
  const filtered = filterRows(latestData.investigations || []);
  const viewData = withFilteredData(latestData, filtered);
  renderKpis(kpiFromRows(filtered));
  renderCharts(filtered);
  renderRole(viewData, filtered);
  applyRoleLayout();
}

function populateFilters(rows) {
  fillSelect(filters.incident, rows.map(row => row.incident_code), "All incidents");
  fillSelect(filters.type, rows.map(row => row.media_type), "All media types");
  fillSelect(filters.verification, rows.map(row => row.verification_status), "All verification states");
  fillSelect(filters.legal, rows.map(row => row.legal_status), "All legal states");
  fillSelect(filters.access, rows.map(row => row.access_classification), "All access classes");
  fillSelect(filters.safety, rows.map(row => row.safe_status || "not_scanned"), "All safety states");
}

function fillSelect(select, values, label) {
  const selected = select.value;
  const options = [...new Set(values.filter(Boolean))].sort();
  select.innerHTML = `<option value="">${label}</option>` + options.map(value => (
    `<option value="${escapeHtml(value)}">${human(value)}</option>`
  )).join("");
  select.value = options.includes(selected) ? selected : "";
}

function filterRows(rows) {
  const term = filters.search.value.toLowerCase().trim();
  return rows.filter(row => {
    const searchText = [
      row.original_filename,
      row.incident_code,
      row.title,
      row.source_code,
      row.media_type,
      row.legal_status,
      row.verification_status
    ].join(" ").toLowerCase();
    return (!term || searchText.includes(term))
      && (!filters.incident.value || row.incident_code === filters.incident.value)
      && (!filters.type.value || row.media_type === filters.type.value)
      && (!filters.verification.value || row.verification_status === filters.verification.value)
      && (!filters.legal.value || row.legal_status === filters.legal.value)
      && (!filters.access.value || row.access_classification === filters.access.value)
      && (!filters.safety.value || (row.safe_status || "not_scanned") === filters.safety.value);
  });
}

function withFilteredData(data, rows) {
  const ids = new Set(rows.map(row => String(row.media_id)));
  return {
    ...data,
    leadership: incidentSummary(rows),
    investigations: rows,
    legal: rows.filter(row => row.legal_status === "approved_for_legal_use" || row.legal_status === "needs_review" || row.legal_status === "not_reviewed"),
    partners: rows.filter(row => Number(row.custody_events) === 0),
    data_protection: rows.filter(row => row.access_classification === "restricted"),
    ai: (data.ai || []).filter(row => ids.has(String(row.media_id))),
    ai_recommendations: data.ai_recommendations || {},
    notifications: data.notifications || {},
    media: (data.media || []).filter(row => ids.has(String(row.media_id))),
    monitoring: data.monitoring || []
  };
}

function kpiFromRows(rows) {
  return {
    total_items: rows.length,
    ready_for_legal: rows.filter(isReady).length,
    restricted_items: rows.filter(row => row.access_classification === "restricted").length,
    custody_gaps: rows.filter(row => Number(row.custody_events) === 0).length,
    needs_legal_review: rows.filter(row => ["needs_review", "not_reviewed"].includes(row.legal_status)).length,
    unverified_items: rows.filter(row => row.verification_status === "unverified").length
  };
}

function isReady(row) {
  return row.verification_status === "verified"
    && row.legal_status === "approved_for_legal_use"
    && Number(row.custody_events) >= 2;
}

function incidentSummary(rows) {
  const grouped = {};
  rows.forEach(row => {
    grouped[row.incident_code] ||= { incident_code: row.incident_code, title: row.title, items: 0, ready: 0, restricted: 0 };
    grouped[row.incident_code].items += 1;
    if (isReady(row)) grouped[row.incident_code].ready += 1;
    if (row.access_classification === "restricted") grouped[row.incident_code].restricted += 1;
  });
  return Object.values(grouped);
}

function renderKpis(values) {
  const labels = {
    total_items: "Total evidence items",
    ready_for_legal: "Ready for legal",
    restricted_items: "Restricted",
    custody_gaps: "Custody gaps",
    needs_legal_review: "Need legal review",
    unverified_items: "Unverified"
  };
  kpis.innerHTML = Object.entries(labels)
    .map(([key, label]) => `<div class="kpi"><strong>${values[key]}</strong><span>${label}</span></div>`)
    .join("");
}

function renderCharts(rows) {
  const profile = visualProfile(activeRole, rows);
  document.querySelector("#media-chart").closest(".chart-panel").querySelector("h2").textContent = profile.leftTitle;
  document.querySelector("#verification-chart").closest(".chart-panel").querySelector("h2").textContent = profile.middleTitle;
  if (profile.leftType === "donut") drawDonut("media-chart", profile.leftData);
  else drawBars("media-chart", profile.leftData);
  if (profile.middleType === "donut") drawDonut("verification-chart", profile.middleData);
  else drawBars("verification-chart", profile.middleData);
}

function visualProfile(role, rows) {
  if (role === "leadership") {
    return {
      leftTitle: "Portfolio Mix",
      leftType: "donut",
      leftData: countBy(rows, "media_type"),
      middleTitle: "Strategic Readiness",
      middleType: "bars",
      middleData: [
        { label: "ready", value: rows.filter(isReady).length },
        { label: "open work", value: rows.filter(row => !isReady(row)).length },
        { label: "restricted", value: rows.filter(row => row.access_classification === "restricted").length }
      ]
    };
  }
  if (role === "legal") {
    return {
      leftTitle: "Legal Status",
      leftType: "donut",
      leftData: countBy(rows, "legal_status"),
      middleTitle: "Evidentiary Completeness",
      middleType: "bars",
      middleData: [
        { label: "ready", value: rows.filter(isReady).length },
        { label: "custody gaps", value: rows.filter(row => Number(row.custody_events) === 0).length },
        { label: "needs review", value: rows.filter(row => ["needs_review", "not_reviewed"].includes(row.legal_status)).length }
      ]
    };
  }
  if (role === "data_protection" || role === "monitoring") {
    return {
      leftTitle: "Access Classification",
      leftType: "donut",
      leftData: countBy(rows, "access_classification"),
      middleTitle: "Control Exceptions",
      middleType: "bars",
      middleData: [
        { label: "custody gaps", value: rows.filter(row => Number(row.custody_events) === 0).length },
        { label: "restricted", value: rows.filter(row => row.access_classification === "restricted").length },
        { label: "unverified", value: rows.filter(row => row.verification_status === "unverified").length }
      ]
    };
  }
  if (role === "ai") {
    return {
      leftTitle: "AI Workload Type",
      leftType: "donut",
      leftData: countBy(rows, "media_type"),
      middleTitle: "HITL Queue",
      middleType: "bars",
      middleData: [
        { label: "transcription", value: rows.filter(row => row.media_type === "video" || row.media_type === "audio").length },
        { label: "extraction", value: rows.filter(row => row.media_type === "document").length },
        { label: "visual triage", value: rows.filter(row => row.media_type === "photo").length }
      ]
    };
  }
  if (role === "partners") {
    return {
      leftTitle: "Masked Submission Mix",
      leftType: "donut",
      leftData: countBy(rows, "media_type"),
      middleTitle: "Partner Follow-up Need",
      middleType: "bars",
      middleData: [
        { label: "custody follow-up", value: rows.filter(row => Number(row.custody_events) === 0).length },
        { label: "verification pending", value: rows.filter(row => row.verification_status === "unverified").length },
        { label: "restricted", value: rows.filter(row => row.access_classification === "restricted").length }
      ]
    };
  }
  return {
    leftTitle: "Media Mix",
    leftType: "donut",
    leftData: countBy(rows, "media_type"),
    middleTitle: "Verification Pipeline",
    middleType: "bars",
    middleData: countBy(rows, "verification_status")
  };
}

function countBy(rows, key) {
  const counts = {};
  rows.forEach(row => { counts[row[key]] = (counts[row[key]] || 0) + 1; });
  return Object.entries(counts).map(([label, value]) => ({ label, value }));
}

function drawDonut(canvasId, rows) {
  const canvas = document.getElementById(canvasId);
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const total = rows.reduce((sum, row) => sum + row.value, 0) || 1;
  let start = -Math.PI / 2;
  palette(rows.length).forEach((color, index) => {
    const slice = (rows[index]?.value || 0) / total * Math.PI * 2;
    ctx.beginPath();
    ctx.moveTo(110, 105);
    ctx.arc(110, 105, 88, start, start + slice);
    ctx.fillStyle = color;
    ctx.fill();
    start += slice;
  });
  ctx.globalCompositeOperation = "destination-out";
  ctx.beginPath();
  ctx.arc(110, 105, 46, 0, Math.PI * 2);
  ctx.fill();
  ctx.globalCompositeOperation = "source-over";
  legend(ctx, rows, 220, 36);
}

function drawBars(canvasId, rows) {
  const canvas = document.getElementById(canvasId);
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const max = Math.max(...rows.map(row => row.value), 1);
  rows.forEach((row, index) => {
    const y = 24 + index * 34;
    const width = (row.value / max) * 185;
    ctx.fillStyle = palette(rows.length)[index];
    ctx.fillRect(120, y, width, 18);
    ctx.fillStyle = "#18212f";
    ctx.font = "12px Arial";
    ctx.fillText(human(row.label), 8, y + 14);
    ctx.fillText(String(row.value), 130 + width, y + 14);
  });
}

function legend(ctx, rows, x, y) {
  rows.forEach((row, index) => {
    ctx.fillStyle = palette(rows.length)[index];
    ctx.fillRect(x, y + index * 24, 12, 12);
    ctx.fillStyle = "#18212f";
    ctx.font = "12px Arial";
    ctx.fillText(`${human(row.label)} (${row.value})`, x + 18, y + 11 + index * 24);
  });
}

function renderRole(data) {
  title.textContent = roleSelect.options[roleSelect.selectedIndex].text;
  note.textContent = notes[activeRole];
  const rows = data[activeRole] || [];
  if (!rows.length) {
    content.innerHTML = `<div class="empty">No records match the current filters.</div>`;
    return;
  }
  if (activeRole === "leadership") renderLeadership(rows);
  else if (activeRole === "partners") renderPartners(rows);
  else if (activeRole === "ai") renderAi(rows, data.ai_recommendations || {}, data.notifications || {});
  else if (activeRole === "media") renderMedia(rows);
  else if (activeRole === "monitoring") renderMonitoring(rows);
  else if (activeRole === "legal") renderLegal(rows);
  else renderEvidence(rows);
}

function applyRoleLayout() {
  const showSupport = ["leadership", "investigations", "legal", "data_protection", "ai", "partners", "monitoring"].includes(activeRole);
  const showFilters = ["investigations", "legal", "data_protection", "media", "ai"].includes(activeRole);
  const showVisuals = ["leadership", "investigations", "legal", "data_protection", "ai", "partners", "monitoring"].includes(activeRole);
  supportRegion.hidden = !showSupport && !showFilters;
  filtersRegion.hidden = !showFilters;
  visualGrid.hidden = !showVisuals;
  kpis.hidden = !showSupport;
}

function renderLeadership(rows) {
  const totalItems = rows.reduce((sum, row) => sum + row.items, 0);
  const ready = rows.reduce((sum, row) => sum + row.ready, 0);
  const restricted = rows.reduce((sum, row) => sum + row.restricted, 0);
  const open = rows.filter(row => row.ready < row.items).length;
  content.innerHTML = `
    <div class="executive-grid">
      ${execCard("Open investigations", open, "Cases with unresolved evidence work")}
      ${execCard("Evidence items", totalItems, "Current filtered portfolio")}
      ${execCard("Ready for legal", ready, "Evidence meeting readiness controls")}
      ${execCard("Restricted items", restricted, "Requires strict access handling")}
    </div>
    <div class="trend-row">
      ${rows.map(row => `
        <button class="trend-card" data-incident="${escapeHtml(row.incident_code)}">
          <strong>${escapeHtml(row.incident_code)}</strong>
          <span>${escapeHtml(row.title)}</span>
          <div class="progress"><i style="width:${row.items ? Math.round((row.ready / row.items) * 100) : 0}%"></i></div>
          <small>${row.ready}/${row.items} ready</small>
        </button>
      `).join("")}
    </div>
    ${timeline("Quarterly case throughput", rows.slice(0, 12))}
  `;
  content.querySelectorAll(".trend-card").forEach(card => {
    card.addEventListener("click", () => {
      filters.incident.value = card.dataset.incident;
      activeRole = "investigations";
      roleSelect.value = "investigations";
      syncRoleNav();
      render();
    });
  });
}

function renderAi(rows, aiRecommendations, notifications) {
  const lowConfidence = rows.length;
  const transcription = rows.filter(row => row.suggested_use.toLowerCase().includes("transcription")).length;
  const extraction = rows.filter(row => row.suggested_use.toLowerCase().includes("extraction")).length;
  const summary = aiRecommendations.summary || {};
  const anomalies = aiRecommendations.anomalies || [];
  const recommendations = aiRecommendations.recommendations || [];
  const pilotLanes = aiRecommendations.pilot_lanes || [];
  const prohibitedUses = aiRecommendations.prohibited_uses || [];
  const decisionLogFields = aiRecommendations.decision_log_fields || [];
  content.innerHTML = `
    <div class="executive-grid">
      ${execCard("Assistive backlog", lowConfidence, "Candidates where AI may reduce manual preparation")}
      ${execCard("Transcription candidates", transcription, "Video/audio work queue")}
      ${execCard("Extraction candidates", extraction, "Document/entity work queue")}
      ${execCard("Detected anomalies", summary.anomaly_count || 0, "Structured facts passed to recommendation layer")}
    </div>
    ${aiControlNotice(aiRecommendations)}
    ${pilotLaneBoard(pilotLanes)}
    ${recommendationBoard(recommendations)}
    ${notificationBoard(notifications)}
    ${table(["Rejected/prohibited use"], prohibitedUses.map(row => [escapeHtml(row)]))}
    <div class="notice">
      <strong>AI decision log</strong>
      <p>${escapeHtml(decisionLogFields.join(", ") || "Tool, version, reviewer, decision, correction, and final disposition should be logged.")}</p>
    </div>
    ${table(["Severity", "Anomaly", "Owner", "Count", "Sample media"], anomalies.map(row => [
      severity(row.severity),
      human(row.type),
      human(row.owner),
      escapeHtml(row.count),
      escapeHtml((row.sample_media_ids || []).join(", ") || "portfolio-level")
    ]))}
    ${table(["Media", "File", "Suggested AI use", "Required control"], rows.map(row => [
      escapeHtml(row.media_id),
      escapeHtml(row.file),
      escapeHtml(row.suggested_use),
      escapeHtml(row.required_control)
    ]))}
    ${qaSplit(rows)}
  `;
}

function aiControlNotice(aiRecommendations) {
  return `<div class="notice">
    <strong>${human(aiRecommendations.mode || "local redacted recommendation engine")}</strong>
    <p>${escapeHtml(aiRecommendations.model_boundary || "Recommendations use redacted facts only.")}</p>
  </div>`;
}

function pilotLaneBoard(rows) {
  if (!rows.length) return `<div class="empty">No GenAI pilot lanes configured for the current snapshot.</div>`;
  return `${table(["Pilot lane", "Priority", "Purpose", "Required control"], rows.map(row => [
    escapeHtml(row.name),
    severity(row.priority),
    escapeHtml(row.purpose),
    escapeHtml(row.required_control)
  ]))}`;
}

function recommendationBoard(rows) {
  if (!rows.length) return `<div class="empty">No AI recommendations for the current snapshot.</div>`;
  return `<div class="recommendation-grid">${rows.map(row => `
    <article class="recommendation-card ${row.severity}">
      <strong>${escapeHtml(row.stakeholder)} | ${human(row.severity)}</strong>
      <h3>${escapeHtml(row.title)}</h3>
      <p>${escapeHtml(row.recommendation)}</p>
      <small>${escapeHtml(row.expected_impact)}</small>
    </article>
  `).join("")}</div>`;
}

function notificationBoard(notifications) {
  const events = notifications.events || [];
  return `<div class="notice">
    <strong>Threshold notifications</strong>
    <p>${notifications.dry_run ? "Dry-run mode: notifications are composed but not sent." : "Live mode: configured Slack/Gmail delivery is enabled."}</p>
    <p>Minimum severity: ${human(notifications.min_severity || "high")} | Minimum count: ${notifications.min_count || 1} | Events: ${notifications.event_count || 0}</p>
  </div>
  ${events.length ? table(["Channel", "Stakeholder", "Severity", "Anomaly", "Count", "Delivery"], events.map(row => [
    human(row.channel),
    escapeHtml(row.recipient),
    severity(row.severity),
    human(row.type),
    row.count,
    deliverySummary(row)
  ])) : ""}`;
}

function deliverySummary(row) {
  if (Array.isArray(row.deliveries) && row.deliveries.length) {
    return row.deliveries.map(delivery => (
      `${human(delivery.channel)}: ${human(delivery.status)}`
    )).join(" | ");
  }
  return `${human(row.delivery_status)}: ${escapeHtml(row.delivery_detail || "")}`;
}

function renderLegal(rows) {
  content.innerHTML = `
    ${milestoneBoard(rows)}
    ${table(
    ["Media", "File", "Incident", "Verification", "Legal", "Custody", "Next legal action"],
    rows.map(row => [
      escapeHtml(row.media_id),
      escapeHtml(row.original_filename),
      escapeHtml(row.incident_code),
      status(row.verification_status),
      status(row.legal_status),
      escapeHtml(row.custody_events),
      legalAction(row)
    ])
  )}
  `;
}

function renderPartners(rows) {
  const grouped = incidentSummary(rows);
  content.innerHTML = `
    <div class="notice">Partner view is masked: no source names, exact locations, person details, file hashes, or raw filenames are exposed.</div>
    ${maskedTrend(grouped)}
    ${table(["Area code", "Shared trend", "Items needing partner follow-up"], grouped.map((row, index) => [
      `AREA-${String(index + 1).padStart(2, "0")}`,
      "Submission quality and custody completeness",
      row.items
    ]))}
  `;
}

function renderMonitoring(rows) {
  content.innerHTML = `${monitorTimeline(rows)}<div class="monitor-grid">${rows.map(row => `
    <div class="monitor-card ${row.status}">
      <strong>${human(row.name)}</strong>
      <p>Value: ${formatMetric(row.value, row.unit)} | Threshold: ${formatMetric(row.threshold, row.unit)}</p>
      <p>${escapeHtml(row.message)}</p>
    </div>
  `).join("")}</div>`;
}

function renderMedia(rows) {
  content.innerHTML = `<div class="media-grid">${rows.map(row => `
    <article class="media-card">
      <img src="/${escapeHtml(normalisePreviewPath(row.preview_path))}" alt="${escapeHtml(row.original_filename)} preview">
      <div class="body">
        <strong>${escapeHtml(row.original_filename)}</strong>
        <p>${escapeHtml(row.incident_code)} | ${human(row.media_type)}</p>
        <p>${human(row.safe_status)} | ${escapeHtml(row.detected_mime)}</p>
      </div>
    </article>
  `).join("")}</div>`;
}

function normalisePreviewPath(path) {
  return String(path || "").replace(/^\.\.\//, "");
}

function renderEvidence(rows) {
  content.innerHTML = `
    ${pipelineBoard(rows)}
    ${table(
    ["Media", "File", "Incident", "Type", "Class", "Verification", "Legal", "Custody", "Safety"],
    rows.map(row => [
      escapeHtml(row.media_id),
      escapeHtml(row.original_filename),
      escapeHtml(row.incident_code),
      escapeHtml(row.media_type),
      status(row.access_classification),
      status(row.verification_status),
      status(row.legal_status),
      row.custody_events,
      status(row.safe_status || "not_scanned")
    ])
  )}
  `;
}

function execCard(label, value, help) {
  return `<div class="exec-card"><strong>${value}</strong><span>${label}</span><p>${help}</p></div>`;
}

function legalAction(row) {
  if (Number(row.custody_events) === 0) return "Hold: reconstruct custody trail";
  if (row.verification_status !== "verified") return "Wait for verification completion";
  if (row.legal_status === "needs_review" || row.legal_status === "not_reviewed") return "Schedule legal review";
  if (row.legal_status === "approved_for_legal_use") return "Eligible for controlled evidence pack";
  return "Restricted: legal sign-off required";
}

function pipelineBoard(rows) {
  const stages = [
    ["Received", rows.length],
    ["Custody complete", rows.filter(row => Number(row.custody_events) >= 2).length],
    ["Verified", rows.filter(row => row.verification_status === "verified").length],
    ["Legal approved", rows.filter(row => row.legal_status === "approved_for_legal_use").length]
  ];
  return `<div class="pipeline">${stages.map(([label, value], index) => `
    <div class="stage"><strong>${value}</strong><span>${label}</span></div>${index < stages.length - 1 ? "<b></b>" : ""}
  `).join("")}</div>`;
}

function milestoneBoard(rows) {
  const items = [
    ["Intake review", rows.length, "Complete record inventory"],
    ["Verification", rows.filter(row => row.verification_status === "verified").length, "Strict-standard verification"],
    ["Legal review", rows.filter(row => row.legal_status === "approved_for_legal_use").length, "Approved for legal use"],
    ["Export pack", rows.filter(isReady).length, "Ready for controlled disclosure"]
  ];
  return `<div class="gantt">${items.map(([label, value, help], index) => `
    <div class="gantt-row">
      <span>${label}</span>
      <i style="width:${Math.min(100, 18 + value * 8)}%; margin-left:${index * 4}%"></i>
      <small>${value} | ${help}</small>
    </div>
  `).join("")}</div>`;
}

function timeline(titleText, rows) {
  return `<div class="timeline"><h3>${titleText}</h3>${rows.map((row, index) => `
    <button data-incident="${escapeHtml(row.incident_code)}">
      <strong>Q${(index % 4) + 1}</strong>
      <span>${escapeHtml(row.incident_code)}</span>
      <i style="height:${Math.max(18, row.items * 12)}px"></i>
    </button>
  `).join("")}</div>`;
}

function maskedTrend(rows) {
  return `<div class="masked-trend">${rows.map((row, index) => `
    <div>
      <strong>AREA-${String(index + 1).padStart(2, "0")}</strong>
      <span>${row.items} submissions need follow-up</span>
      <i style="width:${Math.min(100, row.items * 12)}%"></i>
    </div>
  `).join("")}</div>`;
}

function qaSplit(rows) {
  const human = rows.length;
  return `<div class="qa-grid">
    ${execCard("Human review required", human, "All AI-assisted outputs wait for HITL verification")}
    ${execCard("Auto decisions", 0, "No automated verification or legal conclusions")}
    ${execCard("Restricted inputs", human, "No external SaaS without approval")}
  </div>`;
}

function monitorTimeline(rows) {
  return `<div class="monitor-strip">${rows.map(row => `
    <div class="${row.status}">
      <strong>${human(row.name)}</strong>
      <i style="width:${monitorWidth(row)}%"></i>
      <span>${row.status} | ${formatMetric(row.value, row.unit)}</span>
    </div>
  `).join("")}</div>`;
}

function monitorWidth(row) {
  const value = Number(row.value) || 0;
  const threshold = Number(row.threshold) || 1;
  if (row.unit === "ratio") return Math.min(100, Math.round(value * 100));
  return Math.min(100, Math.round((value / threshold) * 100));
}

function formatMetric(value, unit) {
  const number = Number(value);
  if (unit === "ratio") return `${Math.round(number * 100)}%`;
  if (unit === "seconds") return `${number.toFixed(2)}s`;
  return String(value);
}

function syncRoleNav() {
  roleButtons.forEach(button => {
    button.classList.toggle("active", button.dataset.role === activeRole);
  });
}

function table(headers, rows) {
  return `<table><thead><tr>${headers.map(h => `<th>${h}</th>`).join("")}</tr></thead><tbody>${
    rows.map(row => `<tr>${row.map(cell => `<td>${cell}</td>`).join("")}</tr>`).join("")
  }</tbody></table>`;
}

function status(value) {
  return `<span class="${escapeHtml(value)}">${human(value)}</span>`;
}

function severity(value) {
  return `<span class="severity ${escapeHtml(value)}">${human(value)}</span>`;
}

function human(value) {
  return escapeHtml(String(value || "").replaceAll("_", " "));
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, char => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;"
  })[char]);
}

function palette(count) {
  const colors = ["#1d5f99", "#16724a", "#b76e00", "#b42318", "#607086", "#6f42c1", "#0f766e"];
  return Array.from({ length: count }, (_, index) => colors[index % colors.length]);
}

load();
setInterval(load, 5000);
