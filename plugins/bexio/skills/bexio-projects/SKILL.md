---
name: bexio-projects
description: 'Use when a Bexio request is about projects (Projekt), milestones (Meilenstein), work packages (Arbeitspaket), timesheets and time tracking (Zeiterfassung, Stunden, Rapport) or business activities (Tätigkeit, Leistungsart) — list hours per project, create or edit a project or time entry, archive or delete. Load the core skill bexio first.'
---

# Bexio projects — projects, planning, timesheets, business activities

Core `bexio` first. All 30 ops: `reference.md`.

## Use / not here
- Hours per project · project status · milestones, work packages · create / edit projects + time entries · archive · delete.
- Not here: invoicing hours → `bexio-sales` · notes / tasks on a project, communication types → `bexio-admin`.

## Tools
| Tool | Actions | Gated |
|---|---|---|
| `bexio_projects` | list, search, get, create, update, delete, archive, unarchive, list_statuses, list_types | – |
| `bexio_project_planning` (`resource`: milestones, work_packages) | list, get, create, update, delete | – |
| `bexio_timesheets` | list, search, get, create, update, delete, list_statuses | – |
| `bexio_master_data` (`resource: business_activities`; tool owned by `bexio-admin`) | list, search, create | – (no delete endpoint) |
- Scopes: projects + planning `project_show` / `project_edit` · timesheets `monitoring_show` / `monitoring_edit` · statuses, types, business activities: user rights only [D:v2CreateProject], [D:v2CreateTimesheet], [D:v2CreateBusinessActivity].

## Projects (`/2.0/pr_project`, integer ids)
- Create required: `name`, `pr_state_id` (`list_statuses`), `pr_project_type_id` (`list_types`), `contact_id`, `user_id` [D:v2CreateProject].
- Optional:
  - `document_nr` (only with automatic numbering off) · `start_date` / `end_date` (`2019-07-12 00:00:00`) · `comment`, `contact_sub_id`
  - `pr_invoice_type_id`: 1 hourly rate service, 2 hourly rate employee, 3 hourly rate project, 4 fixed · `pr_invoice_type_amount` only with 3, 4
  - `pr_budget_type_id`: 1 costs, 2 hours, 3 service budget, 4 service employees · `pr_budget_type_amount` only with 1, 2
- Search fields `name`, `contact_id`, `pr_state_id` only [D:v2SearchProjects].
- `archive` / `unarchive` = non-destructive [D:v2ArchiveProject], [D:v2UnarchiveProject] · delete permanent.

## Milestones + work packages (3.0, need `project_id`)
- Milestone: `name` required; `end_date`, `comment`, `pr_parent_milestone_id` [D:CreateMilestone].
- Work package: `name` required; `estimated_time_in_hours`, `spent_time_in_hours`, `comment`, `pr_milestone_id` [D:CreateWorkPackage].
- Edit verbs differ: projects + milestones POST, work packages PATCH (tool handles it) · deletes permanent.

## Timesheets (`/2.0/timesheet`)
- Create required: `user_id`, `client_service_id` (business activity), `allowable_bill` (bool), `tracking` [D:v2CreateTimesheet].
- `tracking`:
  - `{type: "duration", date, duration}` · `duration` string format n.d. → copy an existing timesheet's
  - `{type: "range", start: "2019-05-20 14:22:48", end: …}`
  - timesheet `date` + `duration` read-only → set via `tracking`
- Optional: `status_id` (`list_statuses`), `text`, `contact_id`, `pr_project_id`, `pr_package_id`, `pr_milestone_id`.
- Search fields id, client_service_id, contact_id, user_id, pr_project_id, status_id · `order_by` id, date [D:v2SearchTimesheets].
- Hours per project: `search` `pr_project_id` `=`, page through, sum `duration` · state date range + billable (`allowable_bill`) only or all.

## Business activities (`bexio_master_data`, `resource: business_activities`)
- list, search (`name`), create (`name` required; `default_is_billable`, `default_price_per_hour`, `account_id`) · no get, edit, delete endpoint [D:v2CreateBusinessActivity].

## Gate
- None (core §3.1); all writes direct, deletes included.

## Direct writes with a skill check (core §3)
| Action | Check → report line |
|---|---|
| `bexio_projects.delete` | `bexio_timesheets.search` `pr_project_id` → linked → "<n> timesheets were linked" |

## Gotchas
1. Finished projects: `archive`, not delete.

---
Sources: https://docs.bexio.com/ (OpenAPI 3.0.2; ops cited above; full list `reference.md`), fetched 2026-09-24.
