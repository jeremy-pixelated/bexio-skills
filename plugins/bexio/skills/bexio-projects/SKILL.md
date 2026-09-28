---
name: bexio-projects
description: 'Use when a Bexio request is about projects (Projekt), milestones (Meilenstein), work packages (Arbeitspaket), timesheets and time tracking (Zeiterfassung, Stunden, Rapport) or business activities (Tätigkeit, Leistungsart) — list hours per project, create or edit a project or time entry, archive or delete. Load the core skill bexio first.'
---

# Bexio projects — projects, planning, timesheets, business activities

Core `bexio` first (router, gate, flags). All 30 ops: `reference.md`.

## Use / not here
- Hours per project; project status; milestones, work packages · create / edit projects + time entries; archive; delete.
- Not here: invoicing hours → `bexio-sales` · notes / tasks on a project → `bexio-admin` · communication types → `bexio-admin`.

## Tools
| Tool | Actions | Gated |
|---|---|---|
| `bexio_projects` | list, search, get, create, update, delete, archive, unarchive, list_statuses, list_types | delete |
| `bexio_project_planning` (`resource`: milestones, work_packages) | list, get, create, update, delete | delete |
| `bexio_timesheets` | list, search, get, create, update, delete, list_statuses | delete |
| `bexio_master_data` (`resource: business_activities`; tool owned by `bexio-admin`) | list, search, create | – (business activities have no delete endpoint) |
- Scopes: projects + planning `project_show` / `project_edit`; timesheets `monitoring_show` / `monitoring_edit`; statuses, types, business activities: user rights only [D:v2CreateProject], [D:v2CreateTimesheet], [D:v2CreateBusinessActivity].

## Projects (`/2.0/pr_project`, integer ids)
- Create required: `name`, `pr_state_id` (`list_statuses`), `pr_project_type_id` (`list_types`), `contact_id`, `user_id` [D:v2CreateProject].
- Optional: `document_nr` (only with automatic numbering off), `start_date` / `end_date` (`2019-07-12 00:00:00`), `comment`, `contact_sub_id`, `pr_invoice_type_id` (1 hourly rate service, 2 hourly rate employee, 3 hourly rate project, 4 fixed) + `pr_invoice_type_amount` (only 3, 4), `pr_budget_type_id` (1 costs, 2 hours, 3 service budget, 4 service employees) + `pr_budget_type_amount` (only 1, 2).
- Search fields `name`, `contact_id`, `pr_state_id` only [D:v2SearchProjects].
- `archive` / `unarchive` = non-destructive alternative [D:v2ArchiveProject], [D:v2UnarchiveProject]. Delete permanent.

## Milestones + work packages (3.0, need `project_id`)
- Milestone: `name` required; `end_date`, `comment`, `pr_parent_milestone_id` [D:CreateMilestone].
- Work package: `name` required; `estimated_time_in_hours`, `spent_time_in_hours`, `comment`, `pr_milestone_id` [D:CreateWorkPackage].
- Edit: milestones POST, work packages PATCH (verb: tool). Deletes permanent.

## Timesheets (`/2.0/timesheet`)
- Create required: `user_id`, `client_service_id` (business activity), `allowable_bill` (bool), `tracking` [D:v2CreateTimesheet].
- `tracking` = `{type: "duration", date, duration}` (`duration` string format n.d. → copy the format of an existing timesheet) or `{type: "range", start: "2019-05-20 14:22:48", end: …}`. Timesheet `date` + `duration` read-only → set via `tracking`.
- Optional: `status_id` (`list_statuses`), `text`, `contact_id`, `pr_project_id`, `pr_package_id`, `pr_milestone_id`.
- Search fields id, client_service_id, contact_id, user_id, pr_project_id, status_id; `order_by` id, date [D:v2SearchTimesheets].
- Hours per project: `search` `pr_project_id` `=`, page through, sum `duration`; state date range + billable (`allowable_bill`) only or all.

## Business activities (`bexio_master_data`, `resource: business_activities`)
- list, search (`name`), create (`name` required; `default_is_billable`, `default_price_per_hour`, `account_id`). No get, edit or delete endpoint [D:v2CreateBusinessActivity].

## Gate rows (core §3.2: dry run → one preview → one yes → call with the dry run's `acknowledge_flags`)
| Row | Class | Preview (`pre_image` + `would_send`) | Skill pre-check |
|---|---|---|---|
| `bexio_projects.delete` | delete | id, `nr`, name, customer, status; "permanent, `archive` keeps it" | `bexio_timesheets.search` `pr_project_id` → linked → ⚑ timesheets linked |
| `bexio_project_planning.delete` | delete | project name, resource (milestone / work package), id, name, hours (work package); "permanent" | – |
| `bexio_timesheets.delete` | delete | id, user, date, duration, project, business activity, billable flag; "permanent" | – |

## Gotchas
1. Edit verbs differ (projects / milestones POST, work packages PATCH).
2. Timesheet `date` / `duration` read-only → `tracking`.
3. Finished projects: `archive` over delete.

---
Sources: https://docs.bexio.com/ (OpenAPI 3.0.2; ops cited above; full list `reference.md`), fetched 2026-09-24.
