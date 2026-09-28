---
name: bexio-contacts
description: 'Use when a Bexio request is about the contact master: customers (Kunde, Debitor-Stamm), suppliers as contacts (Lieferant anlegen, Kreditor-Stamm), persons, addresses, contact relations, contact groups (Kontaktgruppe), sectors (Branchen), additional addresses — find, create, update, archive/delete, restore a contact, look up a contact_id / supplier_id (no IBAN field: supplier IBAN → bexio-purchase). Load the core skill bexio first.'
---

# Bexio contacts

Customers + suppliers = one contact master. Core `bexio` first. All 28 ops: `reference.md`.

## Use / not here
- Find customer / supplier (nr, address, email, group) · resolve `contact_id` / `supplier_id` · create, update, delete (archive), restore.
- Not here: salutations, titles, notes / tasks on contacts → `bexio-admin` · supplier IBAN → `bexio-purchase` (contact: no IBAN field).

## Tools
| Tool | Actions | Gated |
|---|---|---|
| `bexio_contacts` | list, search, get, create, update, delete, bulk_create, restore | – |
| `bexio_contact_relations` | list, search, get, create, update, delete | – |
| `bexio_contact_groups` | list, search, get, create, update, delete | – |
| `bexio_contact_sectors` | list, search | – (read-only) |
| `bexio_additional_addresses` | list, search, get, create, update, delete | – |
- Scopes: contacts, relations, additional addresses `contact_show` / `contact_edit` · groups + sectors: none requestable (user rights) [D:v2CreateContact], [D:v2CreateContactGroup].

## Contacts (`/2.0/contact`, integer ids)
- Create required: `contact_type_id` (1 company, 2 person), `name_1` (company / person's last name), `user_id` (`bexio_users.me`), `owner_id` [D:v2CreateContact].
- Optional:
  - `nr` (numeric; null = auto) · `name_2` (company addition / first name)
  - `street_name`, `house_number`, `address_addition`, `postcode`, `city`, `country_id` · single-line `address`: deprecated in requests since 2025-12-09, still in responses [D§Changelog]
  - `mail`, `phone_fixed`, `phone_mobile`, `language_id`, `remarks`
  - `contact_group_ids`, `contact_branch_ids`: comma strings (`"1,2"`), not arrays
- `update`: changed fields only (POST, partial).
- Delete = soft (archived; `show_archived: true` finds it) → `restore` [D:v2DeleteContact], [D:v2RestoreContact] → report id.
- `bulk_create`: `contacts` (array of create payloads) [D:v2BulkCreateContacts]; duplicate refusal n.d. → search each first.
- Search fields: id, name_1, name_2, nr, address, mail, mail_second, postcode, city, country_id, contact_group_ids, contact_type_id, updated_at, user_id, phone_fixed, phone_mobile, fax · `order_by` id, nr, name_1, updated_at [D:v2SearchContact].

## Relations, groups, sectors, additional addresses
- Relations: `contact_id` + `contact_sub_id` required, `description` · semantics n.d. → create only with both contacts user-named · search contact_id, contact_sub_id, updated_at · delete permanent [D:v2CreateContactRelation].
- Groups: `name` required [D:v2CreateContactGroup].
- Sectors (`contact_branch`): list + search on `name` only [D:v2ListContactSectors].
- Additional addresses (need `contact_id`): `name`, `name_addition`, structured street fields, `postcode`, `city`, `country_id`, `subject`, `description` · delete permanent [D:v2CreateAdditionalAddress].

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

## Gotchas
1. Create only after a search without match (name, `nr`, email).

---
Sources: https://docs.bexio.com/ (OpenAPI 3.0.2; ops cited above; full list `reference.md`; §Changelog), fetched 2026-09-24.
