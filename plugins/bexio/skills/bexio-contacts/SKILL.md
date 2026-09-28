---
name: bexio-contacts
description: 'Use when a Bexio request is about the contact master: customers (Kunde, Debitor-Stamm), suppliers as contacts (Lieferant anlegen, Kreditor-Stamm), persons, addresses, contact relations, contact groups (Kontaktgruppe), sectors (Branchen) or additional addresses — find, create, update, archive/delete or restore a contact, or look up a contact_id / supplier_id (no IBAN field: a supplier''s IBAN → bexio-purchase). Load the core skill bexio first.'
---

# Bexio contacts

Customers + suppliers = one contact master. Core `bexio` first (router, gate, flags). All 28 ops: `reference.md`.

## Use / not here
- Find customer / supplier (nr, address, email, group) · resolve `contact_id` / `supplier_id` · create, update, delete (archive), restore.
- Not here: salutations, titles → `bexio-admin` · notes / tasks on a contact → `bexio-admin` · a supplier's IBAN → `bexio-purchase` (contact: no IBAN field).

## Tools
| Tool | Actions | Gated |
|---|---|---|
| `bexio_contacts` | list, search, get, create, update, delete, bulk_create, restore | delete |
| `bexio_contact_relations` | list, search, get, create, update, delete | delete |
| `bexio_contact_groups` | list, search, get, create, update, delete | delete |
| `bexio_contact_sectors` | list, search | – (read-only) |
| `bexio_additional_addresses` | list, search, get, create, update, delete | delete |
- Scopes: contacts, relations, additional addresses `contact_show` / `contact_edit`; groups + sectors: no requestable scope (user rights) [D:v2CreateContact], [D:v2CreateContactGroup].

## Contacts (`/2.0/contact`, integer ids)
- Create required: `contact_type_id` (1 company, 2 person), `name_1` (company name / person's last name), `user_id`, `owner_id` [D:v2CreateContact]. `user_id` from `bexio_users.me`.
- Optional: `nr` (null = auto; numeric), `name_2` (company addition / first name), `street_name` + `house_number` + `address_addition`, `postcode`, `city`, `country_id`, `mail`, `phone_fixed`, `phone_mobile`, `language_id`, `remarks`, `contact_group_ids` + `contact_branch_ids` as comma strings (`"1,2"`).
- Address: structured street fields · single-line `address`: deprecated in requests since 2025-12-09, still in responses [D§Changelog].
- Update = `update` with changed fields only (POST, partial).
- Delete = soft: marked deleted, findable with `show_archived: true`; `restore` → back [D:v2DeleteContact], [D:v2RestoreContact]. Still gated.
- `bulk_create`: `contacts` (array of create payloads) [D:v2BulkCreateContacts]; duplicate refusal n.d. → search each first.
- Search fields: id, name_1, name_2, nr, address, mail, mail_second, postcode, city, country_id, contact_group_ids, contact_type_id, updated_at, user_id, phone_fixed, phone_mobile, fax. `order_by`: id, nr, name_1, updated_at [D:v2SearchContact].

## Relations, groups, sectors, additional addresses
- Relations: `contact_id` + `contact_sub_id` required (links two contacts; further semantics n.d. → create only with both contacts named by the user), `description`. Search contact_id, contact_sub_id, updated_at [D:v2CreateContactRelation].
- Groups: `name` required [D:v2CreateContactGroup]. On contacts: comma string.
- Sectors (`contact_branch`): list + search on `name` only [D:v2ListContactSectors].
- Additional addresses (need `contact_id`): `name`, `name_addition`, structured street fields, `postcode`, `city`, `country_id`, `subject`, `description`. Delete permanent [D:v2CreateAdditionalAddress].

## Gate rows (core §3.2: dry run → one preview → one yes → call with the dry run's `acknowledge_flags`)
| Row | Class | Preview (`pre_image` + `would_send`) | Skill pre-check |
|---|---|---|---|
| `bexio_contacts.delete` | delete | id, `nr`, name_1 / name_2, type; "soft delete, `restore` possible" | open documents referencing it (`bexio_invoices.search` `contact_id`, `bexio_bills.list` by supplier) → ⚑ still referenced |
| `bexio_contact_relations.delete` | delete | relation id, both contacts' names; "permanent" | – |
| `bexio_contact_groups.delete` | delete | group id + name; "permanent" | contacts carrying it (`bexio_contacts.search` `contact_group_ids`) → ⚑ group in use |
| `bexio_additional_addresses.delete` | delete | contact name, address id, full address; "permanent" | – |

## Resolve the counterparty
1. `bexio_contacts.search` `nr` `=` (numbers) or `name_1` `like`.
2. Several hits → list candidates (nr, name, city) → ask which (data, not approval); never guess.
3. Integer `id` → `contact_id` (sales) / `supplier_id` (bills, expenses).

## Gotchas
1. `nr` numeric; search with `=` (`like` = substring).
2. Contact delete soft; additional-address + relation deletes permanent.
3. Groups / sectors on a contact = comma strings, not arrays.
4. Create only after a search without match (name, `nr`, email).

---
Sources: https://docs.bexio.com/ (OpenAPI 3.0.2; ops cited above; full list `reference.md`; §Changelog), fetched 2026-09-24.
