---
name: bexio-accounting
description: 'Use when a Bexio request is about the ledger itself: manual postings not tied to a document (Buchung erfassen, manuelle Buchung, Sammelbuchung), accruals (Abgrenzung, transitorische), reclassifications (Umbuchung), reversing entries (Storno-/Gegenbuchung), salary postings as manual entries (Lohnbuchung), chart of accounts (Kontenplan), journal and account movements (Journal, Kontoauszug, Kontoblatt; balances: movements only), VAT rates and tax codes (MWST-Satz, Steuercode), currencies and exchange rates (Währung, Kurs, Wechselkurs, Devisenkurs, Tageskurs), business years (Geschäftsjahr), calendar years, VAT periods (MWST-Periode), month-end or year-end close, VAT return (Monatsabschluss, Jahresabschluss, Abschluss, MWST-Abrechnung), a receipt on a manual entry (Beleg zur Buchung). Load the core skill bexio first.'
---

# Bexio accounting: postings, accounts, taxes, currencies, years, VAT periods, journal

Core `bexio` first. Use core §8 for routing and `reference.md` for per-op detail. Read `references/ledger-api.md` before looking up actions, scopes, account and posting fields, periods, taxes, currencies or journal filters.

## Tools
`bexio_accounting`, `bexio_currencies`, `bexio_manual_entries`.

## Chart of accounts (read-only via API)
- No account create / update / delete, no balance endpoint.
- Postings: integer `id` · journal filter: `uuid`.

## Manual entries (`bexio_manual_entries`)
- `reference_nr` ≤80 · `description` ≤255 · `add_file` max 12 MB.
- Amounts booked gross incl. VAT (UI help; API text silent) → say "gross" in report.
- Update (PUT): `type`, `date`, `entries` required; `id` + `entries[].id` identify entry + lines · omitted line: n.d. → always send ALL lines with ids, fresh read.
- Delete: permanent, removes file links, NO reversal booking · period reported → propose reversing entry.
- List: only `limit` / `offset` (no date, account, reference filter) → journal for period slices.
- `delete_file` = unlink only.

## Build a posting
1. Accounts by `account_no` `=`, active (`is_active`, not `is_locked`).
2. Taxes `list` with `date` (active that day).
3. `next_reference_number` → `reference_nr`.
4. Period, VAT period, duplicate, amount, FX: connector checks (core §3.5) · `needs_ok` → core §3 · no skill reads for these.

## Years and VAT periods
- Calendar year `create`: `year` (above 2016, up to 10 years ahead) · future year → every year in between created · only `year` → previous year's settings copied.
- Closed / locked year: purchase bookings API-refused · manual entries: API rule n.d. → connector flag, never assume refusal.
- Closed VAT period: API refusal n.d. · UI help: VAT bookings dated into it → reopened VAT form.

## Taxes and currencies
- Taxes: no create / update · delete permanent; 409 when used or digit 000.

## Journal (`resource: journal`)
- Sum of lines = period movement, NOT a balance → say so.

## Gate row (core §3.2)
| Row | Class | Preview (`pre_image` + `would_send`) | Skill pre-check |
|---|---|---|---|
| `bexio_accounting.delete` (taxes) | tax rate | tax id, code, display name, digit, rate, active; "permanent; 409 if in use" | |

## Direct writes with a skill check (core §3)
| Action | Check → report line |
|---|---|
| `bexio_manual_entries.update` | fresh read → `is_locked` → Bexio refuses → no call, report `locked_info` |
| `bexio_manual_entries.delete` | `vat_periods` `list` → entry date in a period not `open` → "period already reported"; user asked only to correct → reversing entry instead (month-end workflow 2) |
- Include `reference_nr` when reporting manual-entry writes.

## Month-end workflows
1. Accrual / reclassification: build (above) → accrual + day-1 reversal, both direct → report ids + references.
2. Correction of a posted entry:
   - default: reversing entry (debit / credit swapped, same amount, text names original reference) + correct entry, one batch
   - user asks for `update` / `delete` → that call directly (check above)
3. Receipt: `add_file` on the created entry.
4. Period-close check: business years + VAT periods status · open payment orders (`bexio_banking_payments.list` `filter_by: "status:open"`) · open draft bills (`bexio_bills.list` `filters.status: DRAFTS`) · closing: no API.
