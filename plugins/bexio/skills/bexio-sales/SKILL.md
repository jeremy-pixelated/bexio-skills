---
name: bexio-sales
description: 'Use when a Bexio request is about selling: quotes (Offerte), sales orders (Auftrag), delivery notes (Lieferschein), customer invoices (Rechnung an Kunden, Debitorenrechnung), document positions, payments received from customers (Zahlungseingang, Skonto), open receivables (offene Debitoren), reminders and dunning runs (Mahnung, Mahnlauf), credit notes (Gutschrift: no API), document comments or templates — create, issue (verbuchen), revert, cancel (stornieren), send, copy, convert, record a customer payment, check whether a customer invoice is paid. Load the core skill bexio first.'
---

# Bexio sales — quotes, orders, deliveries, invoices, payments received, reminders

Core `bexio` first. All 98 ops: `reference.md`.

## Use / not here
- Invoice paid? · open receivables · document content · payments received · reminders · positions incl. articles.
- Quote, order, invoice: create / change · convert quote → order → delivery / invoice · issue, revert, cancel, send.
- Not here: supplier bills → `bexio-purchase` · ledger side → `bexio-accounting` · bank account ids → `bexio-banking` · article master → `bexio-items`.

## Tools
| Tool | Actions | Gated |
|---|---|---|
| `bexio_quotes` | list, search, get, create, update, delete, issue, revert_issue, accept, decline, reissue, mark_as_sent, send, copy, pdf, create_invoice, create_order | delete, send |
| `bexio_orders` | list, search, get, create, update, delete, pdf, get_repetition, edit_repetition, delete_repetition, create_delivery, create_invoice | delete |
| `bexio_deliveries` | list, get, issue | – |
| `bexio_invoices` | list, search, get, create, update, delete, issue, revert_issue, cancel, mark_as_sent, send, copy, pdf | delete, send |
| `bexio_invoice_payments` | list, get, create, delete | – |
| `bexio_invoice_reminders` | list, search, get, create, delete, send, mark_as_sent, mark_as_unsent, pdf | delete, send |
| `bexio_document_positions` | list, get, create, update, delete | – |
| `bexio_document_comments` | list, get, create | – |
| `bexio_document_settings` | list_settings, list_templates | – |
- Scopes `kb_offer_*`, `kb_order_*`, `kb_invoice_*`, `kb_delivery_*` · conversion needs edit scope of source + target [D:v2CreateOrderFromQuote].

## Status ids (`kb_item_status_id`, read-only)
| Doc | Values [D:v2CreateQuote], [D:v2CreateOrder], [D:v2ShowDelivery], [D:v2CreateInvoice] |
|---|---|
| Quote | 1 Draft, 2 Pending, 3 Confirmed, 4 Declined |
| Order | 5 Pending, 6 Done, 15 Partial, 21 Canceled |
| Delivery | 10 Draft, 18 Done, 20 Canceled |
| Invoice | 7 Draft, 8 Pending, 9 Paid, 16 Partial, 19 Canceled, 31 Unpaid |

## Transitions (read status from the response; (…) = result n.d.)
| Action | Precondition → result |
|---|---|
| quote `issue` | Draft → (Pending) [D:v2IssueQuote] |
| quote `revert_issue` | → Draft [D:v2RevertIssueQuote] |
| quote `accept` / `decline` | status 2 → (Confirmed / Declined) [D:v2AcceptQuote], [D:v2DeclineQuote] |
| quote `reissue` | accepted / declined → Pending [D:v2ReissueQuote] |
| invoice `issue` | Draft → status + ledger effect n.d. → say so [D:v2IssueInvoice] |
| invoice `revert_issue` | issued → Draft; ledger effect n.d. → say so [D:v2RevertIssueInvoice] |
| invoice `cancel` | issued only; no un-cancel endpoint [D:v2CancelInvoice] |
| delivery `issue` | Draft only [D:v2IssueDelivery] |
- Orders: no status actions · Paid / Partial / Unpaid: trigger n.d. per endpoint → read status.
- UI-only rules [H:000001859]; API enforcement n.d. → skill pre-check (gate row / direct-write table):
  - revert to Draft: only without recorded payment
  - paid / partially paid invoice: content frozen
  - delete: Draft only, else cancel · credit notes: no API [D§FAQ] → user in Bexio UI

## Documents (2.0)
- Create: no field marked required [D:v2CreateInvoice]; usable minimum n.d. → send `contact_id`, `user_id`, `positions` · `document_nr` not settable with automatic numbering on (`list_settings`).
- Key fields:
  - `title`, `contact_id`, `contact_sub_id`, `pr_project_id`, `language_id`, `bank_account_id` (integer), `currency_id`, `payment_type_id`, `header`, `footer`, `reference`, `template_slug` (`list_templates`)
  - `mwst_type` (0 incl. VAT, 1 excl., 2 exempt; integer here, string on purchase orders), `mwst_is_net`
  - `is_valid_from`, `is_valid_to` (invoice due; quote `is_valid_until`) · `api_reference` (searchable on invoices)
- Totals read-only decimal strings: `total_gross`, `total_net`, `total_taxes`, `total_remaining_payments`, `total`.
- Max ~150 positions per create; more via `bexio_document_positions`.
- Create `positions[]` (quote / order / invoice) [D:v2CreateInvoice]:
  - variants `KbPositionCustom`, `KbPositionArticle`, `KbPositionText`, `KbPositionSubtotal`, `KbPositionPagebreak`, `KbPositionDiscount`
  - never copy from a GET: `id`, `pos`, `internal_pos`, `position_total`, `unit_name`, `tax_value`, `discount_total`, `parent_id`, `value` (subtotal / pagebreak)
  - `amount`, `unit_price` = decimal strings ("2", "150.00") · `is_optional`: custom / article positions on quotes / orders only
- `update` = POST, same fields, no positions [D:v2EditInvoice] · issued-document positions: API n.d., UI Draft only → change in Draft only.
- `copy`: `copy.contact_id` required, also for same customer [D:v2CopyInvoice].
- Conversions (`create_order`, `create_invoice`, `create_delivery`): optional `positions[]` {`id`, `type`, `amount`}; omit = all [D:v2CreateOrderFromQuote].
- `mark_as_sent` = flag only, no email, ungated.
- `send` = emails now: `recipient_email`, `subject`, `message` required · message must contain "[Network Link]" · trial period: recipient = token's own address only [D:v2SendInvoice].
- Invoice search fields: id, kb_item_status_id, document_nr, title, api_reference, contact_id, contact_sub_id, user_id, currency_id, total_gross, total_net, total, is_valid_from, is_valid_to, updated_at [D:v2SearchInvoices].

## Positions (`bexio_document_positions`)
- `document_type` `kb_offer` | `kb_order` | `kb_invoice` (deliveries: no) · `document_id` · `position_type` `custom`, `article`, `text`, `subtotal`, `discount`, `pagebreak`, `subposition`.
- Money / qty strings, max 6 decimals · `tax_id` = active sales tax only (`bexio_accounting` taxes `list`, `types: sales_tax`, `scope: active`) [D:v2CreateItemPosition].
- Full document = one `list` per position type; skip `discount` → wrong totals · delete permanent.

## Payments received (`bexio_invoice_payments`)
- `create`: `value` required (string, `"150.00"`) · `date`: connector requires it (spec optional; API default n.d.) · `bank_account_id` = integer `id` (`bexio_bank_accounts.list`) [D:v2CreateInvoicePayment].
- `payment_service_id`: docs contradictory (table 1 PayPal, 2 Stripe, 3 SIX vs enum 0/1/2) → send only if user names the service.
- `is_cash_discount`, `is_client_account_redemption`: read-only in spec → don't send.
- Delete permanent [D:DeleteInvoicePayment]; invoice status effect n.d. → `get` invoice after, report status.
- Skonto (cash discount) [D:v2CreateInvoicePayment], [D:v2ShowInvoice]:
  - `create` `value` = amount received → invoice `get` → report `total_remaining_payments`
  - write-off via API n.d. (`is_cash_discount` read-only) → propose manual posting (`bexio-accounting`) or user in Bexio UI
- Overpayment (`value` > `total_remaining_payments`): API effect n.d. → ask: open amount + excess as manual posting (`bexio-accounting`), or user in Bexio UI.

## Reminders (Mahnungen)
- `create`: no body → next level [D:v2CreateInvoiceReminder] · refusal cases (e.g. not overdue) n.d. → check `is_valid_to` + status first.
- `delete`: latest reminder only, permanent [D:v2DeleteInvoiceReminder].
- `mark_as_sent` / `mark_as_unsent` = flags · `send` = email.

## Orders: repetitions
- `get_repetition` / `edit_repetition` / `delete_repetition` · rule `daily`, `weekly`, `monthly`, `yearly` + `start`, `end` (null = open) [D:v2EditOrderRepetition].
- Auto-invoicing from a repetition: n.d. → say so · `edit_repetition`: schedule from user's request (core §4).

## Gate rows (core §3.2)
| Row | Class | Preview (`pre_image` + `would_send`) | Skill pre-check |
|---|---|---|---|
| `bexio_invoices.send` | send | document_nr, total + currency, `recipient_email`, subject, full message incl. `[Network Link]`, `attach_pdf`, `mark_as_open`; "emails the customer now" | ⚑ recipient not stored |
| `bexio_quotes.send` | send | as invoice send, quote document_nr + total | ⚑ recipient not stored |
| `bexio_invoice_reminders.send` | send | invoice document_nr, open amount, reminder level, `recipient_email`, subject, message; "emails now" | ⚑ recipient not stored |
| `bexio_invoices.delete` | final delete | id, document_nr, customer, total, status; "permanent" | status ≠ Draft → ⚑ UI: cancel instead |
| `bexio_quotes.delete` | final delete | id, document_nr, customer, total, status; "permanent" | – |
| `bexio_orders.delete` | final delete | id, document_nr, customer, total, status; "permanent" | – |
| `bexio_invoice_reminders.delete` | final delete | invoice, reminder id + level (latest only); "permanent" | – |
- ⚑ recipient not stored: `recipient_email` ≠ contact `mail` / `mail_second` (`bexio_contacts.get`) and not on the company's own mail domain → flag line naming the address source.
  - own domain = `bexio_company_profile` `mail`; empty or public mail-provider domain → no domain exemption

## Direct writes with a skill check (core §3)
| Action | Check → report line |
|---|---|
| `bexio_invoices.revert_issue` | `bexio_invoice_payments.list` → payments recorded → "UI blocks revert with payments [H:000001859]; API n.d." |
| `bexio_invoices.cancel` | `bexio_invoice_payments.list` → payments recorded → list them; "no un-cancel via API" |
| `bexio_invoice_payments.create` | bank-feed double: same bank line also matched in bank reconciliation → counted twice (confirmed for supplier bills [H:000001755]; sales n.d.) → "if this payment is also matched in bank reconciliation, it counts twice" |
- Other ungated writes (`issue`, `delete_repetition`, payment `delete`, position `delete`): call, report id + resulting status.

## Customer payment on an invoice
1. `bexio_invoices.search` `document_nr` `=` → `get`.
2. Status 8, 16 or 31; note `total_remaining_payments`.
3. `bexio_bank_accounts.list` → receiving account's integer `id`.
4. `bexio_invoice_payments.create` (check above) → response: invoice status 9 / 16.

## Gotchas
1. Quote endpoints: `decline` = `/reject`, `revert_issue` = `/revertIssue`.
2. PDFs base64 inline: never paste.

---
Sources: https://docs.bexio.com/ (OpenAPI 3.0.2; ops cited above; full list `reference.md`) · help.bexio.com 000001859, 000001755, fetched 2026-09-24.
