---
name: bexio-accounting
description: 'Use when a Bexio request is about the ledger itself: manual postings not tied to a document (Buchung erfassen, manuelle Buchung, Sammelbuchung), accruals (Abgrenzung, transitorische), reclassifications (Umbuchung), reversing entries (Storno-/Gegenbuchung), salary postings as manual entries (Lohnbuchung), chart of accounts (Kontenplan), journal and account movements (Journal, Kontoauszug, Kontoblatt; balances: movements only), VAT rates and tax codes (MWST-Satz, Steuercode), currencies and exchange rates (Währung, Kurs, Wechselkurs, Devisenkurs, Tageskurs), business years (Geschäftsjahr), calendar years, VAT periods (MWST-Periode), month-end or year-end close, VAT return (Monatsabschluss, Jahresabschluss, Abschluss, MWST-Abrechnung), a receipt on a manual entry (Beleg zur Buchung). Load the core skill bexio first.'
---

# Bexio accounting — postings, accounts, taxes, currencies, years, VAT periods, journal

Core `bexio` first (router, gate, flags). All 35 ops: `reference.md`.

## Use / not here
- Month-end postings, accruals, reclassifications, corrections (reversing entries) · account movements per period · business year / VAT period status · taxes, currencies · receipt on a manual entry · period-close check.
- Not here: booking a supplier bill → `bexio-purchase` · issuing an invoice / customer payment → `bexio-sales` · payment orders, bank reconciliation list → `bexio-banking`.

## Tools
| Tool | Actions | Gated |
|---|---|---|
| `bexio_accounting` (`resource`: accounts, account_groups, calendar_years, business_years, vat_periods, taxes, journal) | list, search, get, create, delete | create (calendar_years only), delete (taxes only) |
| `bexio_currencies` | list, get, create, update, delete, list_codes, list_exchange_rates | delete |
| `bexio_manual_entries` | list, create, update, delete, next_reference_number, list_files, get_file, add_file, delete_file | create, update, delete, delete_file |
- Resource × action pairs: accounts list + search · account_groups list · calendar_years list + search + get + create · business_years list + get · vat_periods list + get · taxes list + get + delete · journal list.
- Scope `accounting` = manual entries + journal, read + write in one; other ops here declare no scope (user rights decide) [D§Authentication/API-Scopes].

## Chart of accounts (read-only via API)
- `resource: accounts` → `id`, `uuid`, `account_no` (string), `name`, `account_type` (1 earnings, 2 expenditures, 3 assets, 4 liabilities, 5 closing), `tax_id`, `is_active` (inactive = no new bookings), `is_locked` [D:v2ListAccounts].
- Search fields `account_no`, `fibu_account_group_id`, `name`, `account_type` [D:v2SearchAccounts].
- No account create / update / delete, no balance endpoint.
- Postings: integer `id` · journal filter: `uuid`.

## Manual entries (`bexio_manual_entries`)
| `type` | Shape [D:CreateManualEntry] |
|---|---|
| `manual_single_entry` | one line: debit account, credit account, amount |
| `manual_compound_entry` | one side one account, other side split over several |
| `manual_group_entry` | several independent lines, one `reference_nr` |
- Create required: `type`, `date`, `entries[]`. Optional `reference_nr` (≤80; `next_reference_number` suggests one).
- Line: `debit_account_id`, `credit_account_id`, `amount`, `description` (≤255), `tax_id`, `tax_account_id` ("the id of the debit account or credit account"), `currency_id`, `currency_factor` (1 when base currency).
- Amounts booked gross incl. VAT (UI help: "Gebuchte Beträge werden immer inklusive MWST (brutto) erfasst" [H:000001672]; API text silent) → "gross" in the preview.
- Response: `created_by_user_id`, `is_locked`, `locked_info`.
- Update (PUT): `type`, `date`, `entries` required; `id` + `entries[].id` identify entry + lines [D:UpdateManualEntry]. Omitted line: n.d. → always send ALL lines with ids from a fresh read.
- `is_locked=true` → not editable; `locked_info` ∈ `closed_business_year`, `closed_tax_period`, `is_generated`, `Banking_transaction`, `locked_business_year` [D:ListManualEntries].
- Delete: permanent, removes file links, NO reversal booking [D:DeleteManualEntry], [H:000001672]. Period already reported → propose a reversing entry.
- List: only `limit` / `offset` (no date, account, reference filter) → journal for period slices.
- Files: `add_file` `content_base64` + `file_name` (max 12 MB; PNG, JPG, JPEG, GIF, DOC(X), XLS(X), PPT(X), PDF). Line level (`entry_id`) for single + group, entry level for compound (no `entry_id`). `delete_file` = unlink only [D:UploadManualEntryFile], [D:DeleteManualEntryFile].

## Build a posting
1. Accounts by `account_no` `=`, active (`is_active`, not `is_locked`).
2. Taxes `list` with `date` (active that day).
3. `next_reference_number` → `reference_nr`.
4. Period, VAT period, duplicate, amount, FX → connector dry run (core §3.5), not skill reads.

## Years and VAT periods
| Resource | Status / fields | Writes |
|---|---|---|
| business_years | `status` `open` (bookings allowed), `locked` (no new bookings, no year-end closing), `closed` (no new bookings, with year-end closing), `closed_at` [D:ListBusinessYears] | none; lock / close / reopen in Bexio UI [H:000001915] |
| vat_periods | `type` quarter / semester / annual; `status` `open`, `closed`, `closed_with_message` [D:ListVatPeriods] | none; reopening needs Bexio support [H:000002234] |
| calendar_years | `is_vat_subject`, `vat_accounting_method` (`effective`, `net_tax`), `vat_accounting_type` (`agreed`, `collected`) [D:ListCalendarYears] | `create` (gated) |
- Calendar year `create`: `year` (above 2016, up to 10 years ahead); future year → every year in between created; only `year` → previous year's settings copied [D:CreateCalendarYear].
- Closed / locked year: purchase bookings refused by the API [D:ApiBillBookings_PUT]; manual entries: API rule n.d. → connector flag, never assume refusal.
- Closed VAT period: API refusal n.d. · UI help: VAT bookings dated into it → reopened VAT form ("ins neu geöffnete MWST-Formular") [H:000002234].

## Taxes and currencies
- Taxes `list` filters `scope` (active / inactive), `date`, `types` (`sales_tax`, `pre_tax`). Use `display_name`, not `name`; `code` (e.g. UN77), `digit` (VAT form), `value` (%). No create / update. Delete permanent; 409 when used or digit 000 [D:ListTaxes], [D:DeleteTax].
- Currencies: `create` needs `name` (ISO 4217) + `round_factor`; `update` only `round_factor`; rates via `embed: exchange_rate` + `date`, `list_exchange_rates`; `list_codes` [D:CreateCurrency], [D:ListCurrencies].

## Journal (`resource: journal`)
- `list` `from`, `to`, `account_uuid`, `limit` / `offset` → `date`, `debit_account_id`, `credit_account_id`, `description`, `amount`, currency fields, `ref_class` (e.g. `KbInvoice`) [D:ListJournalEntries].
- Sum of lines = movement in the period, NOT a balance → say so.

## Gate rows (core §3.2: dry run → one preview → one yes → call with the dry run's `acknowledge_flags`)
| Row | Class | Preview (`pre_image` + `would_send`) | Skill pre-check |
|---|---|---|---|
| `bexio_manual_entries.create` | posting | type; date; `reference_nr`; each line: debit no + name, credit no + name, amount (gross), currency + factor, tax code / rate + side, text; compound: total per side; files to attach | – |
| `bexio_manual_entries.update` | posting | entry id, `is_locked`, before → after for EVERY line (all sent), date moving across periods | `pre_image` `is_locked` → ⚑ Bexio refuses |
| `bexio_manual_entries.delete` | delete | entry id, `reference_nr`, date, all lines + amounts; "permanent, no reversal, file links removed"; reversing entry offered as alternative | `vat_periods` `list` → entry date in a period not `open` → ⚑ period already reported |
| `bexio_manual_entries.delete_file` | delete | entry id (+ line id), file id + name; "unlinks only" | – |
| `bexio_accounting.create` (calendar_years) | posting | every year created (incl. in between), VAT subject, method, type, default taxes | – |
| `bexio_accounting.delete` (taxes) | delete | tax id, code, display name, digit, rate, active; "permanent; 409 if in use" | – |
| `bexio_currencies.delete` | delete | currency id + ISO code; "permanent" | – |

## Month-end workflows
1. Accrual / reclassification: build (above) → accrual + day-1 reversal as one numbered batch (core §3.2) → report ids + references.
2. Correction of a posted entry: default = reversing entry (debit / credit swapped, same amount, text names the original reference) + correct entry, one batch. User asks for `update` / `delete` → that gate row.
3. Receipt: `add_file` on the created entry.
4. Period-close check: business years + VAT periods status; open payment orders (`bexio_banking_payments.list` `filter_by: "status:open"`); open draft bills (`bexio_bills.list` `filters.status: DRAFTS`). Closing = Bexio UI only.

## Gotchas
1. Manual-entry update: send all lines (omitted = n.d.); delete: no reversal.
2. Accounts: integer `id` for postings, `uuid` for the journal filter.
3. No balance, P&L or VAT report endpoint.
4. `accounting` scope: no read-only variant.

---
Sources: https://docs.bexio.com/ (OpenAPI 3.0.2; ops cited above; full list `reference.md`) · help.bexio.com 000001672, 000001915, 000002083, 000002234, fetched 2026-09-24.
