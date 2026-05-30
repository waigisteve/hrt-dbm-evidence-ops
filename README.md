# Videre Database Manager Preparation Pack

This pack is a practical work sample for the Videre Database Manager next step. It is built around a fictional investigation so it can demonstrate secure investigative data management without using real victims, real conflicts, or sensitive personal data.

## How to Use This Pack

1. Start with `work_sample_pack.md`.
   - Use it as the main evidence-systems proposal.
   - Treat it as the document you could discuss in a technical interview.

2. Review the SQL files in `sql/`.
   - `schema.sql` defines a PostgreSQL relational model for investigative evidence.
   - `sample_data.sql` adds a fictional dataset for practice.
   - `continuous_intake_simulation.sql` simulates a new batch of sensitive video, image, and field-note intake.
   - `analysis_queries.sql` contains practical queries for verification, chain of custody, migration validation, and evidentiary readiness.

Optional local run:

```bash
createdb videre_prep
psql -d videre_prep -f sql/schema.sql
psql -d videre_prep -f sql/sample_data.sql
psql -d videre_prep -f sql/continuous_intake_simulation.sql
psql -d videre_prep -f sql/analysis_queries.sql
```

3. Rehearse with `interview_simulation.md`.
   - Practice the 10-minute presentation.
   - Use the panel questions to prepare concise, grounded answers.

4. Use `stakeholder_operating_model.md`.
   - Explain how raw sensitive multimedia becomes controlled intelligence, legal evidence, and partner-safe outputs.

5. Use `live_dashboard_runbook.md`.
   - Run a live stakeholder dashboard with PostgreSQL OLTP, DuckDB OLAP, simulated logins, and AI review.

6. Use `architecture_and_business_case.md`.
   - Explain the OLTP/OLAP architecture, business workflow, achieved outcomes, gaps, and diagrams.net assets.
   - dbdiagram schema: https://dbdiagram.io/d/hrights-ngo-schema-6a1ac16ff15b4b045235d88d

7. Use `schema_security_workflow.md`.
   - Explain the schema, table dependencies, security measures, data expectations, and investigative/legal workflow.

8. Use `nosql_media_and_monitoring_design.md`.
   - Explain the NoSQL media catalog, safe media scaffolding, visual analytics, AI controls, and monitoring posture.

9. Use `stakeholder_dashboard_framework.md`.
   - Explain the stakeholder-specific dashboard design, filters, masking, and one-click workflow drilldowns.

10. Use `source_references.md`.
   - Ground your answers in Videre's public model and recognised evidence-management standards.

11. Follow `practice_schedule.md`.
   - The schedule gives a 3-week route from research to final mock interview.

## Positioning Statement

I would first stabilise and understand the existing systems, then improve evidence integrity and user confidence, then scope any migration only where it clearly reduces risk or improves investigative value.

## Core Message for Videre

This role is not only database administration. It is secure investigative systems leadership: operating closed-source evidence platforms, strengthening relational analysis, preserving metadata and chain of custody, guiding responsible AI adoption, training non-technical users, supporting CSO partners, and leading data protection practice.

## Schema Note

The `persons` table is pseudonymous and now connects through `incident_persons` and `media_persons`. This allows investigative analysis of witnesses, victims, collectors, reviewers, or visible persons while preserving protection controls and avoiding direct personal identifiers in operational dashboards.
