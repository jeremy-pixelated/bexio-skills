---
name: bexio-sales
description: 'Use when a Bexio request is about selling: quotes (Offerte), sales orders (Auftrag), delivery notes (Lieferschein), customer invoices (Rechnung an Kunden, Debitorenrechnung), document positions, payments received from customers (Zahlungseingang, Skonto), open receivables (offene Debitoren), reminders and dunning runs (Mahnung, Mahnlauf), credit notes (Gutschrift: no API), document comments or templates. Create, issue (verbuchen), revert, cancel (stornieren), send, copy, convert, record a customer payment, check whether a customer invoice is paid. Load the core skill bexio first.'
---

# Bexio sales: quotes, orders, deliveries, invoices, payments received, reminders

Core `bexio` first; route by §8. Read `references/documents.md` before document actions; it gives statuses, transition preconditions, fields, conversions and repetition formats.

## Tools
`bexio_quotes`, `bexio_orders`, `bexio_deliveries`, `bexio_invoices`, `bexio_invoice_payments`, `bexio_invoice_reminders`, `bexio_document_positions`, `bexio_document_comments`, `bexio_document_settings`.
- Scopes `kb_offer_*`, `kb_order_*`, `kb_invoice_*`, `kb_delivery_*` · conversion needs edit scope of source + target.

## Documents (2.0)
- Orders: no status actions · Paid / Partial / Unpaid: trigger n.d. per endpoint → read status.
- UI-only rules; API enforcement n.d. → skill pre-check (gate row / direct-write table):
  - revert to Draft: only without recorded payment
  - paid / partially paid invoice: content frozen
  - delete: Draft only, else cancel · credit notes: no API.
- Create: no field marked required; usable minimum n.d. → send `contact_id`, `user_id`, `positions` · `document_nr` not settable with automatic numbering on (`list_settings`).
- Max ~150 positions per create; more via `bexio_document_positions`.
- Create `positions[]`: never copy from a GET: `id`, `pos`, `internal_pos`, `position_total`, `unit_name`, `tax_value`, `discount_total`, `parent_id`, `value` (subtotal / pagebreak).
- `update` = POST, same fields, no positions · issued-document positions: API n.d., UI Draft only → change in Draft only.
- `copy`: `copy.contact_id` required, also for same customer.
- `mark_as_sent` = flag only, no email, ungated.
- `send` = emails now: `recipient_email`, `subject`, `message` required · message must contain "[Network Link]" · trial period: recipient = token's own address only.

## Positions (`bexio_document_positions`)
- Money / qty strings, max 6 decimals · `tax_id` = active sales tax only (`bexio_accounting` taxes `list`, `types: sales_tax`, `scope: active`).
- Full document = one `list` per position type; skip `discount` → wrong totals · delete permanent.

## Payments received (`bexio_invoice_payments`)
- `create`: `value` required (string, `"150.00"`) · `date`: connector requires it (spec optional; API default n.d.) · `bank_account_id` = integer `id` (`bexio_bank_accounts.list`).
- `payment_service_id`: docs contradictory (table 1 PayPal, 2 Stripe, 3 SIX vs enum 0/1/2) → send only if user names the service.
- `is_cash_discount`, `is_client_account_redemption`: read-only in spec → don't send.
- Delete permanent; invoice status effect n.d. → `get` invoice after, report status.
- Skonto: `create` `value` = amount received → invoice `get` → report `total_remaining_payments`.
- Write-off via API n.d. (`is_cash_discount` read-only) → propose a manual posting (`bexio-accounting`).
- Overpayment (`value` > `total_remaining_payments`): API effect n.d. → ask: open amount + excess as manual posting (`bexio-accounting`)?

## Reminders (Mahnungen)
- `create`: no body → next level · refusal cases (e.g. not overdue) n.d. → check `is_valid_to` + status first.
- `delete`: latest reminder only, permanent.
- `mark_as_sent` / `mark_as_unsent` = flags · `send` = email.

## Orders: repetitions
- Auto-invoicing from a repetition: n.d. → say so · `edit_repetition`: schedule from user's request (core §4).

## Gate rows (core §3.2)
| Row | Class | Preview (`pre_image` + `would_send`) | Skill pre-check |
|---|---|---|---|
| `bexio_invoices.send` | send | document_nr, total + currency, `recipient_email`, subject, full message incl. `[Network Link]`, `attach_pdf`, `mark_as_open`; "emails the customer now" | ⚑ recipient not stored |
| `bexio_quotes.send` | send | as invoice send, quote document_nr + total | ⚑ recipient not stored |
| `bexio_invoice_reminders.send` | send | invoice document_nr, open amount, reminder level, `recipient_email`, subject, message; "emails now" | ⚑ recipient not stored |
| `bexio_invoices.delete` | final delete | id, document_nr, customer, total, status; "permanent" | status ≠ Draft → ⚑ UI: cancel instead |
| `bexio_quotes.delete` | final delete | id, document_nr, customer, total, status; "permanent" | |
| `bexio_orders.delete` | final delete | id, document_nr, customer, total, status; "permanent" | |
| `bexio_invoice_reminders.delete` | final delete | invoice, reminder id + level (latest only); "permanent" | |
- ⚑ recipient not stored: `recipient_email` ≠ contact `mail` / `mail_second` (`bexio_contacts.get`) and not on the company's own mail domain → flag line naming the address source.
  - own domain = `bexio_company_profile` `mail`; empty or public mail-provider domain → no domain exemption

## Direct writes with a skill check (core §3)
| Action | Check → report line |
|---|---|
| `bexio_invoices.revert_issue` | `bexio_invoice_payments.list` → payments recorded → "UI blocks revert with payments; API n.d." |
| `bexio_invoices.cancel` | `bexio_invoice_payments.list` → payments recorded → list them; "no un-cancel via API" |
| `bexio_invoice_payments.create` | bank-feed double: same bank line also matched in bank reconciliation → counted twice (confirmed for supplier bills; sales n.d.) → "if this payment is also matched in bank reconciliation, it counts twice" |

## Customer payment on an invoice
1. `bexio_invoices.search` `document_nr` `=` → `get`.
2. Status 8, 16 or 31; note `total_remaining_payments`.
3. `bexio_bank_accounts.list` → receiving account's integer `id`.
4. `bexio_invoice_payments.create` (check above) → response: invoice status 9 / 16.
