# HRT-Style Evidence Systems Work Sample

## Scenario

This work sample uses a fictional investigation called Project Northlight. Field partners submit short videos, photos, witness notes, and contextual observations about alleged political violence. HRT-style programme, investigation, verification, legal, and advocacy teams need a secure system that preserves raw evidence, supports relational analysis, and produces defensible outputs.

The assumed environment includes a closed-source video management system, secure file storage, a relational PostgreSQL analysis layer, controlled exports for legal and advocacy use, and staff/partner users in different countries with varied connectivity and IT confidence.

## 1. Systems Management & Optimisation

### Current-State Architecture

```text
Field collector / CSO partner
        |
        | encrypted transfer, offline handover, or approved secure upload
        v
Secure intake area
        |
        | hash, virus scan, metadata capture, intake review
        v
Closed-source video management system
        |
        | approved metadata/API/export connector
        v
PostgreSQL relational analysis layer
        |
        +--> investigator search and pattern analysis
        +--> legal review and evidence export tracking
        +--> management reporting without exposing sensitive identities

Supporting controls:
MFA, role-based access, encrypted storage, backups, audit logs, vendor support channel,
incident register, data retention policy, user guidance, and access review cadence.
```

### Operations Checklist

| Area | Minimum operating control |
| --- | --- |
| Availability | Daily service checks, failed upload queue review, backup completion check, vendor status monitoring |
| Security | MFA enforced, quarterly access review, least-privilege roles, encrypted storage, secure admin accounts |
| Evidence integrity | File hash at intake, metadata completeness check, custody event for every transfer, immutable audit log |
| Usage monitoring | Track active users, failed logins, upload failures, incomplete records, export requests, stale cases |
| Vendor management | Named support contacts, severity levels, escalation path, change log, release notes review |
| Documentation | Architecture diagram, runbooks, data dictionary, role matrix, user guide, incident process |

### Sample Runbook

| Issue | First checks | Escalation |
| --- | --- | --- |
| Upload failure | Confirm file size, connection, user role, intake queue, storage capacity, error code | Vendor ticket if platform error repeats or upload queue blocks multiple users |
| Missing metadata | Check intake template, required fields, source form, EXIF extraction status, manual entry history | Investigations lead if metadata cannot be recovered from source |
| Slow search | Check query/filter pattern, index health, recent bulk uploads, storage latency, vendor status | DBA review for relational layer; vendor escalation for closed-source search |
| Permission error | Confirm role, case assignment, geographic restriction, legal hold, account status | Data Protection Lead review if user requests access to sensitive records |
| Evidence export request | Confirm purpose, lawful basis, approval, redaction needs, export format, custody log | Legal lead and Data Protection Lead sign-off before external transfer |

## 2. Strategic Development & Migration

### Assessment Memo

| Option | When to choose | Main risks | Recommended position |
| --- | --- | --- | --- |
| Keep and improve current system | Core video platform is stable, secure, and accepted by users | Existing limitations remain; vendor lock-in | Best first move if evidence integrity gaps can be fixed around the system |
| Replace/migrate | Current system cannot meet security, verification, scale, or usability needs | Data loss, downtime, user resistance, broken custody history | Only after discovery, pilot migration, and defensible business case |
| Hybrid integration | Video platform is useful but weak for relational analysis | Connector/API fragility; duplicated metadata | Strong likely approach: preserve video platform and add relational analysis layer |

### Migration Plan

1. Discovery: inventory systems, data types, users, permissions, integrations, exports, retention rules, and vendor constraints.
2. Data mapping: map media, metadata, incidents, sources, users, custody events, verification status, tags, legal flags, and exports.
3. Risk assessment: identify sensitive records, legal holds, high-risk sources, weak metadata, duplicate records, and incomplete custody trails.
4. Pilot migration: migrate a small representative case set and validate counts, hashes, relationships, permissions, search, and user workflows.
5. User acceptance testing: investigators, legal reviewers, programme staff, and partner support users test realistic tasks.
6. Cutover planning: freeze window, final sync, validation checklist, rollback trigger, communications plan, support rota.
7. Post-migration support: daily checks for two weeks, issue triage, training refreshers, vendor review, lessons learned.

### Risk Register

| Risk | Control |
| --- | --- |
| Data loss | Read-only source snapshot, full backup, record count validation, checksum validation |
| Metadata corruption | Field mapping review, mandatory field tests, sample manual review |
| Broken chain of custody | Preserve original custody events, log migration as custody event, retain source identifiers |
| Access-control failure | Role matrix validation, test users, sensitive-case spot checks |
| User resistance | Early demos, practical training, plain-language guidance, feedback loop |
| Vendor lock-in | Export documentation, API review, periodic data portability tests |
| Unsafe transfer | Encrypted transfer, named recipients, approval workflow, transfer logs |

## 3. Relational Database Development

The relational layer complements the closed-source video system. The video system remains the controlled repository for original multimedia and playback workflows. PostgreSQL adds structured cross-referencing, analytical queries, evidence readiness reporting, migration validation, and governance reporting.

Core entities are incidents, media files, sources, persons, locations, organisations, verification steps, custody events, access logs, exports, tags, and legal reviews. The model keeps raw media under controlled storage while enabling investigators to ask relational questions: which incidents share sources, locations, actors, timestamps, or verification weaknesses?

See `sql/schema.sql` and `sql/analysis_queries.sql`.

## 4. Verification & Investigative Workflows

### Evidence Lifecycle

1. Collection: field collector records media using agreed safety and consent guidance where feasible.
2. Secure transfer: file is transferred through approved encrypted route or documented offline handover.
3. Intake: system records source, hash, filename, received timestamp, collector code, and sensitivity class.
4. Metadata preservation: original metadata is extracted and stored without overwriting the original file.
5. Verification: team records geolocation, chronolocation, source assessment, corroboration, and technical checks.
6. Corroboration: link media to other media, testimony, documents, satellite imagery, public records, or partner reports.
7. Legal review: mark evidentiary readiness, concerns, restrictions, and required redactions.
8. Export: record recipient, purpose, approval, format, redactions, hash, and transfer method.
9. Archive/retention: apply retention schedule, legal hold, deletion review, or long-term preservation.

### Chain-of-Custody Model

Every evidence object should have:

- Original file hash and any derivative/export hash.
- Source identifier and intake user.
- Custody event for collection, transfer, ingestion, review, export, archive, or deletion.
- Timestamp, responsible person/system, transfer method, and reason.
- Audit trail for metadata edits, access, permission changes, and export.
- Clear distinction between original, working copy, redacted derivative, and external export.

### Standards Alignment

- Berkeley Protocol: preserve digital information methodically, document investigative steps, protect affected people, and maintain chain of custody.
- WITNESS Video as Evidence: collect video with purpose, preserve context, and plan for advocacy or legal use.
- HURIDOCS/Uwazi: structure human-rights information for document/evidence management, relationships, search, roles, and activity logs.
- Mnemonic/Syrian Archive: preserve authenticity, integrity, traceability, and verification methodology.

## 5. AI & Innovation

### Responsible AI Guidance

Potentially useful AI-supported tasks:

- Transcription and translation for internal review.
- Deduplication or similarity matching across large video sets.
- Entity extraction from notes or transcripts.
- Visual classification for triage, not final findings.
- Summarisation of non-sensitive internal documents.

AI outputs must be treated as leads or drafting aids, not evidence findings. Human review, source protection, auditability, and data protection review are mandatory.

### AI Risk Framework

| Risk | Control |
| --- | --- |
| Hallucination | Human verification and source-linked outputs |
| Bias or missed context | Diverse review, local context input, error sampling |
| Sensitive-data exposure | Prefer local/private tools, no external upload without approval |
| Vendor retention | Contract review, retention guarantees, no training on data |
| Evidentiary weakness | Keep AI outputs separate from verified findings |
| Source protection | Redact identities before testing where possible |

### Pilot Evaluation Template

- Problem statement: What workflow pain does the tool solve?
- Data sensitivity: What data will be processed and who could be harmed?
- Tool model: local, private cloud, vendor SaaS, or open-source.
- Security review: access, encryption, logging, retention, vendor terms.
- Accuracy test: sample size, ground truth, error categories, reviewer process.
- Human controls: who reviews, approves, rejects, or escalates output.
- Decision: reject, limited pilot, controlled deployment, or wider rollout.
- Do-not-use scenarios: unapproved sensitive uploads, source identification, final verification decisions, legal conclusions, or automated publication.

## 6. Team Support, Capacity Building & Data Protection

### Investigator User Guide

- Use consistent incident names, dates, locations, and source codes.
- Never overwrite original metadata or original files.
- Record unknown values as unknown, not guessed.
- Add verification notes with method, reviewer, date, and confidence.
- Log every transfer, export, and external share.
- Escalate missing metadata, consent concerns, security incidents, or source-risk issues.

### Training Outline

| Module | Outcome |
| --- | --- |
| Secure collection | Staff and partners understand safe capture, consent limits, and risk-aware collection |
| Secure transfer | Users can select approved transfer methods and document handover |
| Data entry | Users can complete required metadata without unnecessary complexity |
| Verification status | Teams understand unverified, partially verified, verified, disputed, and rejected statuses |
| Access and sharing | Users understand least privilege, MFA, redaction, and approval paths |
| Incident escalation | Users know what to do after lost device, wrong upload, suspected breach, or unsafe disclosure |

### Data Protection Lead Pack

| Topic | Practical position |
| --- | --- |
| Lawful basis | Identify basis before processing; avoid assuming consent is valid in coercive or high-risk settings |
| Special category data | Treat human-rights evidence, political opinions, ethnicity, health, biometric clues, and victim data as high-risk |
| Data minimisation | Collect what is needed for investigation, verification, legal use, safety, and accountability |
| Retention | Define retention by case status, legal hold, risk, and archival value |
| DPIA triggers | New system, AI tool, large sensitive dataset, new external sharing, high-risk partner workflow |
| Access controls | Need-to-know access, quarterly review, immediate removal for role changes |
| Breach response | Contain, assess harm, notify leadership/legal, document decisions, meet regulator timelines where required |
| Policy cadence | Annual review plus event-driven review after incidents, migrations, new tools, or legal changes |
