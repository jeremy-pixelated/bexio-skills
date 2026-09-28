---
name: bexio-admin
description: 'Use when a Bexio request is about users and rights (Benutzer, Berechtigung, who is signed in), fictional users, notes (Notiz), tasks (Aufgabe, Pendenz), the company profile (Firmenprofil, MWST-Nr, UID), or master data lookups: countries (Land), languages (Sprache), payment types (Zahlungsart), units (Einheit), salutations (Anrede), titles (Titel), communication types. Load the core skill bexio first.'
---

# Bexio admin — users, permissions, notes, tasks, company profile, master data

Core `bexio` first (router, gate, flags). All 55 ops: `reference.md`.

## Use / not here
- Who is signed in (`me`), what that user may edit (`permissions`) · company name, VAT number, legal form · notes + tasks, also on contacts / projects · lookup ids: country, language, unit, salutation, title, payment type, communication type.
- Not here: business activities (same tool, `resource: business_activities`) → `bexio-projects` · the company's bank accounts → `bexio-banking`.

## Tools
| Tool | Actions | Gated |
|---|---|---|
| `bexio_users` | list, get, me, list_fictional, get_fictional, create_fictional, update_fictional, delete_fictional, permissions | – |
| `bexio_notes` | list, search, get, create, update, delete | – |
| `bexio_tasks` | list, search, get, create, update, delete, list_priorities, list_statuses | – |
| `bexio_company_profile` | list, get | – (read-only) |
| `bexio_master_data` (`resource`: salutations, titles, units, countries, languages, payment_types, communication_types, business_activities) | list, search, get, create, update, delete | – |
- Scopes: notes `note_*`, tasks `task_*` · rest: user rights only [D:v3ListUsers], [D:v2CreateNote] · spec `general` = not requestable [D§Authentication/API-Scopes].

## Users + permissions
- Regular users read-only via API: no write endpoint (`list`, `get`, `me` only) [D:v3ListUsers], [D:v3ShowMe]. `is_superadmin` / `is_accountant` "only included if the user has the necessary admin rights".
- Fictional users (dropdowns, no login): create requires `salutation_type` (`male` | `female`), `firstname`, `lastname`, `email` (unique across all users); update PATCH; delete permanent [D:v3CreateFictionalUser].
- `permissions` → activated modules + per-module rights, e.g. `"contact": {"activation": "enabled", "edit": "own", "show": "all"}`. Keys incl. accounting_reports, banking, banking_direct, contact, expense, fm (inbox), kb_bill, kb_invoice, kb_offer, kb_order, kb_article_order, monitoring, project, stockmanagement, user_administration [D:Permissions].
- 403 on a write → check that module's `edit` here.

## Notes + tasks
- Note create requires `user_id`, `event_start` (`2019-01-16 14:20:00`), `subject`; optional `info`, `contact_id`, `pr_project_id` [D:v2CreateNote].
- Task create requires `user_id`, `subject`; optional `finish_date`, `info`, `contact_id`, `pr_project_id`, `todo_status_id` (`list_statuses`), `todo_priority_id` (`list_priorities`), `have_remember` (+ `remember_type_id`, `remember_time_id`) [D:v2CreateTask].
- Task search: subject, updated_at, user_id, contact_id, todo_status_id.

## Company profile
- `list` / `get`: one profile per account; name, address, `address_nr` (extra address line, not a house number), postcode, city, `legal_form`, `mail`, `mwst_nr`, `ust_id_nr`, `trade_register_nr` [D:v2ListCompanyProfile].
- `name` → explicit company questions; gated previews take `company.name` from the dry run (core §3.2); `mail` domain → recipient check on `send` (core §3.4, `bexio-sales`).

## Master data
| Resource | Actions | Create requires |
|---|---|---|
| salutations, titles, units | list, search (`name`), get, create, update, delete | `name` |
| countries | same; search `name`, `name_short` | `name`, `name_short`, `iso3166_alpha2` |
| languages | list, search (`name`, `iso_639_1`); read-only | – |
| payment_types, communication_types | list, search (`name`); read-only | – |
- Sources: [D:v2CreateSalutation], [D:v2CreateCountry], [D:v2ListLanguages], [D:v2ListPaymentTypes], [D:v2ListCommunicationTypes].
- Language records: `decimal_point`, `thousands_separator`, `date_format_id` (1 = `DD.MM.YYYY`).

## Gate
- No gated action here (core §3.1). All writes run directly, deletes included (master data, notes, tasks, fictional users) → report id + name.

## Gotchas
1. No requestable `general` scope; access = user rights.
2. Regular users: no create / change via API.
3. `address_nr` in the company profile ≠ house number.

---
Sources: https://docs.bexio.com/ (OpenAPI 3.0.2; ops cited above; full list `reference.md`; §Authentication/API-Scopes), fetched 2026-09-24.
