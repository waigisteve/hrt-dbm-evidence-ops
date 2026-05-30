const roleSelect = document.getElementById("role");
const loginButton = document.getElementById("login");
const kpis = document.getElementById("kpis");
const content = document.getElementById("content");
const title = document.getElementById("view-title");
const note = document.getElementById("view-note");
const updated = document.getElementById("updated");

const notes = {
  leadership: "Strategic readiness, risk, and operational posture.",
  investigations: "Working queue for verification, custody repair, and case analysis.",
  legal: "Items ready or waiting for legal review and controlled disclosure decisions.",
  partners: "Partner-facing process improvements for collection, transfer, and custody logging.",
  data_protection: "Restricted records, source risk, retention, access, and DPIA triggers.",
  ai: "AI-assisted triage candidates with controls and human review requirements."
};

let activeRole = "leadership";

loginButton.addEventListener("click", () => {
  activeRole = roleSelect.value;
  load();
});

async function load() {
  const response = await fetch(`data.json?ts=${Date.now()}`);
  const data = await response.json();
  renderKpis(data.kpis);
  renderRole(data);
  updated.textContent = `Updated ${new Date(data.generated_at).toLocaleString()}`;
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

function renderRole(data) {
  title.textContent = roleSelect.options[roleSelect.selectedIndex].text;
  note.textContent = notes[activeRole];
  const rows = data[activeRole] || [];
  if (!rows.length) {
    content.innerHTML = `<div class="empty">No records for this stakeholder view.</div>`;
    return;
  }
  if (activeRole === "leadership") renderLeadership(rows);
  else if (activeRole === "ai") renderAi(rows);
  else renderEvidence(rows);
}

function renderLeadership(rows) {
  content.innerHTML = table(["Incident", "Title", "Items", "Ready", "Restricted"], rows.map(row => [
    row.incident_code,
    row.title,
    row.items,
    `<span class="ready">${row.ready}</span>`,
    `<span class="restricted">${row.restricted}</span>`
  ]));
}

function renderAi(rows) {
  content.innerHTML = table(["Media", "File", "Suggested AI use", "Required control"], rows.map(row => [
    row.media_id,
    row.file,
    row.suggested_use,
    row.required_control
  ]));
}

function renderEvidence(rows) {
  content.innerHTML = table(
    ["Media", "File", "Incident", "Type", "Class", "Verification", "Legal", "Custody"],
    rows.map(row => [
      row.media_id,
      row.original_filename,
      row.incident_code,
      row.media_type,
      status(row.access_classification),
      status(row.verification_status),
      status(row.legal_status),
      row.custody_events
    ])
  );
}

function table(headers, rows) {
  return `<table><thead><tr>${headers.map(h => `<th>${h}</th>`).join("")}</tr></thead><tbody>${
    rows.map(row => `<tr>${row.map(cell => `<td>${cell}</td>`).join("")}</tr>`).join("")
  }</tbody></table>`;
}

function status(value) {
  return `<span class="${value}">${String(value).replaceAll("_", " ")}</span>`;
}

load();
setInterval(load, 5000);
