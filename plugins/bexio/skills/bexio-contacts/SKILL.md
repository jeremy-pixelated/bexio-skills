---
name: bexio-contacts
description: 'Use when a Bexio request is about the contact master: customers (Kunde, Debitor-Stamm), suppliers as contacts (Lieferant anlegen, Kreditor-Stamm), persons, addresses, contact relations, contact groups (Kontaktgruppe), sectors (Branchen), additional addresses. Find, create, update, archive/delete, restore a contact, look up a contact_id / supplier_id (no IBAN field: supplier IBAN → bexio-purchase). Load the core skill bexio first.'
---

# Bexio contacts

Core `bexio` first; route by core §8. Per-op detail: `reference.md`. Read `references/contact-fields.md` for actions, scopes, payloads and search fields.

## Tools
`bexio_contacts`, `bexio_contact_relations`, `bexio_contact_groups`, `bexio_contact_sectors`, `bexio_additional_addresses`, `bexio_users.me`.

## Contacts (`/2.0/contact`, integer ids)
- `contact_group_ids`, `contact_branch_ids`: comma strings (`"1,2"`), not arrays.
- `update`: changed fields only (POST, partial).
- Delete = soft (archived; `show_archived: true` finds it) → `restore` → report id.
- Create only after a search without match (name, `nr`, email); for `bulk_create`, search each first.
- Relations: semantics n.d. → create only with both contacts user-named. Relation and additional address deletes are permanent.

## Gate
- None (core §3.1); all writes direct, deletes included.

## Direct writes with a skill check (core §3)
| Action | Check → report line |
|---|---|
| `bexio_contacts.delete` | open documents referencing it (`bexio_invoices.search` `contact_id`, `bexio_bills.list` by supplier) → "still referenced by <docs>; `restore` undoes the delete" |
| `bexio_contact_groups.delete` | contacts carrying it (`bexio_contacts.search` `contact_group_ids`) → "group was in use on <n> contacts" |

## Resolve the counterparty
1. `bexio_contacts.search` `nr` `=` (`like` = substring) or `name_1` `like`.
2. Several hits → list candidates (nr, name, city) → ask which; never guess.
3. Integer `id` → `contact_id` (sales) / `supplier_id` (bills, expenses).
