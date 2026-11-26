---
name: bexio-admin
description: 'Use when a Bexio request is about users and rights (Benutzer, Berechtigung, who is signed in), fictional users, notes (Notiz), tasks (Aufgabe, Pendenz), the company profile (Firmenprofil, MWST-Nr, UID), or master data lookups: countries (Land), languages (Sprache), payment types (Zahlungsart), units (Einheit), salutations (Anrede), titles (Titel), communication types. Load the core skill bexio first.'
---

# Bexio admin: users, permissions, notes, tasks, company profile, master data

Core `bexio` first; route by core §8. Per-op detail: `reference.md`. Read `references/admin-fields.md` for actions, scopes, fields and master data.

## Tools
`bexio_users`, `bexio_notes`, `bexio_tasks`, `bexio_company_profile`, `bexio_master_data`.

## Users + permissions
- Regular users: read-only, no write endpoint (`list`, `get`, `me` only) · `is_superadmin` / `is_accountant` only returned with admin rights.
- Fictional users (dropdowns, no login): create requires `salutation_type` (`male` | `female`), `firstname`, `lastname`, `email` (unique across all users) · update PATCH · delete permanent.
- 403 on write → check that module's `edit`.

## Company profile
- Used by: company questions (`name`) · gated previews: `company.name` from the dry run (core §3.2) · `send` recipient check: `mail` domain (core §3.4, `bexio-sales`).

## Gate
- None (core §3.1); all writes direct, deletes included (master data, notes, tasks, fictional users) → report id + name.

## Gotchas
1. Company profile `address_nr` ≠ house number.
