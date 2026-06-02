# Live Dashboard and Continuous Simulation Runbook

## Architecture

```text
PostgreSQL OLTP
  - Receives sensitive evidence records
  - Preserves source, metadata, custody, legal status, access classification
  - Optimised for controlled write workflows

DuckDB OLAP
  - Receives refreshed reporting facts from PostgreSQL
  - Supports dashboard reporting and stakeholder summaries
  - Keeps analytics separate from operational evidence intake

Dashboard
  - Reads dashboard/data.json generated from OLAP refresh
  - Simulates stakeholder login views
  - Refreshes every 5 seconds
```

## Start the Dashboard

Terminal 1.

Use the same root-capable WSL terminal where PostgreSQL is running. If needed:

```bash
sudo -i
```

Then:

```bash
cd "/mnt/c/Users/Hp/Desktop/dba/2026/HRT_DBM_Prep_Pack"
python3 scripts/refresh_olap.py
python3 scripts/sync_media_catalog.py
python3 scripts/refresh_olap.py
python3 dashboard/server.py
```

Open:

```text
http://127.0.0.1:8765
```

The dashboard has demo stakeholder access tabs:

- Leadership
- Investigations
- Legal
- CSO Partners
- Data Protection
- AI Review

The password box is present to simulate separate access, but this is not production authentication.

## Run the One-Hour Continuous Simulation

Terminal 2.

Use another root-capable WSL terminal:

```bash
cd "/mnt/c/Users/Hp/Desktop/dba/2026/HRT_DBM_Prep_Pack"
python3 scripts/simulate_continuous_intake.py --minutes 60 --interval 30
```

For a quick test:

```bash
python3 scripts/simulate_continuous_intake.py --minutes 2 --interval 15
```

The simulator continuously inserts new sensitive video, image, and document records into PostgreSQL, then refreshes DuckDB and the dashboard JSON.

Each simulator run now creates a fresh run ID, for example:

```text
INC-LIVE-20260601143022-a1b2c3-0001
SRC-LIVE-20260601143022-a1b2c3-0001
LIVE-20260601143022-a1b2c3-0001-1
```

This prevents repeated runs from reusing the same incident, source, media IDs, or hashes. The generated data also varies media types, verification states, legal states, access classes, custody completeness, confidence, and location confidence so the dashboard changes visibly while the simulation runs.

To force a named run for a demonstration:

```bash
python3 scripts/simulate_continuous_intake.py --minutes 5 --interval 15 --run-id demo-001
```

## NoSQL Media Store

The demo includes a file-backed NoSQL-style media catalog:

```text
media_store/catalog.jsonl
media_store/objects/
media_store/quarantine/
```

Run:

```bash
python3 scripts/sync_media_catalog.py
python3 scripts/refresh_olap.py
```

The catalog stores one JSON document per media object. Each document includes media ID, incident code, original filename, object path, preview path, SHA-256 hash, detected MIME type, byte size, and safety scan status.

For safety, sample media objects are generated locally as synthetic SVG/text placeholders. The scanner allowlists safe demo extensions and flags blocked or unexpected extensions. This demonstrates the architecture without downloading unknown internet media or committing risky binaries.

## How to Explain the OLTP/OLAP Split

Use this phrasing:

> I would keep the operational evidence database separate from the reporting layer. PostgreSQL OLTP handles controlled intake, metadata, custody, verification, and legal status. DuckDB OLAP receives a reporting-ready copy so dashboards and stakeholder summaries do not interfere with the integrity or performance of the evidence system.

## How AI Is Integrated

The AI tab does not claim AI has verified evidence. It now has two layers:

1. Anomaly detection over the reporting snapshot.
2. A local GenAI-style recommendation layer that converts redacted anomaly facts into practical actions for each stakeholder.

The local recommendation engine lives in:

```text
scripts/ai_recommendations.py
```

It detects issues such as:

- Custody gaps.
- Restricted but unverified records.
- Empty metadata or missing captured time.
- Unsafe or unscanned media catalog items.
- Recent source skew.
- Recent unverified surges.
- Low legal-ready yield.
- Monitoring alerts.

It then produces recommendations for leadership, investigations, legal, CSO partners, data protection, monitoring, operations, and AI review.

## Threshold Notifications: Slack and Email

The AI recommendation layer can compose stakeholder notifications for anomalies that exceed configured thresholds. It is dry-run by default so the demo does not accidentally send sensitive alerts.

Notification code:

```text
scripts/notifications.py
```

Default thresholds:

```text
HRT_NOTIFY_MIN_SEVERITY=high
HRT_NOTIFY_MIN_COUNT=1
HRT_NOTIFY_DRY_RUN=true
```

In dry-run mode, the AI Review dashboard shows which notifications would be sent, the stakeholder recipient, severity, anomaly type, and delivery status.

### Slack Setup

Create a Slack app and incoming webhook:

1. Open `https://api.slack.com/apps`.
2. Create an app, for example `HRT Evidence Alerts`.
3. Select the target workspace.
4. Open `Incoming Webhooks`.
5. Enable incoming webhooks.
6. Add a webhook to the target channel.
7. Copy the webhook URL.

Do not paste the webhook into chat or commit it. If a webhook is exposed, revoke it in Slack and create a new one.

To enable Slack delivery:

```bash
export HRT_NOTIFY_DRY_RUN=false
export HRT_NOTIFY_MIN_SEVERITY=high
export HRT_SLACK_WEBHOOK_URL="https://hooks.slack.com/services/REDACTED"
python3 scripts/refresh_olap.py
```

### Gmail Setup

Use a Gmail app password, not your normal Gmail password:

1. Open `https://myaccount.google.com/security`.
2. Confirm 2-Step Verification is enabled.
3. Open `https://myaccount.google.com/apppasswords`.
4. Create an app password, for example `HRT evidence alerts`.
5. Copy the 16-character app password once.

Do not paste the app password into chat or commit it. If it is exposed, delete it in Google Account app passwords and create a new one.

Gmail SMTP can use SSL on port 465:

```bash
export HRT_NOTIFY_DRY_RUN=false
export HRT_SMTP_HOST="smtp.gmail.com"
export HRT_SMTP_PORT=465
export HRT_SMTP_SECURITY="ssl"
export HRT_SMTP_SENDER="sender@gmail.com"
export HRT_SMTP_PASSWORD="gmail-app-password"
export HRT_STAKEHOLDER_EMAILS="investigations:investigations@example.org,data_protection:dpo@example.org,legal:legal@example.org,leadership:leadership@example.org,monitoring:monitoring@example.org"
python3 scripts/refresh_olap.py
```

Or STARTTLS on port 587:

```bash
export HRT_NOTIFY_DRY_RUN=false
export HRT_SMTP_HOST="smtp.gmail.com"
export HRT_SMTP_PORT=587
export HRT_SMTP_SECURITY="starttls"
export HRT_SMTP_SENDER="sender@gmail.com"
export HRT_SMTP_PASSWORD="gmail-app-password"
export HRT_STAKEHOLDER_EMAILS="investigations:investigations@example.org,data_protection:dpo@example.org,legal:legal@example.org,leadership:leadership@example.org,monitoring:monitoring@example.org"
python3 scripts/refresh_olap.py
```

### Slack and Gmail Together

To send to both Slack and Gmail, keep both channel configurations set. Do not unset `HRT_SLACK_WEBHOOK_URL`.

```bash
export HRT_NOTIFY_DRY_RUN=false
export HRT_NOTIFY_MIN_SEVERITY=high
export HRT_NOTIFY_MIN_COUNT=1
export HRT_NOTIFY_TIMEOUT_SECONDS=30
export HRT_SLACK_WEBHOOK_URL="https://hooks.slack.com/services/REDACTED"
export HRT_SMTP_HOST="smtp.gmail.com"
export HRT_SMTP_PORT=587
export HRT_SMTP_SECURITY="starttls"
export HRT_SMTP_SENDER="sender@gmail.com"
export HRT_SMTP_PASSWORD="gmail-app-password"
export HRT_STAKEHOLDER_EMAILS="investigations:investigations@example.org,data_protection:dpo@example.org,legal:legal@example.org,leadership:leadership@example.org,monitoring:monitoring@example.org"
python3 scripts/refresh_olap.py
```

Expected AI Review delivery status:

```text
slack: sent | email: sent
```

The older Gmail-specific aliases also work:

```bash
export HRT_GMAIL_SENDER="sender@gmail.com"
export HRT_GMAIL_APP_PASSWORD="gmail-app-password"
```

For another provider, keep the same pattern and change host, port, sender, and password:

```bash
export HRT_NOTIFY_DRY_RUN=false
export HRT_SMTP_HOST="smtp.example.org"
export HRT_SMTP_PORT=465
export HRT_SMTP_SECURITY="ssl"
export HRT_SMTP_SENDER="alerts@example.org"
export HRT_SMTP_PASSWORD="smtp-password-or-app-password"
python3 scripts/refresh_olap.py
```

### Gmail SMTP Troubleshooting

If Slack sends but Gmail does not, open the AI Review dashboard and inspect **Threshold notifications**. A common failure is:

```text
Email send failed: _ssl.c:983: The handshake operation timed out
```

That means the code attempted email but Gmail TLS did not complete. Test from WSL:

```bash
python3 - <<'PY'
import smtplib, ssl

try:
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as smtp:
        print("connected")
        smtp.ehlo()
        print("ehlo ok")
        smtp.starttls(context=ssl.create_default_context())
        print("starttls ok")
except Exception as e:
    print("failed:", repr(e))
PY
```

Also test SSL on port 465:

```bash
python3 - <<'PY'
import smtplib, ssl

try:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30, context=ssl.create_default_context()) as smtp:
        print("ssl connected")
        smtp.ehlo()
        print("ehlo ok")
except Exception as e:
    print("failed:", repr(e))
PY
```

From WSL, Windows PowerShell network checks can be run as:

```bash
powershell.exe -Command "Test-NetConnection smtp.gmail.com -Port 587"
powershell.exe -Command "Test-NetConnection smtp.gmail.com -Port 465"
```

If Windows succeeds but WSL times out during TLS, check VPN, firewall, or proxy routing. In the local test environment, ProtonVPN allowed TCP reachability but initially caused TLS handshakes from WSL to time out. Disconnecting or changing the network path allowed both Gmail SSL and STARTTLS to complete.

Security rules:

- Do not commit webhook URLs, app passwords, or real stakeholder emails.
- Rotate any Slack webhook or Gmail app password that is exposed in chat, terminal history, screenshots, or Git.
- Send redacted anomaly facts only.
- Do not include raw media, precise locations, source names, file hashes, victim names, or personal identifiers.
- Use high severity as the default threshold to avoid alert fatigue.
- In production, route alerts through approved organisational channels with access control and audit logging.

This is the safe demo architecture:

```text
PostgreSQL evidence records
  -> DuckDB/reporting snapshot
  -> redacted anomaly facts
  -> local recommendation generator
  -> threshold notification composer
  -> AI Review dashboard
```

In a production design, this same boundary is where an approved private LLM could be called, but only with redacted facts and after DPIA, security review, vendor review, and human-in-the-loop controls.

Safe examples:

- Local/private transcription of video or audio.
- Translation for internal triage.
- Entity extraction from redacted notes.
- Similarity or duplicate detection.
- Draft summaries for human review.
- Recommendation drafting from redacted anomaly facts.

Controls:

- No raw restricted media to unapproved external SaaS.
- Human review required.
- AI output labelled as AI-assisted.
- Tool, version, reviewer, and decision logged.
- DPIA triggered for systematic processing of sensitive data.

## Monitoring Coverage

The Monitoring tab tracks:

- Portfolio-wide restricted-data concentration, custody gap rate, unverified backlog, and single-source skew.
- Recent intake window size, using the latest 30 evidence records.
- Recent custody gap rate, restricted concentration, unverified intake, verification progress, legal-ready yield, and single-source skew.
- Dashboard refresh freshness.
- ETL refresh duration.

The recent-window checks are designed to move visibly during a live demo. The full database can become stable as it grows, but the newest 30 records should change when the simulator inserts a fresh random batch.

To trigger a noticeable Monitoring tab change:

```bash
python3 scripts/simulate_continuous_intake.py --minutes 2 --interval 15
```

Watch for these cards to move between percentages and alert states:

- Recent custody gap rate.
- Recent unverified intake.
- Recent verification progress.
- Recent legal-ready yield.
- Recent single-source skew.

Interview framing:

> I would monitor not only system health, but also evidentiary health. A database can be online and still produce weak findings if custody gaps, source skew, stale verification, or unsafe access patterns are not visible.

Interview phrasing:

> AI would sit behind data protection and verification controls. It can help triage, transcribe, translate, classify, and detect duplicates, but it cannot identify perpetrators, make legal conclusions, or replace human verification.
