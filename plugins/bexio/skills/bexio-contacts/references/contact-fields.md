# Contact API lookup

## Tools
- `bexio_contacts`: list, search, get, create, update, delete, bulk_create, restore.
- `bexio_contact_relations`, `bexio_contact_groups`, `bexio_additional_addresses`: list, search, get, create, update, delete.
- `bexio_contact_sectors`: list, search (read-only).
- Scopes: contacts, relations, additional addresses `contact_show` / `contact_edit` · groups + sectors: none requestable (user rights).

## Contacts (`/2.0/contact`, integer ids)
- Create required: `contact_type_id` (1 company, 2 person), `name_1` (company / person's last name), `user_id` (`bexio_users.me`), `owner_id`.
- Optional: `nr` (numeric; null = auto) · `name_2` (company addition / first name) · `street_name`, `house_number`, `address_addition`, `postcode`, `city`, `country_id` · single-line `address`: deprecated in requests since 2025-12-09, still in responses · `mail`, `phone_fixed`, `phone_mobile`, `language_id`, `remarks`.
- `bulk_create`: `contacts` (array of create payloads).
- Search fields: id, name_1, name_2, nr, address, mail, mail_second, postcode, city, country_id, contact_group_ids, contact_type_id, updated_at, user_id, phone_fixed, phone_mobile, fax · `order_by` id, nr, name_1, updated_at.

## Relations, groups, sectors, additional addresses
- Relations: `contact_id` + `contact_sub_id` required, `description` · search contact_id, contact_sub_id, updated_at.
- Groups: `name` required.
- Sectors (`contact_branch`): list + search on `name` only.
- Additional addresses (need `contact_id`): `name`, `name_addition`, structured street fields, `postcode`, `city`, `country_id`, `subject`, `description`.
