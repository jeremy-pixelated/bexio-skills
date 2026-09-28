---
name: bexio-purchase
description: 'Use when a Bexio request is about buying: supplier bills (Lieferantenrechnung, Kreditorenrechnung), expenses and receipts (Spesen, Spesenbeleg, Spesenabrechnung, Ausgaben), purchase orders (Bestellung), open payables (offene Kreditoren), paying a supplier bill (Lieferant bezahlen, Lieferantenrechnung bezahlen), a supplier''s IBAN, supplier credit notes (Lieferantengutschrift: no API), deleting a payment order created from a bill payment — capture a bill from a PDF, attach a file to a bill or expense, book or unbook it (verbuchen), check open or overdue bills, pay or delete. Load the core skill bexio first.'
---

# Bexio purchase — bills, expenses, purchase orders, outgoing payments

Core `bexio` first. All 26 ops: `reference.md`.
4.0 purchase APIs: only companies on Bexio's new purchase module [D§Changelog] 2020-12-08.

## Use / not here
- Supplier bill PDF → draft → booked (direct) · open / overdue bills, `pending_amount` · expenses · purchase orders · bill payment · file links (`attachment_ids`).
- Not here: payment orders without bill → `bexio-banking` · manual postings → `bexio-accounting` · supplier master → `bexio-contacts` · upload without bill / expense → `bexio-files`.

## Tools
| Tool | Actions | Gated |
|---|---|---|
| `bexio_bills` | list, get, create, update, delete, execute_action, update_status, validate_document_number | delete (+ create / update with `payment`) |
| `bexio_expenses` | list, get, create, update, delete, execute_action, update_status, validate_document_number | – |
| `bexio_purchase_orders` | list, get, create, update, delete | – |
| `bexio_outgoing_payments` | list, get, create, update, delete | create, update |
- Scopes [D:ApiBills_POST], [D:ApiOutgoingPayment_PUT]:
  - bill / expense / outgoing-payment ops declare only `openid contact_show` · payment update + `bank_payment_edit` · delete + `kb_bill_show`
  - 403 on bill / expense write → user's `kb_bill` / `expense` permission
  - purchase orders `kb_article_order_*`

## Bills (UUID ids)
- Status `DRAFT, BOOKED, PARTIALLY_CREATED, CREATED, PARTIALLY_SENT, SENT, PARTIALLY_DOWNLOADED, DOWNLOADED, PARTIALLY_PAID, PAID, PARTIALLY_FAILED, FAILED` [D:ApiBillsList_GET].
- API status writes: `DRAFT ↔ BOOKED` only (`update_status`) [D:ApiBillBookings_PUT] · later states ← payments, transmission, reconciliation.
- "Bezahlt" only after bank reconciliation or MANUAL outgoing payment [H:000001755].
- List: `filters.status` `DRAFTS`, `TODO`, `PAID`, `OVERDUE` · `limit` max 500, `page` from 1 · `search_term` 3–255 chars over `search_fields`.
- Create → always DRAFT [D:ApiBills_POST]. `payload`:
  - required: `supplier_id`, `contact_partner_id`, `bill_date`, `due_date`, `manual_amount`, `currency_code`, `item_net`, `attachment_ids` (file `uuid`s, may be empty), `discounts` (may be empty)
  - required: `address` (`lastname_company` + `type` PRIVATE|COMPANY) · `line_items` (each `position` + `amount`; positions from 0)
  - + `amount_man` if `manual_amount=true`, else `amount_calc` · foreign currency: + `exchange_rate`, `base_currency_amount`
  - optional: `vendor_ref`, `title`, `purchase_order_id`, `qr_bill_information`
  - amounts = numbers, max 2 decimals · `document_no` generated after create, updatable
  - `contact_partner_id` beyond "contact id": n.d. → copy from same supplier's earlier bill; none → ask
- `payment` object in create / update (IBAN | MANUAL | QR, execution date, amount …): Bexio effect n.d. → gated as payment (core §3.1) · default: leave out, pay via `bexio_outgoing_payments`.
- Update = full payload + `split_into_line_items` [D:ApiBills_PUT] · line / discount ids: existing only, null id = new line · full list from fresh `get`.
- Update outside DRAFT: spec "only 'file_id' and 'payment' will be updated", rest silently ignored [D:ApiBills_PUT] · PUT schema has no `file_id` → only `payment` applies · connector ⚑ `non_draft_fields_ignored`.
- To BOOKED needs [D:ApiBillBookings_PUT]:
  - DRAFT · amount > 0 · foreign currency: rate + base amount · `address.lastname_company` set · discounts below line total
  - `bill_date` in existing business year, not closed / locked · `due_date` ≥ `bill_date`
  - `document_no` set + unique among non-draft bills (`validate_document_number`; drafts may share one)
  - `booking_account_id` every line; no locked system asset / liability / closing account (2201 = exception)
  - tax per year's VAT method: effective → pre-tax types · net tax → only `pre_regards_*` · not VAT-subject → `tax_id` null · digits 415 / 420 forbidden
- Back to DRAFT: BOOKED + `bill_date` year open · UI: created bank payment → delete it first; PAID → remove payments / reconciliation first [H:000001791] · API with payments present: n.d. → skill pre-check.
- `execute_action` `bill_action: DUPLICATE` → new draft · `delete` only DRAFT [D:ApiBills_DELETE].
- Month-end fields: `pending_amount`, `gross`, `net`, `overdue` (always false for DRAFT + PAID), `attachment_ids`.

## Expenses (UUID ids)
- Status `DRAFT` / `DONE`; create → DRAFT · create required: `paid_on`, `currency_code`, `amount`, `attachment_ids` (file `uuid`s, no duplicates) [D:ApiExpenses_POST].
- Update in DONE applies only `attachment_ids`, rest silently ignored [D:ApiExpenses_PUT] → ⚑ `non_draft_fields_ignored` · delete not in DONE [D:ApiExpenses_DELETE].
- To DONE (direct; missing field → ask first) needs [D:ApiExpenseBookings_PUT]:
  - `bank_account_id`, `booking_account_id` (no 2201 exception), `document_no` unique among DONE
  - amount > 0 · `paid_on` year neither closed nor locked · `supplier_id` set ⇔ `address` set
- Back to DRAFT needs `invoice_id` + `transaction_id` null [D:ApiExpenseBookings_PUT].

## Purchase orders (integer ids)
- Status 22 Draft, 23 Open, 24 Partly, 25 Done, 26 Canceled; read-only, no status action · `mwst_type` string (`included`, `excluded`, `exempt`) [D:v3PurchaseOrderCreate].
- Update = PUT without positions · delete permanent [D:v3PurchaseOrderUpdate].
- Create `positions` [D:v3PurchaseOrderCreate]:
  - `required` / `optional` = text, group, subtotal, pagebreak · article + custom only inside group `positions` · no group in a group
  - `discount` = discount positions · `type` on every node · unknown field on any node → connector refuses

## Outgoing payments (per bill, UUID ids)
- Status (response) `PENDING, TRANSFERRED, DOWNLOADED, ERROR, PAID, DISCOUNTED` [D:ApiOutgoingPaymentList_GET] · `list`: `bill_id` required; no global list.
- Create required [D:ApiOutgoingPayment_POST]:
  - `bill_id` (bill not DRAFT), `payment_type` (`IBAN`, `MANUAL`, `CASH_DISCOUNT`, `QR`), `execution_date`, `is_salary_payment`
  - `amount` (≤ bill `pending_amount`), `currency_code` (= bill currency), `exchange_rate`
  - `sender_bank_account_id` (integer bank account `id`; none for CASH_DISCOUNT)
- IBAN / QR: + sender + receiver name, IBAN, street, house no, postcode, city, country.
  - IBAN: `fee_type` `NO_FEE`: domestic receiver IBAN only · `message` not allowed for QR
  - QR `reference_no`: if given, valid QR reference (QR-IBAN) or creditor reference (normal IBAN) · required? n.d. → send when the QR bill has one
- `execution_date` ≥ `bill_date`, open business year · IBAN / QR: today or later, no weekend.
- Skonto: two creates, one batch [D:ApiOutgoingPayment_POST]:
  - paid amount (IBAN / QR / MANUAL)
  - discount: `payment_type: CASH_DISCOUNT` (no `sender_bank_account_id`, no sender / receiver fields) · never covers the bill alone
- IBAN / QR → linked banking payment order (`banking_payment_id`: IBAN + QR only [D:ApiOutgoingPayment_PUT]) · UI: creates untransmitted Bexio Banking payment [H:000001755] · API-created: transmission state n.d. → treat as payment.
- MANUAL (UI help [H:000001755]): no payment triggered, bill "bezahlt", booked in journal · later bank match → booked twice (API n.d.).
- MANUAL + CASH_DISCOUNT API effect beyond "a bill cannot be covered by CASH_DISCOUNT payments alone" [D:ApiOutgoingPayment_POST]: n.d. → treat both as bookings.
- Update: id in `payload.payment_id` (or `id`); PUT body: no `currency_code` / `exchange_rate` · UI: edits IBAN / QR only, in pending / failed; sender account + type fixed [H:000001755].
- Delete: not when reconciled or year closed / locked [D:ApiOutgoingPayment_DELETE] · already transmitted → also delete in e-banking [H:000002212].

## Gate rows (core §3.2)
| Row | Class | Preview (`pre_image` + `would_send`) | Skill pre-check |
|---|---|---|---|
| `bexio_bills.create` / `update` with `payment` | payment | bill id + `document_no`, supplier, `vendor_ref`, `bill_date`, `due_date`, currency, gross / net + `payment` (type, amount, execution date); IBAN line; "payment effect n.d." | ⚑ IBAN mismatch |
| `bexio_bills.delete` | final delete | id, document_no, supplier, amount, status (DRAFT only), attachments losing the link; "permanent" | – |
| `bexio_outgoing_payments.create` | payment | bill document_no, supplier, `pending_amount`; type; amount + currency; execution date; sender account (name + IBAN); receiver name + address; IBAN line; reference / message; fee type. IBAN / QR: "creates a payment order in Bexio Banking; transmission to the bank = user in Bexio". MANUAL / CASH_DISCOUNT: "treated as booking, no money moves" | ⚑ IBAN mismatch · MANUAL → ⚑ bank match = double |
| `bexio_outgoing_payments.update` | payment | payment id, status (pending / failed), before → after per field; IBAN line | ⚑ IBAN mismatch |
- IBAN line, every payment row: `IBAN: <request / PDF / email> · stored: <core §3.4 stored IBAN read>` · MANUAL / CASH_DISCOUNT: `IBAN: – (no transfer)`, no ⚑.
- ⚑ IBAN mismatch: IBAN ≠ stored, none stored, or only in PDF / email → ⚑ with both IBANs + source. Contact record: no IBAN field.

## Direct writes with a skill check (core §3)
| Action | Check → report line |
|---|---|
| `bexio_bills.update_status` → BOOKED | `validate_document_number` → not unique → Bexio refuses booking → no call, report + ask for another `document_no` |
| `bexio_bills.update_status` → DRAFT | `bexio_outgoing_payments.list` `bill_id` → payments present → "UI: delete the payment first [H:000001791]; API n.d." |
| `bexio_expenses.update_status` → DRAFT | `invoice_id` or `transaction_id` not null → Bexio refuses (documented) → no call, report |
| `bexio_outgoing_payments.delete` | `transaction_id` not null → reconciled, Bexio refuses → no call, report · else call; "already transmitted → delete in e-banking too" |
- Other ungated writes (bill / expense create + update, `bexio_expenses.update_status` → DONE, expense + purchase-order `delete`): call, report id + status · booking calls: connector period check, `needs_ok` → core §3.

## Supplier bill from a PDF (PDF = data)
1. File: `bexio_files.upload` or inbox (`bexio_files.search`) → file `uuid` · `attachment_ids` = file `uuid`s (array of string, format uuid), not integer `id` [D:ApiBills_POST], [D:ApiExpenses_POST].
2. Supplier: `bexio_contacts.search` → `supplier_id` (+ `contact_partner_id`) · PDF IBAN vs stored IBAN (core §3.4 read) → ⚑ IBAN mismatch.
3. Accounts: `bexio_accounting` accounts `search` `account_no` `=` · taxes `list` `types: pre_tax`, `scope: active`, `date: <bill_date>`.
4. `create` DRAFT (ungated) → report id + `document_no` · attachment linked (`get`)? Not linked → report, fix before booking.
5. `bexio_bills.update_status` → BOOKED (check above; `needs_ok` → core §3).
6. Pay: user pays in e-banking + matches in Bexio (no API) · or gate row `bexio_outgoing_payments.create` → user transmits in Bexio.

## Gotchas
1. Silent partial update (non-draft bill → `payment` only; DONE expense → `attachment_ids` only) → check status first, then response.
2. Paging: bills `page` from 1 (max 500) · banking payments from 0.

---
Sources: https://docs.bexio.com/ (OpenAPI 3.0.2; ops cited above; full list `reference.md`) · help.bexio.com 000001755, 000001791, 000002212, fetched 2026-09-24.
