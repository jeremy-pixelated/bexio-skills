# Accounting API lookup

## Tools
- `bexio_accounting`: accounts `list` / `search`; account_groups `list`; journal `list`; calendar_years `list` / `search` / `get` / `create`; business_years and vat_periods `list` / `get`; taxes `list` / `get` / `delete`.
- `bexio_currencies`: `list`, `get`, `create`, `update`, `delete`, `list_codes`, `list_exchange_rates`.
- `bexio_manual_entries`: `list`, `create`, `update`, `delete`, `next_reference_number`, `list_files`, `get_file`, `add_file`, `delete_file`.
- Scope `accounting` = manual entries + journal, read + write in one (no read-only variant) · other ops: no scope (user rights).

## Chart of accounts (read-only via API)
- `resource: accounts`: `id`, `uuid`, `account_no` (string), `name`, `tax_id`, `is_active` (inactive = no new bookings), `is_locked`.
- `account_type`: 1 earnings, 2 expenditures, 3 assets, 4 liabilities, 5 closing.
- Search fields `account_no`, `fibu_account_group_id`, `name`, `account_type`.

## Manual entries (`bexio_manual_entries`)
| `type` | Shape |
|---|---|
| `manual_single_entry` | one line: debit account, credit account, amount |
| `manual_compound_entry` | one side one account, other side split over several |
| `manual_group_entry` | several independent lines, one `reference_nr` |
- Create required: `type`, `date`, `entries[]` · optional `reference_nr` (≤80; `next_reference_number` suggests one).
- Line: `debit_account_id`, `credit_account_id`, `amount`, `description` (≤255), `tax_id`, `tax_account_id` (= debit or credit account id), `currency_id`, `currency_factor` (1 when base currency).
- Response: `created_by_user_id`, `is_locked`, `locked_info`.
- `locked_info`: `closed_business_year`, `closed_tax_period`, `is_generated`, `Banking_transaction`, `locked_business_year`.
- `list`: `limit` / `offset`, no date, account or reference filter.
- `add_file`: `content_base64` + `file_name` · max 12 MB · PNG, JPG, JPEG, GIF, DOC(X), XLS(X), PPT(X), PDF. Line level (`entry_id`) for single + group · entry level for compound (no `entry_id`).

## Years and VAT periods
| Resource | Status / fields |
|---|---|
| business_years | `status` `open` (bookings allowed), `locked` (no new bookings, no year-end closing), `closed` (no new bookings, with year-end closing), `closed_at` |
| vat_periods | `type` quarter / semester / annual; `status` `open`, `closed`, `closed_with_message` |
| calendar_years | `is_vat_subject`, `vat_accounting_method` (`effective`, `net_tax`), `vat_accounting_type` (`agreed`, `collected`) |

## Taxes and currencies
- Taxes `list` filters: `scope` (active / inactive), `date`, `types` (`sales_tax`, `pre_tax`).
- Tax fields: `display_name` (use, not `name`), `code` (e.g. UN77), `digit` (VAT form), `value` (%).
- Currencies: `create` needs `name` (ISO 4217) + `round_factor` · `update` only `round_factor` · rates via `embed: exchange_rate` + `date`, `list_exchange_rates` · `list_codes`.

## Journal (`resource: journal`)
- `list` `from`, `to`, `account_uuid`, `limit` / `offset` → `date`, `debit_account_id`, `credit_account_id`, `description`, `amount`, currency fields, `ref_class` (e.g. `KbInvoice`).
