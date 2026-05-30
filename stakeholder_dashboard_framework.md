# Stakeholder Dashboard Framework

## Design Principle

Each dashboard is shaped around the decision-making urgency and cognitive load of its stakeholder. Human-rights investigations need different levels of detail: leadership needs strategic health, investigators need workflow queues, legal teams need precise evidence status, partners need masked aggregates, compliance teams need alerts, and AI reviewers need quality-assurance queues.

## Stakeholder Archetypes

| Stakeholder | Dashboard type | Primary purpose | Design priority |
| --- | --- | --- | --- |
| Leadership | Strategic / executive summary | Organisational risk, throughput, readiness, resource prioritisation | KPI cards, simple trend/readiness bars, no raw evidence table |
| Investigations | Operational / tactical | Verification work, pattern detection, evidence pipeline management | Filters, heatmaps, workflow drilldowns, granular queues |
| Legal | Analytical / compliance | Legal readiness, custody adequacy, restrictions, evidence-pack decisions | Precise tables, exact statuses, next legal action |
| CSO Partners | Collaborative / restricted external | Safe feedback on submission quality and macro trends | Aggressive masking and aggregation |
| Data Protection & Monitoring | Compliance / audit | Security, GDPR, retention, system and evidence health | Alert-driven cards and conditional status |
| AI Review | Quality assurance | AI triage candidates, human-in-the-loop queue, controls | Clear split between AI suggestion and human decision |

## Implemented Dashboard Behaviours

- Leadership shows executive cards and incident readiness progress, avoiding raw evidence rows.
- Investigations keeps the full working evidence queue with filters and visual heatmap.
- Legal shows precise fields and a computed next legal action for each item.
- CSO Partners receive masked area-level follow-up summaries rather than filenames, sources, hashes, or exact details.
- Monitoring exposes security, performance, data-quality, and source-skew alerts.
- AI Review shows the human-in-the-loop queue and keeps auto-approved outputs at zero by design.

## One-Click to Workflow Rule

Dashboard visuals are not passive. Clicking an incident heatmap cell or leadership readiness card:

1. Sets the incident filter.
2. Switches the user to the Investigations view.
3. Shows the exact filtered working queue.

This models the operational behaviour expected from a practical investigative data system: a spike or risk signal should lead directly to the records that need action.

## Filter Model

Filters apply consistently across KPIs, charts, heatmap, and stakeholder views:

- Search text.
- Incident.
- Media type.
- Verification state.
- Legal state.
- Access class.
- Safety scan state.

## Interview Framing

> I would not give every stakeholder the same dashboard. Leadership should see strategic health, investigators need operational drilldowns, legal teams need precision and dates/statuses, CSO partners need masked aggregate feedback, data protection needs alerts, and AI review needs human-in-the-loop quality controls.
