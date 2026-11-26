---
name: bexio-projects
description: 'Use when a Bexio request is about projects (Projekt), milestones (Meilenstein), work packages (Arbeitspaket), timesheets and time tracking (Zeiterfassung, Stunden, Rapport) or business activities (Tätigkeit, Leistungsart): list hours per project, create or edit a project or time entry, archive or delete. Load the core skill bexio first.'
---

# Bexio projects: projects, planning, timesheets, business activities

Core `bexio` first; route by core §8. Per-op detail: `reference.md`. Read `references/project-fields.md` for actions, scopes, field mappings, search and tracking formats.

## Tools
`bexio_projects`, `bexio_project_planning`, `bexio_timesheets`, `bexio_master_data`.

## Projects (`/2.0/pr_project`, integer ids)
- `archive` / `unarchive` = non-destructive · delete permanent.
- Milestone and work-package deletes permanent.
- `pr_invoice_type_amount` only with 3, 4 · `pr_budget_type_amount` only with 1, 2.

## Timesheets (`/2.0/timesheet`)
- `duration` string format n.d. → copy an existing timesheet's.
- timesheet `date` + `duration` read-only → set via `tracking`.
- Hours per project: `search` `pr_project_id` `=`, page through, sum `duration` · state date range + billable (`allowable_bill`) only or all.

## Business activities (`bexio_master_data`, `resource: business_activities`)
- No get, edit, delete endpoint.

## Gate
- None (core §3.1); all writes direct, deletes included.

## Direct writes with a skill check (core §3)
| Action | Check → report line |
|---|---|
| `bexio_projects.delete` | `bexio_timesheets.search` `pr_project_id` → linked → "<n> timesheets were linked" |

## Gotchas
1. Finished projects: `archive`, not delete.
