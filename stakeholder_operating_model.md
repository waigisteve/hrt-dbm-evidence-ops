# Stakeholder Operating Model: From Sensitive Media to Defensible Findings

## Executive Framing

The database function is the control layer that turns sensitive incoming material into secure, searchable, verifiable, and usable information. The closed-source video system protects original multimedia. The relational database connects media to incidents, sources, locations, verification work, custody history, legal review, retention, and exports.

The value to Videre is not only storage. It is confidence: leadership can know what exists, investigators can know what is usable, legal teams can know what is defensible, and partners can know how to submit material safely.

## How the Simulation Maps to the Job Description

| Videre responsibility | Simulation artifact | Stakeholder meaning |
| --- | --- | --- |
| Manage closed-source video systems and infrastructure | `media_files.external_video_system_id`, `storage_uri`, operations checklist | Original media remains controlled in the video platform; the relational layer indexes and governs it |
| Keep systems secure, reliable, and legally/ethically aligned | sensitivity fields, access logs, legal review status, retention category | Sensitive records are not treated the same as ordinary files; access and use are governed |
| Monitor usage and troubleshoot issues | metadata-quality, custody-gap, access-review queries | The system produces weekly exception reports instead of waiting for failures |
| Coordinate vendors | architecture and runbook | Vendor limits are documented; internal controls cover what the vendor system cannot do |
| Maintain documentation | README, work sample, schema, runbook, training guidance | Staff can understand the system without depending on one technical person |
| Assess improvement or replacement | migration plan and risk register | Migration is evidence-led, not technology-led |
| Lead migrations securely | migration validation query and controls | Counts, hashes, relationships, permissions, and custody history must survive migration |
| Build relational analysis capacity | `incidents`, `media_files`, `sources`, `locations`, `alleged_actors`, tags | Teams can detect patterns and relationships across evidence, not just store files |
| Support evidentiary use | evidentiary readiness query | Legal and advocacy teams can see what is ready, limited, or unsafe to use |
| Preserve metadata and chain of custody | `metadata_json`, `file_sha256`, `custody_events` | Every file has provenance, integrity checks, and transfer history |
| Optimise investigative workflows | verification steps and readiness status | Investigators can see what action is needed next |
| Explore AI responsibly | AI guidance and pilot framework | AI supports triage and productivity but does not replace verification or legal judgement |
| Train staff and CSO partners | user guide and training outline | Non-technical users get safe, simple, repeatable workflows |
| Data Protection Lead | restricted records, retention, access logs, DPIA triggers | GDPR and protection risks are built into daily operations |

## How to Explain This to Different Stakeholders

### Leadership

> This system gives Videre a defensible view of its sensitive evidence estate: what we hold, where it came from, who accessed it, whether it is verified, whether it is legally usable, and what risks remain.

Focus on risk visibility, legal defensibility, compliance, continuity, and vendor/system decisions.

### Investigators and Verification Teams

> The database helps you know what evidence is strong, what needs follow-up, and what cannot yet be used. It reduces manual tracking and makes verification work visible.

Focus on missing metadata, custody gaps, duplicates, corroboration, and next actions.

### Legal and Accountability Teams

> The system separates possession of material from evidentiary readiness. A file may exist, but it is only ready for legal use when custody, verification, metadata, and review controls are complete.

Focus on hashes, custody events, verification steps, export approvals, restrictions, and auditability.

### Programme and CSO Partner Teams

> The workflow is designed to make safe submission practical for partners, including low-connectivity and high-risk contexts.

Focus on secure collection, safe transfer, source protection, minimal required metadata, low-tech fallback routes, and training.

### Data Protection / Compliance Stakeholders

> Sensitive information is classified, access-controlled, retained according to purpose, and reviewed before external sharing or new processing such as AI.

Focus on lawful basis, minimisation, retention, restricted access, breach response, and DPIAs.

## Four-Layer Interpretation Model

| Layer | Question | Database controls | Stakeholder output |
| --- | --- | --- | --- |
| Raw evidence | What did we receive? | `media_files`, `file_sha256`, `storage_uri`, `metadata_json` | Intake register, storage confirmation, missing metadata report |
| Provenance and protection | Can we trust handling and protect people? | `sources`, `custody_events`, `access_logs`, sensitivity | Custody gap report, restricted access review, source-risk list |
| Verification and analysis | What can we responsibly say? | `verification_steps`, `incidents`, `locations`, `alleged_actors`, `tags` | Corroboration matrix, pattern report, limitations note |
| Use and disclosure | Who can use it, why, and under what limits? | `legal_reviews`, `exports`, legal status, access classification | Legal pack, advocacy-safe summary, export audit log |

## Continuous Intake and Processing Flow

```text
Receive -> Register -> Preserve -> Protect -> Verify -> Analyse -> Review -> Package -> Export -> Retain/Archive
```

1. Receive from field collector, CSO partner, investigator, public source, secure upload, or offline handover.
2. Register intake ID, source code, received timestamp, sensitivity, and storage location.
3. Preserve original file, calculate hash, extract metadata, prevent overwrite.
4. Protect with access classification, source-risk controls, retention category, and legal hold where needed.
5. Verify through geolocation, chronolocation, source assessment, duplicate detection, corroboration, and technical review.
6. Analyse links between media, incidents, actors, locations, time periods, tags, and related sources.
7. Review through legal, data protection, and AI risk gates.
8. Package internal reports, legal evidence packs, advocacy summaries, or partner feedback.
9. Export only after approval, redaction, hash creation, transfer logging, and recipient restrictions.
10. Retain, archive, or delete according to retention schedule and legal hold.

## Continuous Operating Rhythm

| Frequency | Activity | Owner |
| --- | --- | --- |
| Daily | Failed uploads, new restricted records, missing metadata, urgent legal flags | Database Manager |
| Twice weekly | Custody gaps, duplicate media, verification backlog | Database Manager + Investigations |
| Weekly | Restricted access review and vendor tickets | Database Manager |
| Monthly | Evidence readiness report, storage growth, backup restore check, policy exceptions | Database Manager + Leadership |
| Quarterly | Access recertification, retention review, vendor review, training refresh | Database Manager + Data Protection Lead |
| Before migration or AI pilot | DPIA/risk review, test plan, approval gates | Database Manager + Legal/Leadership |

## GenAI and Supporting Tools

Good candidate uses:

- Transcription and translation for internal review.
- Entity extraction from notes or transcripts.
- Similarity detection across transcripts or descriptions.
- Broad triage classification.
- Drafting training materials from approved policy text.

Uses to reject or tightly restrict:

- Uploading raw sensitive media to external SaaS without approval.
- Identifying people in footage.
- Inferring perpetrator identity.
- Drawing legal conclusions.
- Publishing AI-generated summaries without human verification.

Minimum controls:

- Data sensitivity review.
- Tool classification: local, private cloud, approved vendor, or prohibited external tool.
- Vendor terms review: no training on data, clear retention rules, deletion rights, access controls.
- Human review before outputs enter verification or reporting.
- AI-assisted output labelling.
- Audit log of tool, version, prompt class, reviewer, date, and decision.
- Redaction before AI processing where possible.
- DPIA for systematic AI processing of sensitive data.

## Interview Closing Statement

> My approach would be to make the system trustworthy at every stage: safe intake, secure storage, preserved metadata, clear custody, structured analysis, responsible verification, careful legal and data protection review, and controlled disclosure. That gives investigators practical tools while giving leadership, legal teams, and partners confidence that sensitive evidence is handled responsibly.
