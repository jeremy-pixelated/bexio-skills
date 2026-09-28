---
name: bexio-sales
description: 'Use when a Bexio request is about selling: quotes (Offerte), sales orders (Auftrag), delivery notes (Lieferschein), customer invoices (Rechnung an Kunden, Debitorenrechnung), document positions, payments received from customers (Zahlungseingang, Skonto), open receivables (offene Debitoren), reminders and dunning runs (Mahnung, Mahnlauf), credit notes (Gutschrift: no API), document comments or templates — create, issue (verbuchen), revert, cancel (stornieren), send, copy, convert, record a customer payment, check whether a customer invoice is paid. Load the core skill bexio first.'
---

# Bexio sales — quotes, orders, deliveries, invoices, payments received, reminders

Core `bexio` first (router, gate, flags). All 98 ops: `reference.md`.

## Use / not here
- Customer invoice paid?; open receivables; document content; create / change quote, order, invoice; convert quote → order → delivery / invoice; issue, revert, cancel, send; payments received; reminders; positions incl. articles on a document.
- Not here: supplier bills → `bexio-purchase` · ledger side → `bexio-accounting` · bank account ids → `bexio-banking` · article master → `bexio-items`.

## Tools
| Tool | Actions | Gated |
|---|---|---|
| `bexio_quotes` | list, search, get, create, update, delete, issue, revert_issue, accept, decline, reissue, mark_as_sent, send, copy, pdf, create_invoice, create_order | delete, send |
| `bexio_orders` | list, search, get, create, update, delete, pdf, get_repetition, edit_repetition, delete_repetition, create_delivery, create_invoice | delete, delete_repetition |
| `bexio_deliveries` | list, get, issue | – |
| `bexio_invoices` | list, search, get, create, update, delete, issue, revert_issue, cancel, mark_as_sent, send, copy, pdf | delete, issue, revert_issue, cancel, send |
| `bexio_invoice_payments` | list, get, create, delete | create, delete |
| `bexio_invoice_reminders` | list, search, get, create, delete, send, mark_as_sent, mark_as_unsent, pdf | delete, send |
| `bexio_document_positions` | list, get, create, update, delete | delete |
| `bexio_document_comments` | list, get, create | – |
| `bexio_document_settings` | list_settings, list_templates | – |
- Scopes `kb_offer_*`, `kb_order_*`, `kb_invoice_*`, `kb_delivery_*`; conversion needs edit scope of source + target [D:v2CreateOrderFromQuote].

## Status ids (`kb_item_status_id`, read-only)
| Doc | Values [D:v2CreateQuote], [D:v2CreateOrder], [D:v2ShowDelivery], [D:v2CreateInvoice] |
|---|---|
| Quote | 1 Draft, 2 Pending, 3 Confirmed, 4 Declined |
| Order | 5 Pending, 6 Done, 15 Partial, 21 Canceled |
| Delivery | 10 Draft, 18 Done, 20 Canceled |
| Invoice | 7 Draft, 8 Pending, 9 Paid, 16 Partial, 19 Canceled, 31 Unpaid |

## Transitions (read status from the response; results in () n.d.)
- Quote `issue`: must be Draft (→ Pending n.d.) [D:v2IssueQuote] · `revert_issue` → Draft [D:v2RevertIssueQuote] · `accept` / `decline`: need status 2 (→ Confirmed / Declined n.d.) [D:v2AcceptQuote], [D:v2DeclineQuote] · `reissue` → Pending from accepted / declined [D:v2ReissueQuote].
- Invoice `issue`: must be Draft; resulting status + ledger effect n.d. → gated as posting [D:v2IssueInvoice] · `revert_issue`: issued → Draft; ledger effect n.d. → gated as posting [D:v2RevertIssueInvoice] · `cancel`: cancels an issued invoice; no un-cancel endpoint [D:v2CancelInvoice] · how Paid / Partial / Unpaid are reached: n.d. per endpoint → read status.
- Delivery `issue`: must be Draft [D:v2IssueDelivery]. Orders: no status actions.
- UI-only rules (API enforcement n.d. → skill pre-check) [H:000001859]: revert to Draft only without recorded payment · paid / partially paid invoice: content frozen · delete only in Draft, else cancel (credit notes: no API [D§FAQ] → user in Bexio UI).

## Documents (2.0)
- Create: no field marked required [D:v2CreateInvoice]; minimum for a usable document n.d. → send `contact_id`, `user_id`, `positions`. `document_nr` not settable with automatic numbering on (`list_settings`).
- Key fields: `title`, `contact_id`, `contact_sub_id`, `pr_project_id`, `language_id`, `bank_account_id` (integer), `currency_id`, `payment_type_id`, `header`, `footer`, `mwst_type` (0 incl. VAT, 1 excl., 2 exempt), `mwst_is_net`, `is_valid_from`, `is_valid_to` (invoice due; quote `is_valid_until`), `reference`, `api_reference` (searchable on invoices), `template_slug` (`list_templates`).
- Totals read-only decimal strings: `total_gross`, `total_net`, `total_taxes`, `total_remaining_payments`, `total`.
- Max ~150 positions per create; more via `bexio_document_positions`.
- Create `positions[]` (quote / order / invoice): variants `KbPositionCustom`, `KbPositionArticle`, `KbPositionText`, `KbPositionSubtotal`, `KbPositionPagebreak`, `KbPositionDiscount` [D:v2CreateInvoice]. Writable fields only: never copy `id`, `pos`, `internal_pos`, `position_total`, `unit_name`, `tax_value`, `discount_total`, `parent_id`, `value` (subtotal / pagebreak) from a GET. `amount`, `unit_price` = decimal strings ("2", "150.00"). `is_optional`: custom / article positions on quotes / orders only.
- `update` = POST, same fields, no positions [D:v2EditInvoice]. Positions of an issued document: API n.d.; UI: Draft only → change positions in Draft only.
- `copy`: `copy.contact_id` required, also same customer [D:v2CopyInvoice].
- Conversions (`create_order`, `create_invoice`, `create_delivery`): optional `positions[]` {`id`, `type`, `amount`}; omit = all [D:v2CreateOrderFromQuote].
- `mark_as_sent` = flag only, no email, ungated → call directly. `send` = emails now: `recipient_email`, `subject`, `message` required; message with "[Network Link]" (required); trial period: recipient limited to the token's own address [D:v2SendInvoice].
- Invoice search fields: id, kb_item_status_id, document_nr, title, api_reference, contact_id, contact_sub_id, user_id, currency_id, total_gross, total_net, total, is_valid_from, is_valid_to, updated_at [D:v2SearchInvoices].

## Positions (`bexio_document_positions`)
- `document_type` `kb_offer` | `kb_order` | `kb_invoice` (deliveries: no) · `document_id` · `position_type` `custom`, `article`, `text`, `subtotal`, `discount`, `pagebreak`, `subposition`.
- Money / qty strings, max 6 decimals; `tax_id` = active sales tax only (`bexio_accounting` taxes `list`, `types: sales_tax`, `scope: active`) [D:v2CreateItemPosition].
- Full document = one `list` per position type; skip `discount` → wrong totals. Delete permanent.

## Payments received (`bexio_invoice_payments`)
- `create`: `value` required (string, `"150.00"`) · `date`: the connector requires it (spec: optional; API default n.d.) · `bank_account_id` = integer `id` from `bexio_bank_accounts.list` [D:v2CreateInvoicePayment].
- `payment_service_id`: docs contradictory (table 1 PayPal, 2 Stripe, 3 SIX vs enum 0/1/2) → send only when the user names the service.
- `is_cash_discount`, `is_client_account_redemption`: read-only in spec → don't send.
- Delete permanent [D:DeleteInvoicePayment]; effect on invoice status n.d. → `get` invoice after, report status.
- Skonto (cash discount): `create` `value` = amount received · then invoice `get` → report `total_remaining_payments` · discount write-off via API n.d. (`is_cash_discount` read-only) → propose a manual posting (`bexio-accounting`) or the user in Bexio UI [D:v2CreateInvoicePayment], [D:v2ShowInvoice].
- Overpayment (`value` > `total_remaining_payments`): API effect n.d. → ask: record the open amount + excess as manual posting (`bexio-accounting`), or user in Bexio UI.

## Reminders (Mahnungen)
- `create`: no body → next level [D:v2CreateInvoiceReminder]. Refusal case (e.g. not overdue) n.d. → check `is_valid_to` + status first.
- `delete`: most recent reminder only, permanent [D:v2DeleteInvoiceReminder].
- `mark_as_sent` / `mark_as_unsent` = flags; `send` = email.

## Orders: repetitions
- `get_repetition` / `edit_repetition` / `delete_repetition`; rule `daily`, `weekly`, `monthly`, `yearly` + `start`, `end` (null = open) [D:v2EditOrderRepetition].
- Auto-invoicing from a repetition: n.d. → say so; `edit_repetition`: schedule from the user's request (core §4).

## Gate rows (core §3.2: dry run → one preview → one yes → call with the dry run's `acknowledge_flags`)
| Row | Class | Preview (`pre_image` + `would_send`) | Skill pre-check |
|---|---|---|---|
| `bexio_invoices.issue` | posting | id + document_nr, customer, title, date + due, net / VAT / gross, currency, positions (text, qty, unit price, account, tax), bank account / QR; "leaves Draft; ledger effect n.d., treated as posting" | – |
| `bexio_invoices.revert_issue` | posting | document_nr, status (Pending / Unpaid), total; "back to Draft; ledger effect n.d." | `bexio_invoice_payments.list` → payments recorded → ⚑ UI blocks revert [H:000001859] |
| `bexio_invoices.cancel` | cancel | document_nr, customer, total, status; "no un-cancel via API" | `bexio_invoice_payments.list` → payments in the preview |
| `bexio_invoices.send` | send | document_nr, `recipient_email`, subject, full message incl. `[Network Link]`, `attach_pdf`, `mark_as_open`; "emails the customer now" | ⚑ recipient not stored |
| `bexio_quotes.send` | send | as invoice send, quote document_nr | ⚑ recipient not stored |
| `bexio_invoice_reminders.send` | send | invoice document_nr, reminder level, `recipient_email`, subject, message; "emails now" | ⚑ recipient not stored |
| `bexio_invoice_payments.create` | posting | invoice document_nr + customer, open amount (`total_remaining_payments`), `value`, `date`, bank account (name + IBAN), resulting status (Paid / Partial) | ⚑ bank-feed double |
| `bexio_invoice_payments.delete` | delete | invoice, payment id, date, value, bank account; "permanent; status effect n.d." | – |
| `bexio_invoices.delete` | delete | id, document_nr, customer, total, status; "permanent" | status ≠ Draft → ⚑ UI: cancel instead |
| `bexio_quotes.delete` | delete | id, document_nr, customer, total, status; "permanent" | – |
| `bexio_orders.delete` | delete | id, document_nr, customer, total, status; "permanent" | – |
| `bexio_orders.delete_repetition` | delete | order id + document_nr, current rule | – |
| `bexio_invoice_reminders.delete` | delete | invoice, reminder id + level (latest only); "permanent" | – |
| `bexio_document_positions.delete` | delete | doc type + nr, position type + id, text, amount, line total; "permanent" | – |
- ⚑ recipient not stored: `recipient_email` ≠ contact `mail` / `mail_second` (`bexio_contacts.get`) and not on the company's own mail domain (from `bexio_company_profile` `mail`; empty or public mail-provider domain → no domain exemption) → flag line naming the address source.
- ⚑ bank-feed double: same bank line also matched in Bexio bank reconciliation → API payment + match may count twice (confirmed for supplier bills [H:000001755]; sales n.d.) → same question: also matched in reconciliation?

## Customer payment on an invoice
1. `bexio_invoices.search` `document_nr` `=` → `get`.
2. Status 8, 16 or 31; note `total_remaining_payments`.
3. `bexio_bank_accounts.list` → integer `id` of the receiving account.
4. Gate row `bexio_invoice_payments.create` → response: invoice status 9 / 16.

## Gotchas
1. `revert_issue` / `cancel` / `delete` preconditions = UI help only [H:000001859] → skill pre-checks.
2. `send` = email now · `mark_as_sent` = flag only.
3. Quote endpoints: `decline` = `/reject`, `revert_issue` = `/revertIssue`.
4. `mwst_type`: integer here, string on purchase orders.
5. PDFs base64 inline: never paste.

---
Sources: https://docs.bexio.com/ (OpenAPI 3.0.2; ops cited above; full list `reference.md`) · help.bexio.com 000001859, 000001755, fetched 2026-09-24.
