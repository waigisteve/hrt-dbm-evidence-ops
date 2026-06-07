# Stakeholder Dashboard Framework

## Design Principle

Each dashboard is shaped around the decision-making urgency and cognitive load of its stakeholder. Human-rights investigations need different levels of detail: leadership needs strategic health, investigators need workflow queues, legal teams need precise evidence status, partners need masked aggregates, compliance teams need alerts, and AI reviewers need quality-assurance queues.

## Stakeholder Archetypes

| Stakeholder | Dashboard type | Primary purpose | Design priority |
| --- | --- | --- | --- |
| Leadership | Strategic / executive summary | Organisational risk, throughput, readiness, resource prioritisation | KPI cards, simple trend/readiness bars, no raw evidence table |
| Investigations | Operational / tactical | Verification work, pattern detection, evidence pipeline management | Filters, pipeline visuals, workflow drilldowns, granular queues |
| Legal | Analytical / compliance | Legal readiness, custody adequacy, restrictions, evidence-pack decisions | Precise tables, exact statuses, next legal action |
| CSO Partners | Collaborative / restricted external | Safe feedback on submission quality and macro trends | Aggressive masking and aggregation |
| Data Protection & Monitoring | Compliance / audit | Security, GDPR, retention, system and evidence health | Alert-driven cards and conditional status |
| AI Review | Quality assurance / workload acceleration | AI triage candidates, pilot lanes, human-in-the-loop queue, controls | Clear split between AI suggestion and human decision |

## Implemented Dashboard Behaviours

- Leadership shows executive cards and incident readiness progress, avoiding raw evidence rows.
- Investigations keeps the full working evidence queue with filters, pipeline visuals, and operational charts.
- Legal shows precise fields and a computed next legal action for each item.
- CSO Partners receive masked area-level follow-up summaries rather than filenames, sources, hashes, or exact details.
- Monitoring exposes security, performance, data-quality, and source-skew alerts.
- AI Review shows assistive workload acceleration, pilot lanes, the human-in-the-loop queue, prohibited uses, and keeps auto-approved outputs at zero by design.

## One-Click to Workflow Rule

Dashboard visuals are not passive. Clicking a leadership readiness card:

1. Sets the incident filter.
2. Switches the user to the Investigations view.
3. Shows the exact filtered working queue.

This models the operational behaviour expected from a practical investigative data system: a spike or risk signal should lead directly to the records that need action.

## Filter Model

Filters apply consistently across KPIs, charts, and stakeholder views:

- Search text.
- Incident.
- Media type.
- Verification state.
- Legal state.
- Access class.
- Safety scan state.

## Interview Framing

> I would not give every stakeholder the same dashboard. Leadership should see strategic health, investigators need operational drilldowns, legal teams need precision and dates/statuses, CSO partners need masked aggregate feedback, data protection needs alerts, and AI review needs human-in-the-loop quality controls.

## Design References Applied

The dashboard follows Qlik-style principles: know the audience, choose the right dashboard type, focus on essential metrics, tell a clear data story, use appropriate chart types, keep the layout simple, use visual cues for actions, and iterate with user feedback.

It also follows the executive/manager/analyst split:

- Executives get 3-5 strategic metrics and quick status.
- Managers/operators get filters, comparative visuals, and workflow queues.
- Analysts/legal users get dense tables, exact statuses, and clear next actions.
