# Admin API lookup

## Tools
- `bexio_users`: list, get, me, list_fictional, get_fictional, create_fictional, update_fictional, delete_fictional, permissions.
- `bexio_notes`: list, search, get, create, update, delete.
- `bexio_tasks`: list, search, get, create, update, delete, list_priorities, list_statuses.
- `bexio_company_profile`: list, get (read-only).
- `bexio_master_data`: list, search, get, create, update, delete by resource.
- Scopes: notes `note_*`, tasks `task_*` · rest: user rights only · spec `general` = not requestable.

## Users + permissions
- `permissions`: activated modules + per-module rights, e.g. `"contact": {"activation": "enabled", "edit": "own", "show": "all"}`.
- Keys incl. accounting_reports, banking, banking_direct, contact, expense, fm (inbox), kb_bill, kb_invoice, kb_offer, kb_order, kb_article_order, monitoring, project, stockmanagement, user_administration.
- Fictional user fields: `salutation_type` (`male` | `female`), `firstname`, `lastname`, `email`; update PATCH.

## Notes + tasks
- Note create requires `user_id`, `event_start` (`2019-01-16 14:20:00`), `subject`; optional `info`, `contact_id`, `pr_project_id`.
- Task create requires `user_id`, `subject`; optional `finish_date`, `info`, `contact_id`, `pr_project_id`, `todo_status_id` (`list_statuses`), `todo_priority_id` (`list_priorities`), `have_remember` (+ `remember_type_id`, `remember_time_id`).
- Task search: subject, updated_at, user_id, contact_id, todo_status_id.

## Company profile
- `list` / `get`: one profile per account · name, address, `address_nr` (extra address line), postcode, city, `legal_form`, `mail`, `mwst_nr`, `ust_id_nr`, `trade_register_nr`.

## Master data
| Resource | Actions | Create requires |
|---|---|---|
| salutations, titles, units | list, search (`name`), get, create, update, delete | `name` |
| countries | same; search `name`, `name_short` | `name`, `name_short`, `iso3166_alpha2` |
| languages | list, search (`name`, `iso_639_1`); read-only | |
| payment_types, communication_types | list, search (`name`); read-only | |
- `business_activities`: see `bexio-projects`.
- Language records: `decimal_point`, `thousands_separator`, `date_format_id` (1 = `DD.MM.YYYY`).
