# HRT Database Manager Interview Simulation

## 10-Minute Presentation

### Opening

I understand this role as secure investigative systems leadership, not only database administration. My first priority would be to understand and stabilise the existing closed-source video and information systems, protect evidence integrity, and build user confidence. I would then improve relational analysis and workflows around those systems. I would only recommend migration where the evidence shows that it reduces risk or materially improves investigative value.

### Minute-by-Minute Structure

| Time | Message |
| --- | --- |
| 0:00-1:00 | Role framing: secure systems, legal defensibility, user adoption, data protection |
| 1:00-2:00 | First 30 days: discovery, architecture, risks, users, vendors, access, backups |
| 2:00-3:30 | Evidence integrity: metadata, hashes, custody events, audit logs, legal review |
| 3:30-5:00 | Relational analysis: incidents, media, sources, actors, locations, verification status |
| 5:00-6:30 | Migration judgement: improve, replace, or hybrid; pilot before cutover |
| 6:30-7:30 | Team support: training, low-IT-literacy workflows, CSO partner guidance |
| 7:30-8:30 | Data protection: GDPR, minimisation, retention, DPIAs, breach response |
| 8:30-9:30 | AI: careful pilots, human review, source protection, no unsupported conclusions |
| 9:30-10:00 | Close: trusted systems that help investigators work safely and defensibly |

## 45-Minute Panel Simulation

### Systems Management & Optimisation

**Question:** How would you manage a closed-source vendor system when you cannot directly change the internals?

**Answer frame:** I would document the architecture, data flows, permissions, vendor boundaries, and operational risks. Then I would strengthen what I can control: access reviews, intake standards, audit exports, backup checks, usage monitoring, user guidance, vendor SLAs, and integration points. If the platform cannot support a required evidentiary or security control, I would document the gap and propose mitigation, integration, or replacement options.

**Question:** What would you monitor weekly?

**Answer frame:** Upload failures, incomplete metadata, failed logins, inactive accounts, export requests, backup status, storage growth, unresolved vendor tickets, custody gaps, and cases approaching retention review.

### Strategic Development & Migration

**Question:** How would you decide whether to migrate?

**Answer frame:** I would not start with migration as the answer. I would assess risk, user needs, security, evidence integrity, cost, vendor dependency, integration limits, and operational pain. If improvement around the current system solves the problem, that is safer. If the system cannot meet core requirements, I would run a controlled pilot migration with validation before recommending cutover.

**Question:** How do you protect chain of custody during migration?

**Answer frame:** Preserve original identifiers, export source metadata, calculate and compare hashes, migrate custody history, record the migration itself as a custody event, validate relationships and permissions, sample high-risk records manually, and keep source data read-only until acceptance is complete.

### Relational Database Development

**Question:** What would the relational database add if HRT already has a video platform?

**Answer frame:** The video platform controls the original media. The relational layer helps connect incidents, sources, locations, actors, verification steps, legal review, custody events, and exports. It supports pattern analysis and evidentiary readiness without weakening control over original files.

**Question:** What is an example of a useful analytical query?

**Answer frame:** Identify all verified incidents in a location and period where two independent sources submitted media, custody is complete, legal review is approved, and alleged actor references match other incidents. That helps investigators see patterns and prepare defensible findings.

### Verification & Investigative Workflows

**Question:** How would you detect weak metadata?

**Answer frame:** I would define required fields by evidence type and run completeness reports: missing capture date, source, hash, location, verification status, collector code, consent/risk notes, or custody events. Weak records would be routed to investigators for remediation or flagged as limited-use.

**Question:** What does defensibility mean in this role?

**Answer frame:** A finding should be traceable back to source material, verification steps, custody history, reviewer decisions, and export controls. The system should make it clear what is known, unknown, disputed, and independently corroborated.

### AI & Innovation

**Question:** How would you decide whether AI transcription is safe?

**Answer frame:** I would start with sensitivity and threat modelling. If data includes identifiable victims, sources, or high-risk locations, I would avoid external SaaS unless legal, security, and vendor terms are acceptable. I would test accuracy, require human review, prevent outputs from becoming findings automatically, and log the tool, version, reviewer, and decision.

**Question:** What AI uses would you reject?

**Answer frame:** Automated verification conclusions, source identification, legal conclusions, unapproved upload of sensitive media to third-party tools, or publication decisions based on AI output.

### Team Support & Capacity Building

**Question:** How would you support colleagues with low IT literacy?

**Answer frame:** I would simplify the workflow, reduce unnecessary fields, use plain-language guides, provide role-based training, offer short live demos, build checklists, and create feedback channels. The goal is consistent safe practice, not technical perfection.

**Question:** How would you train CSO partners?

**Answer frame:** Focus on practical risk-aware basics: secure collection, device hygiene, encrypted transfer, metadata preservation, consent limits, source protection, and what to do when connectivity is poor or a device is lost.

### Data Protection & Compliance

**Question:** How would you act when programme teams want to keep everything just in case?

**Answer frame:** I would acknowledge the operational reason but test it against lawful basis, minimisation, retention, risk to individuals, and legal/archival value. I would propose retention categories rather than blanket deletion or indefinite storage, and document leadership decisions for high-risk exceptions.

**Question:** What would trigger a DPIA?

**Answer frame:** A new evidence platform, migration of large sensitive datasets, AI processing, new external sharing, new partner collection workflow, biometric or highly identifiable data processing, or systematic monitoring of vulnerable groups.

## Strong Questions to Ask HRT

- What are the most painful current limitations in the existing information systems?
- Where do investigative, legal, and programme teams currently lose time or confidence in the data?
- What parts of the closed-source video system are vendor-controlled versus internally configurable?
- What does success look like after six months in this role?
- Are the biggest risks currently technical, workflow-related, data protection-related, or adoption-related?
