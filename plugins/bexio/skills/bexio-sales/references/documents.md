# Sales API lookup

## Tools

| Tool | Actions |
|---|---|
| `bexio_quotes` | list, search, get, create, update, delete, issue, revert_issue, accept, decline, reissue, mark_as_sent, send, copy, pdf, create_invoice, create_order |
| `bexio_orders` | list, search, get, create, update, delete, pdf, get_repetition, edit_repetition, delete_repetition, create_delivery, create_invoice |
| `bexio_deliveries` | list, get, issue |
| `bexio_invoices` | list, search, get, create, update, delete, issue, revert_issue, cancel, mark_as_sent, send, copy, pdf |
| `bexio_invoice_payments` | list, get, create, delete |
| `bexio_invoice_reminders` | list, search, get, create, delete, send, mark_as_sent, mark_as_unsent, pdf |
| `bexio_document_positions` | list, get, create, update, delete |
| `bexio_document_comments` | list, get, create |
| `bexio_document_settings` | list_settings, list_templates |

## Status ids (`kb_item_status_id`, read-only)

| Doc | Values |
|---|---|
| Quote | 1 Draft, 2 Pending, 3 Confirmed, 4 Declined |
| Order | 5 Pending, 6 Done, 15 Partial, 21 Canceled |
| Delivery | 10 Draft, 18 Done, 20 Canceled |
| Invoice | 7 Draft, 8 Pending, 9 Paid, 16 Partial, 19 Canceled, 31 Unpaid |

## Transitions (read status from the response; (…) = result n.d.)

| Action | Precondition → result |
|---|---|
| quote `issue` | Draft → (Pending) |
| quote `revert_issue` | → Draft |
| quote `accept` / `decline` | status 2 → (Confirmed / Declined) |
| quote `reissue` | accepted / declined → Pending |
| invoice `issue` | Draft → status + ledger effect n.d. → say so |
| invoice `revert_issue` | issued → Draft; ledger effect n.d. → say so |
| invoice `cancel` | issued only; no un-cancel endpoint |
| delivery `issue` | Draft only |

## Documents (2.0)

- Key fields:
  - `title`, `contact_id`, `contact_sub_id`, `pr_project_id`, `language_id`, `bank_account_id` (integer), `currency_id`, `payment_type_id`, `header`, `footer`, `reference`, `template_slug` (`list_templates`)
  - `mwst_type` (0 incl. VAT, 1 excl., 2 exempt; integer here, string on purchase orders), `mwst_is_net`
  - `is_valid_from`, `is_valid_to` (invoice due; quote `is_valid_until`) · `api_reference` (searchable on invoices)
- Totals read-only decimal strings: `total_gross`, `total_net`, `total_taxes`, `total_remaining_payments`, `total`.
- `positions[]` variants: `KbPositionCustom`, `KbPositionArticle`, `KbPositionText`, `KbPositionSubtotal`, `KbPositionPagebreak`, `KbPositionDiscount`.
- `amount`, `unit_price` = decimal strings ("2", "150.00") · `is_optional`: custom / article positions on quotes / orders only.
- Conversions (`create_order`, `create_invoice`, `create_delivery`): optional `positions[]` {`id`, `type`, `amount`}; omit = all.
- Invoice search fields: id, kb_item_status_id, document_nr, title, api_reference, contact_id, contact_sub_id, user_id, currency_id, total_gross, total_net, total, is_valid_from, is_valid_to, updated_at.

## Positions (`bexio_document_positions`)

- `document_type` `kb_offer` | `kb_order` | `kb_invoice` (deliveries: no) · `document_id` · `position_type` `custom`, `article`, `text`, `subtotal`, `discount`, `pagebreak`, `subposition`.

## Orders: repetitions

- `get_repetition` / `edit_repetition` / `delete_repetition` · rule `daily`, `weekly`, `monthly`, `yearly` + `start`, `end` (null = open).

## Gotchas

- Quote endpoints: `decline` = `/reject`, `revert_issue` = `/revertIssue`.
