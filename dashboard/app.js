const roleSelect = document.getElementById("role");
const loginButton = document.getElementById("login");
const kpis = document.getElementById("kpis");
const content = document.getElementById("content");
const title = document.getElementById("view-title");
const note = document.getElementById("view-note");
const updated = document.getElementById("updated");

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
  ai: "AI-assisted triage candidates with controls and human review requirements.",
  media: "NoSQL media catalog with scanned synthetic sample objects.",
  monitoring: "Operational, security, performance, and data-skew monitoring."
};

let activeRole = "leadership";
let latestData = null;

loginButton.addEventListener("click", () => {
  activeRole = roleSelect.value;
  render();
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
  const response = await fetch(`/dashboard/data.json?ts=${Date.now()}`);
  latestData = await response.json();
  populateFilters(latestData.investigations || []);
  render();
  updated.textContent = `Updated ${new Date(latestData.generated_at).toLocaleString()}`;
}

function render() {
  if (!latestData) return;
  const filtered = filterRows(latestData.investigations || []);
  const viewData = withFilteredData(latestData, filtered);
  renderKpis(kpiFromRows(filtered));
  renderCharts(filtered);
  renderRole(viewData, filtered);
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
  drawDonut("media-chart", countBy(rows, "media_type"));
  drawBars("verification-chart", countBy(rows, "verification_status"));
  renderHeatmap(incidentSummary(rows));
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

function renderHeatmap(rows) {
  const heatmap = document.getElementById("heatmap");
  heatmap.innerHTML = rows.map(row => {
    const score = row.items ? (row.restricted + row.items - row.ready) / (row.items * 2) : 0;
    const color = heatColor(score);
    return `<button class="heat-cell" style="background:${color}" data-incident="${escapeHtml(row.incident_code)}">
      <strong>${row.incident_code}</strong>
      <span>${row.items} items | ${row.restricted} restricted</span>
    </button>`;
  }).join("") || `<div class="empty">No heatmap data.</div>`;
  heatmap.querySelectorAll(".heat-cell").forEach(cell => {
    cell.addEventListener("click", () => {
      filters.incident.value = cell.dataset.incident;
      activeRole = "investigations";
      roleSelect.value = "investigations";
      render();
    });
  });
}

function heatColor(score) {
  if (score > 0.7) return "#b42318";
  if (score > 0.4) return "#b76e00";
  return "#16724a";
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
  else if (activeRole === "ai") renderAi(rows);
  else if (activeRole === "media") renderMedia(rows);
  else if (activeRole === "monitoring") renderMonitoring(rows);
  else if (activeRole === "legal") renderLegal(rows);
  else renderEvidence(rows);
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
          <strong>${row.incident_code}</strong>
          <span>${escapeHtml(row.title)}</span>
          <div class="progress"><i style="width:${row.items ? Math.round((row.ready / row.items) * 100) : 0}%"></i></div>
          <small>${row.ready}/${row.items} ready</small>
        </button>
      `).join("")}
    </div>
  `;
  content.querySelectorAll(".trend-card").forEach(card => {
    card.addEventListener("click", () => {
      filters.incident.value = card.dataset.incident;
      activeRole = "investigations";
      roleSelect.value = "investigations";
      render();
    });
  });
}

function renderAi(rows) {
  const lowConfidence = rows.length;
  const transcription = rows.filter(row => row.suggested_use.toLowerCase().includes("transcription")).length;
  const extraction = rows.filter(row => row.suggested_use.toLowerCase().includes("extraction")).length;
  content.innerHTML = `
    <div class="executive-grid">
      ${execCard("HITL queue", lowConfidence, "AI candidates awaiting human review")}
      ${execCard("Transcription candidates", transcription, "Video/audio work queue")}
      ${execCard("Extraction candidates", extraction, "Document/entity work queue")}
      ${execCard("Auto-approved outputs", 0, "Kept at zero by design")}
    </div>
    ${table(["Media", "File", "Suggested AI use", "Required control"], rows.map(row => [
      row.media_id,
      row.file,
      row.suggested_use,
      row.required_control
    ]))}
  `;
}

function renderLegal(rows) {
  content.innerHTML = table(
    ["Media", "File", "Incident", "Verification", "Legal", "Custody", "Next legal action"],
    rows.map(row => [
      row.media_id,
      row.original_filename,
      row.incident_code,
      status(row.verification_status),
      status(row.legal_status),
      row.custody_events,
      legalAction(row)
    ])
  );
}

function renderPartners(rows) {
  const grouped = incidentSummary(rows);
  content.innerHTML = `
    <div class="notice">Partner view is masked: no source names, exact locations, person details, file hashes, or raw filenames are exposed.</div>
    ${table(["Area code", "Shared trend", "Items needing partner follow-up"], grouped.map((row, index) => [
      `AREA-${String(index + 1).padStart(2, "0")}`,
      "Submission quality and custody completeness",
      row.items
    ]))}
  `;
}

function renderMonitoring(rows) {
  content.innerHTML = `<div class="monitor-grid">${rows.map(row => `
    <div class="monitor-card ${row.status}">
      <strong>${human(row.name)}</strong>
      <p>Value: ${row.value} | Threshold: ${row.threshold}</p>
      <p>${row.message}</p>
    </div>
  `).join("")}</div>`;
}

function renderMedia(rows) {
  content.innerHTML = `<div class="media-grid">${rows.map(row => `
    <article class="media-card">
      <img src="/${normalisePreviewPath(row.preview_path)}" alt="${escapeHtml(row.original_filename)} preview">
      <div class="body">
        <strong>${escapeHtml(row.original_filename)}</strong>
        <p>${row.incident_code} | ${human(row.media_type)}</p>
        <p>${human(row.safe_status)} | ${row.detected_mime}</p>
      </div>
    </article>
  `).join("")}</div>`;
}

function normalisePreviewPath(path) {
  return String(path || "").replace(/^\.\.\//, "");
}

function renderEvidence(rows) {
  content.innerHTML = table(
    ["Media", "File", "Incident", "Type", "Class", "Verification", "Legal", "Custody", "Safety"],
    rows.map(row => [
      row.media_id,
      row.original_filename,
      row.incident_code,
      row.media_type,
      status(row.access_classification),
      status(row.verification_status),
      status(row.legal_status),
      row.custody_events,
      status(row.safe_status || "not_scanned")
    ])
  );
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

function table(headers, rows) {
  return `<table><thead><tr>${headers.map(h => `<th>${h}</th>`).join("")}</tr></thead><tbody>${
    rows.map(row => `<tr>${row.map(cell => `<td>${cell}</td>`).join("")}</tr>`).join("")
  }</tbody></table>`;
}

function status(value) {
  return `<span class="${value}">${human(value)}</span>`;
}

function human(value) {
  return String(value || "").replaceAll("_", " ");
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
