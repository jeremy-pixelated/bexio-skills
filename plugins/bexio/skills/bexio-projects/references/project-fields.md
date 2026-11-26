# Project API lookup

## Tools
- `bexio_projects`: list, search, get, create, update, delete, archive, unarchive, list_statuses, list_types.
- `bexio_project_planning` (`resource`: milestones, work_packages): list, get, create, update, delete.
- `bexio_timesheets`: list, search, get, create, update, delete, list_statuses.
- `bexio_master_data` (`resource: business_activities`; tool owned by `bexio-admin`): list, search, create.
- Scopes: projects + planning `project_show` / `project_edit` · timesheets `monitoring_show` / `monitoring_edit` · statuses, types, business activities: user rights only.

## Projects (`/2.0/pr_project`, integer ids)
- Create required: `name`, `pr_state_id` (`list_statuses`), `pr_project_type_id` (`list_types`), `contact_id`, `user_id`.
- Optional: `document_nr` (only with automatic numbering off) · `start_date` / `end_date` (`2019-07-12 00:00:00`) · `comment`, `contact_sub_id`.
- `pr_invoice_type_id`: 1 hourly rate service, 2 hourly rate employee, 3 hourly rate project, 4 fixed · `pr_invoice_type_amount` only with 3, 4.
- `pr_budget_type_id`: 1 costs, 2 hours, 3 service budget, 4 service employees · `pr_budget_type_amount` only with 1, 2.
- Search fields `name`, `contact_id`, `pr_state_id` only.

## Milestones + work packages (3.0, need `project_id`)
- Milestone: `name` required; `end_date`, `comment`, `pr_parent_milestone_id`.
- Work package: `name` required; `estimated_time_in_hours`, `spent_time_in_hours`, `comment`, `pr_milestone_id`.
- Edit verbs differ: projects + milestones POST, work packages PATCH (tool handles it).

## Timesheets (`/2.0/timesheet`)
- Create required: `user_id`, `client_service_id` (business activity), `allowable_bill` (bool), `tracking`.
- `tracking`: `{type: "duration", date, duration}` or `{type: "range", start: "2019-05-20 14:22:48", end: …}`.
- Optional: `status_id` (`list_statuses`), `text`, `contact_id`, `pr_project_id`, `pr_package_id`, `pr_milestone_id`.
- Search fields id, client_service_id, contact_id, user_id, pr_project_id, status_id · `order_by` id, date.

## Business activities (`bexio_master_data`, `resource: business_activities`)
- list, search (`name`), create (`name` required; `default_is_billable`, `default_price_per_hour`, `account_id`).
