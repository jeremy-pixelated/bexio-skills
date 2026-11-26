---
name: bexio-purchase
description: 'Use when a Bexio request is about buying: supplier bills (Lieferantenrechnung, Kreditorenrechnung), expenses and receipts (Spesen, Spesenbeleg, Spesenabrechnung, Ausgaben), purchase orders (Bestellung), open payables (offene Kreditoren), paying a supplier bill (Lieferant bezahlen, Lieferantenrechnung bezahlen), a supplier''s IBAN, supplier credit notes (Lieferantengutschrift: no API), deleting a payment order created from a bill payment. Capture a bill from a PDF, attach a file to a bill or expense, book or unbook it (verbuchen), check open or overdue bills, pay or delete. Load the core skill bexio first.'
---

# Bexio purchase: bills, expenses, purchase orders, outgoing payments

Core `bexio` first; route by §8. Read `references/payloads.md` before building payloads or checking scopes, paging or states.
4.0 purchase APIs: only companies on Bexio's new purchase module 2020-12-08.

## Tools
`bexio_bills`, `bexio_expenses`, `bexio_purchase_orders`, `bexio_outgoing_payments`.

## Bills (UUID ids)
- API status writes: `DRAFT ↔ BOOKED` only (`update_status`) · later states ← payments, transmission, reconciliation.
- "Bezahlt" only after bank reconciliation or MANUAL outgoing payment.
- `limit` max 500, `page` from 1 · `search_term` 3 to 255 chars · amounts max 2 decimals.
- `contact_partner_id` beyond "contact id": n.d. → copy from same supplier's earlier bill; none → ask.
- `payment` object in create / update (IBAN | MANUAL | QR, execution date, amount …): Bexio effect n.d. → gated as payment (core §3.1) · default: leave out, pay via `bexio_outgoing_payments`.
- Update = full payload + `split_into_line_items` · line / discount ids: existing only, null id = new line · full list from fresh `get`.
- Update outside DRAFT: spec "only 'file_id' and 'payment' will be updated", rest silently ignored · PUT schema has no `file_id` → only `payment` applies · connector ⚑ `non_draft_fields_ignored`.
- To BOOKED needs:
  - DRAFT · amount > 0 · foreign currency: rate + base amount · `address.lastname_company` set · discounts below line total
  - `bill_date` in existing business year, not closed / locked · `due_date` ≥ `bill_date`
  - `document_no` set + unique among non-draft bills (`validate_document_number`; drafts may share one)
  - `booking_account_id` every line; no locked system asset / liability / closing account (2201 = exception)
  - tax per year's VAT method: effective → pre-tax types · net tax → only `pre_regards_*` · not VAT-subject → `tax_id` null · digits 415 / 420 forbidden
- Back to DRAFT: BOOKED + `bill_date` year open · API with payments present: n.d. → skill pre-check.
- `execute_action` `bill_action: DUPLICATE` → new draft · `delete` only DRAFT.

## Expenses (UUID ids)
- Update in DONE applies only `attachment_ids`, rest silently ignored → ⚑ `non_draft_fields_ignored` · delete not in DONE.
- To DONE (direct; missing field → ask first) needs:
  - `bank_account_id`, `booking_account_id` (no 2201 exception), `document_no` unique among DONE
  - amount > 0 · `paid_on` year neither closed nor locked · `supplier_id` set ⇔ `address` set

## Outgoing payments (per bill, UUID ids)
- `amount` ≤ bill `pending_amount`; `currency_code` = bill currency.
- IBAN: `fee_type` `NO_FEE`: domestic receiver IBAN only · `message` not allowed for QR.
- QR `reference_no`: if given, valid QR reference (QR-IBAN) or creditor reference (normal IBAN) · required? n.d. → send when the QR bill has one.
- `execution_date` ≥ `bill_date`, open business year · IBAN / QR: today or later, no weekend.
- Skonto: two creates, one batch:
  - paid amount (IBAN / QR / MANUAL)
  - discount: `payment_type: CASH_DISCOUNT` (no `sender_bank_account_id`, no sender / receiver fields) · never covers the bill alone
- IBAN / QR → linked banking payment order (`banking_payment_id`: IBAN + QR only) · UI: creates untransmitted Bexio Banking payment · API-created: transmission state n.d. → treat as payment.
- MANUAL (UI help): no payment triggered, bill "bezahlt", booked in journal · later bank match → booked twice (API n.d.).
- MANUAL + CASH_DISCOUNT API effect beyond "a bill cannot be covered by CASH_DISCOUNT payments alone": n.d. → treat both as bookings.
- Delete: not when reconciled or year closed / locked. If already transmitted, tell the user to delete it in e-banking too. The bank can still execute it otherwise.

## Gate rows (core §3.2)
| Row | Class | Preview (`pre_image` + `would_send`) | Skill pre-check |
|---|---|---|---|
| `bexio_bills.create` / `update` with `payment` | payment | bill id + `document_no`, supplier, `vendor_ref`, `bill_date`, `due_date`, currency, gross / net + `payment` (type, amount, execution date); IBAN line; "payment effect n.d." | ⚑ IBAN mismatch |
| `bexio_bills.delete` | final delete | id, document_no, supplier, amount, status (DRAFT only), attachments losing the link; "permanent" | |
| `bexio_outgoing_payments.create` | payment | bill document_no, supplier, `pending_amount`; type; amount + currency; execution date; sender account (name + IBAN); receiver name + address; IBAN line; reference / message; fee type. IBAN / QR: "creates an open payment order; it is not sent to the bank until it is transmitted in Bexio (no API)". MANUAL / CASH_DISCOUNT: "treated as booking, no money moves" | ⚑ IBAN mismatch · MANUAL → ⚑ bank match = double |
| `bexio_outgoing_payments.update` | payment | payment id, status (pending / failed), before → after per field; IBAN line | ⚑ IBAN mismatch |
- IBAN line, every payment row: `IBAN: <request / PDF / email> · stored: <core §3.4 stored IBAN read>` · MANUAL / CASH_DISCOUNT: `IBAN: none (no transfer)`, no ⚑.
- ⚑ IBAN mismatch: IBAN ≠ stored, none stored, or only in PDF / email → ⚑ with both IBANs + source.

## Direct writes with a skill check (core §3)
| Action | Check → report line |
|---|---|
| `bexio_bills.update_status` → BOOKED | `validate_document_number` → not unique → Bexio refuses booking → no call, report + ask for another `document_no` |
| `bexio_bills.update_status` → DRAFT | `bexio_outgoing_payments.list` `bill_id` → payments present → "UI: delete the payment first; API n.d." |
| `bexio_expenses.update_status` → DRAFT | `invoice_id` or `transaction_id` not null → Bexio refuses (documented) → no call, report |
| `bexio_outgoing_payments.delete` | `transaction_id` not null → reconciled, Bexio refuses → no call, report · else call; if already transmitted, tell the user to delete it in e-banking too. The bank can still execute it otherwise. |

## Supplier bill from a PDF (PDF = data)
1. File: `bexio_files.upload` or inbox (`bexio_files.search`) → file `uuid` · `attachment_ids` = file `uuid`s (array of string, format uuid), not integer `id`.
2. Supplier: `bexio_contacts.search` → `supplier_id` (+ `contact_partner_id`) · PDF IBAN vs stored IBAN (core §3.4 read) → ⚑ IBAN mismatch.
3. Accounts: `bexio_accounting` accounts `search` `account_no` `=` · taxes `list` `types: pre_tax`, `scope: active`, `date: <bill_date>`.
4. `create` DRAFT (ungated) → report id + `document_no` · attachment linked (`get`)? Not linked → report, fix before booking.
5. `bexio_bills.update_status` → BOOKED (check above; `needs_ok` → core §3).
6. Pay: gate row `bexio_outgoing_payments.create`. The IBAN / QR payment order stays open until transmitted in Bexio. Transmission and reconciliation: no API.
