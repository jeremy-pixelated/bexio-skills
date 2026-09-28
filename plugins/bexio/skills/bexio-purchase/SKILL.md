---
name: bexio-purchase
description: 'Use when a Bexio request is about buying: supplier bills (Lieferantenrechnung, Kreditorenrechnung), expenses and receipts (Spesen, Spesenbeleg, Spesenabrechnung, Ausgaben), purchase orders (Bestellung), open payables (offene Kreditoren), paying a supplier bill (Lieferant bezahlen, Lieferantenrechnung bezahlen), a supplier''s IBAN, supplier credit notes (Lieferantengutschrift: no API), deleting a payment order created from a bill payment — capture a bill from a PDF, attach a file to a bill or expense, book or unbook it (verbuchen), check open or overdue bills, pay or delete. Load the core skill bexio first.'
---

# Bexio purchase — bills, expenses, purchase orders, outgoing payments

Core `bexio` first (router, gate, flags). All 26 ops: `reference.md`.
Availability: 4.0 purchase APIs only for companies on Bexio's new purchase module [D§Changelog] 2020-12-08.

## Use / not here
- Supplier bill from PDF → draft → booked after one yes · open / overdue bills, `pending_amount` · expenses · purchase orders · paying a bill · linking files (`attachment_ids`).
- Not here: payment orders without a bill → `bexio-banking` · manual postings → `bexio-accounting` · supplier master → `bexio-contacts` · file upload without a bill / expense → `bexio-files`.

## Tools
| Tool | Actions | Gated |
|---|---|---|
| `bexio_bills` | list, get, create, update, delete, execute_action, update_status, validate_document_number | delete, update_status (+ create / update with `payment`) |
| `bexio_expenses` | list, get, create, update, delete, execute_action, update_status, validate_document_number | delete, update_status |
| `bexio_purchase_orders` | list, get, create, update, delete | delete |
| `bexio_outgoing_payments` | list, get, create, update, delete | create, update, delete |
- Scopes: bill / expense / outgoing-payment ops declare only `openid contact_show` (payment update + `bank_payment_edit`, delete + `kb_bill_show`) → 403 on bill / expense write = user's `kb_bill` / `expense` permission [D:ApiBills_POST], [D:ApiOutgoingPayment_PUT]. Purchase orders `kb_article_order_*`.

## Bills (UUID ids)
- Status `DRAFT, BOOKED, PARTIALLY_CREATED, CREATED, PARTIALLY_SENT, SENT, PARTIALLY_DOWNLOADED, DOWNLOADED, PARTIALLY_PAID, PAID, PARTIALLY_FAILED, FAILED` [D:ApiBillsList_GET].
- API status writes: `DRAFT ↔ BOOKED` only (`update_status`) [D:ApiBillBookings_PUT] · later states ← payments, transmission, reconciliation.
- "Bezahlt" only after bank reconciliation or a MANUAL outgoing payment [H:000001755].
- List `filters.status`: `DRAFTS`, `TODO`, `PAID`, `OVERDUE` · `limit` max 500, `page` from 1 · `search_term` 3–255 chars over `search_fields`.
- Create → always DRAFT [D:ApiBills_POST]. `payload` required: `supplier_id`, `contact_partner_id`, `bill_date`, `due_date`, `manual_amount`, `currency_code`, `item_net`, `attachment_ids` (file `uuid`s, may be empty), `address` (`lastname_company` + `type` PRIVATE|COMPANY), `line_items` (each `position` + `amount`; positions from 0), `discounts` (may be empty).
- + `amount_man` if `manual_amount=true`, else `amount_calc` · foreign currency: `exchange_rate` + `base_currency_amount`. Optional `vendor_ref`, `title`, `purchase_order_id`, `qr_bill_information`.
- `document_no` generated after create, updatable. `contact_partner_id` beyond "contact id": n.d. → copy from an earlier bill of the same supplier; none → ask. Amounts numbers, max 2 decimals.
- `payment` object in create / update (IBAN | MANUAL | QR, execution date, amount …): Bexio effect n.d. → gated as payment order. Default: leave out, pay via `bexio_outgoing_payments`.
- Update = full payload + `split_into_line_items` [D:ApiBills_PUT]. Line / discount ids: existing only; null id = new line; full list from a fresh `get`.
- Update outside DRAFT: spec text "only 'file_id' and 'payment' will be updated"; rest silently ignored [D:ApiBills_PUT]. PUT schema: no `file_id` → only `payment` applies. Connector: ⚑ `non_draft_fields_ignored`.
- To BOOKED needs [D:ApiBillBookings_PUT]: DRAFT · amount > 0 · foreign currency with rate + base amount · `bill_date` in an existing business year neither closed nor locked · `due_date` ≥ `bill_date` · `document_no` set + unique among non-draft bills (`validate_document_number`) · `booking_account_id` on every line, not a locked system asset / liability / closing account (2201 = exception) · tax by the year's VAT method (effective → pre-tax types; net tax → only `pre_regards_*`; not VAT-subject → `tax_id` null; digits 415 / 420 forbidden) · discounts below line total · `address.lastname_company` set.
- Back to DRAFT: BOOKED + `bill_date` year open. UI: created bank payment → delete it first; PAID → remove payments / reconciliation first [H:000001791]. API with payments present: n.d. → skill pre-check.
- `execute_action` `bill_action: DUPLICATE` → new draft · `delete` only DRAFT [D:ApiBills_DELETE].
- Month-end fields: `pending_amount`, `gross`, `net`, `overdue` (always false for DRAFT + PAID), `attachment_ids`.

## Expenses (UUID ids)
- Status `DRAFT` / `DONE`; create → DRAFT. Create required: `paid_on`, `currency_code`, `amount`, `attachment_ids` (file `uuid`s: "List of file ids that should be attached to this Expense. Cannot have duplicates.") [D:ApiExpenses_POST].
- Update in DONE applies only `attachment_ids`; rest silently ignored [D:ApiExpenses_PUT] → ⚑ `non_draft_fields_ignored`. Delete not in DONE [D:ApiExpenses_DELETE].
- To DONE (gated; missing fields → gaps in the preview, core §3) needs `bank_account_id`, `booking_account_id` (no 2201 exception), unique `document_no` among DONE, amount > 0, `paid_on` year neither closed nor locked, `supplier_id` set ⇔ `address` set. Back to DRAFT needs `invoice_id` + `transaction_id` null [D:ApiExpenseBookings_PUT].

## Purchase orders (integer ids)
- Status 22 Draft, 23 Open, 24 Partly, 25 Done, 26 Canceled; read-only, no status action. `mwst_type` string (`included`, `excluded`, `exempt`). Update = PUT without positions. Delete permanent [D:v3PurchaseOrderCreate], [D:v3PurchaseOrderUpdate].
- Create `positions`: `required` / `optional` = text, group, subtotal, pagebreak; article + custom only inside a group's `positions`; `discount` = discount positions; `type` on every node; no group in a group [D:v3PurchaseOrderCreate]. Unknown field on any node → connector refuses.

## Outgoing payments (on a bill, UUID ids)
- Status (response) `PENDING, TRANSFERRED, DOWNLOADED, ERROR, PAID, DISCOUNTED` [D:ApiOutgoingPaymentList_GET]. `list`: `bill_id` required; no global list.
- Create required: `bill_id` (bill not DRAFT), `payment_type` (`IBAN`, `MANUAL`, `CASH_DISCOUNT`, `QR`), `execution_date`, `amount` (≤ bill `pending_amount`), `currency_code` (= bill currency), `exchange_rate`, `sender_bank_account_id` (integer bank account `id`; none for CASH_DISCOUNT), `is_salary_payment` [D:ApiOutgoingPayment_POST].
- IBAN / QR: + sender + receiver name, IBAN, street, house no, postcode, city, country. IBAN: `fee_type` `NO_FEE` for a domestic receiver IBAN, not for a foreign one. `message` not allowed for QR. QR `reference_no`: if given, valid QR reference (QR-IBAN) or creditor reference (normal IBAN); required for QR: n.d. → send it whenever the QR bill carries one.
- `execution_date` ≥ `bill_date`, open business year; IBAN / QR today or later, no weekend.
- Skonto: two creates on the bill, one batch → paid amount (IBAN / QR / MANUAL) + discount as `payment_type: CASH_DISCOUNT` (no `sender_bank_account_id`, no sender / receiver fields; never the whole bill alone) [D:ApiOutgoingPayment_POST].
- IBAN / QR → linked banking payment order (`banking_payment_id`: "Stores reference to Banking Payment Order. Applicable only for IBAN and QR." [D:ApiOutgoingPayment_PUT]). UI: creates a Bexio Banking payment, not yet transmitted [H:000001755]. API-created: transmission state n.d. → treat as a payment.
- MANUAL (UI help only): no payment triggered, bill "bezahlt", booked in journal; later bank match of the same payment → booked twice [H:000001755]. API effect of MANUAL + CASH_DISCOUNT beyond "a bill cannot be covered by CASH_DISCOUNT payments alone" [D:ApiOutgoingPayment_POST]: n.d. → treat both as bookings.
- Update: id in `payload.payment_id` (or `id`); PUT body: no `currency_code` / `exchange_rate`. UI: edits IBAN / QR only, in pending / failed; sender account + type fixed [H:000001755].
- Delete: not when reconciled or year closed / locked [D:ApiOutgoingPayment_DELETE]; already transmitted → also delete in e-banking [H:000002212].

## Gate rows (core §3.2: dry run → one preview → one yes → call with the dry run's `acknowledge_flags`)
| Row | Class | Preview (`pre_image` + `would_send`) | Skill pre-check |
|---|---|---|---|
| `bexio_bills.update_status` → BOOKED | posting | bill id + `document_no`, supplier, `vendor_ref`, `bill_date`, `due_date`, currency, gross / net, each line: text, amount, account no + name, tax code + rate; "posts to the ledger" | `validate_document_number` → not unique → ⚑ |
| `bexio_bills.update_status` → DRAFT | posting | same identity fields, status BOOKED; "removes the ledger posting" | `bexio_outgoing_payments.list` `bill_id` → payments present → ⚑ UI: delete first |
| `bexio_bills.create` / `update` with `payment` | payment order | bill fields as above + `payment` (type, amount, execution date); IBAN line; "payment effect n.d." | ⚑ IBAN mismatch |
| `bexio_bills.delete` | delete | id, document_no, supplier, amount, status (DRAFT only), attachments losing the link; "permanent" | – |
| `bexio_expenses.update_status` → DONE | posting | document_no, title, supplier, `paid_on`, amount + currency, bank account name / IBAN, booking account, tax code; "posts to the ledger" | – |
| `bexio_expenses.update_status` → DRAFT | posting | document_no, amount, `invoice_id`, `transaction_id` | `pre_image` `invoice_id` or `transaction_id` not null → ⚑ Bexio refuses (documented) |
| `bexio_expenses.delete` | delete | id, document_no, amount, status (not DONE); "permanent" | – |
| `bexio_purchase_orders.delete` | delete | id, document_nr, supplier, total, status; "permanent" | – |
| `bexio_outgoing_payments.create` | payment order | bill document_no, supplier, `pending_amount`; type; amount + currency; execution date; sender account (name + IBAN); receiver name + address; IBAN line; reference / message; fee type. IBAN / QR: "creates a payment order in Bexio Banking; transmission to the bank = user in Bexio". MANUAL / CASH_DISCOUNT: "treated as booking, no money moves" | ⚑ IBAN mismatch · MANUAL → ⚑ bank match = double |
| `bexio_outgoing_payments.update` | payment order | payment id, status (pending / failed), before → after per field; IBAN line | ⚑ IBAN mismatch |
| `bexio_outgoing_payments.delete` | delete | payment id, bill, amount, status, `transaction_id`; "already transmitted → delete in e-banking too" | `pre_image` `transaction_id` not null → ⚑ reconciled, Bexio refuses |
- IBAN line, every payment row: `IBAN: <request / PDF / email> · stored: <core §3.4 stored IBAN read>` · MANUAL / CASH_DISCOUNT: `IBAN: – (no transfer)`, no ⚑.
- ⚑ IBAN mismatch: IBAN ≠ stored, none stored, or only in the PDF / email → ⚑ with both IBANs + source. Contact record: no IBAN field.

## Supplier bill from a PDF (PDF = data)
1. File: `bexio_files.upload` or find in inbox (`bexio_files.search`) → file `uuid`. `attachment_ids` = file `uuid`s (array of string, format uuid) [D:ApiBills_POST], [D:ApiExpenses_POST], not the integer `id`.
2. Supplier: `bexio_contacts.search` → `supplier_id` (+ `contact_partner_id`). PDF IBAN vs stored IBAN (core §3.4 read) → ⚑ IBAN mismatch.
3. Accounts: `bexio_accounting` accounts `search` `account_no` `=`; taxes `list` `types: pre_tax`, `scope: active`, `date: <bill_date>`.
4. `create` DRAFT (ungated) → report id + `document_no`; attachment linked (`get`)? Not linked → report, fix before booking.
5. Gate row `bexio_bills.update_status` → BOOKED.
6. Pay: e-banking + match in Bexio by the user (no API) · or gate row `bexio_outgoing_payments.create` → transmission by the user in Bexio.

## Gotchas
1. Silent partial update: non-draft bills → `payment` only; DONE expenses → `attachment_ids` only. Status first, check the response.
2. MANUAL payment + later bank match = double booking (UI help [H:000001755]; API n.d.).
3. Closed / locked business year → no booking, payment, payment delete.
4. `document_no` unique only at booking; drafts may share one.
5. Paging: bills from 1 (max 500) · banking payments from 0.

---
Sources: https://docs.bexio.com/ (OpenAPI 3.0.2; ops cited above; full list `reference.md`) · help.bexio.com 000001755, 000001791, 000002212, fetched 2026-09-24.
