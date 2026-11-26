# Purchase API lookup

## Tools

| Tool | Actions |
|---|---|
| `bexio_bills` | list, get, create, update, delete, execute_action, update_status, validate_document_number |
| `bexio_expenses` | list, get, create, update, delete, execute_action, update_status, validate_document_number |
| `bexio_purchase_orders` | list, get, create, update, delete |
| `bexio_outgoing_payments` | list, get, create, update, delete |
- Scopes:
  - bill / expense / outgoing-payment ops declare only `openid contact_show` · payment update + `bank_payment_edit` · delete + `kb_bill_show`
  - 403 on bill / expense write → user's `kb_bill` / `expense` permission
  - purchase orders `kb_article_order_*`

## Bills (UUID ids)

- Status `DRAFT, BOOKED, PARTIALLY_CREATED, CREATED, PARTIALLY_SENT, SENT, PARTIALLY_DOWNLOADED, DOWNLOADED, PARTIALLY_PAID, PAID, PARTIALLY_FAILED, FAILED`.
- List: `filters.status` `DRAFTS`, `TODO`, `PAID`, `OVERDUE` · `limit` max 500, `page` from 1 · `search_term` 3 to 255 chars over `search_fields`.
- Create → always DRAFT. `payload`:
  - required: `supplier_id`, `contact_partner_id`, `bill_date`, `due_date`, `manual_amount`, `currency_code`, `item_net`, `attachment_ids` (file `uuid`s, may be empty), `discounts` (may be empty)
  - required: `address` (`lastname_company` + `type` PRIVATE|COMPANY) · `line_items` (each `position` + `amount`; positions from 0)
  - + `amount_man` if `manual_amount=true`, else `amount_calc` · foreign currency: + `exchange_rate`, `base_currency_amount`
  - optional: `vendor_ref`, `title`, `purchase_order_id`, `qr_bill_information`
  - amounts = numbers, max 2 decimals · `document_no` generated after create, updatable
- Month-end fields: `pending_amount`, `gross`, `net`, `overdue` (always false for DRAFT + PAID), `attachment_ids`.

## Expenses (UUID ids)

- Status `DRAFT` / `DONE`; create → DRAFT · create required: `paid_on`, `currency_code`, `amount`, `attachment_ids` (file `uuid`s, no duplicates).

## Purchase orders (integer ids)

- Status 22 Draft, 23 Open, 24 Partly, 25 Done, 26 Canceled; read-only, no status action · `mwst_type` string (`included`, `excluded`, `exempt`).
- Update = PUT without positions · delete permanent.
- Create `positions`:
  - `required` / `optional` = text, group, subtotal, pagebreak · article + custom only inside group `positions` · no group in a group
  - `discount` = discount positions · `type` on every node · unknown field on any node → connector refuses

## Outgoing payments (per bill, UUID ids)

- Status (response) `PENDING, TRANSFERRED, DOWNLOADED, ERROR, PAID, DISCOUNTED` · `list`: `bill_id` required; no global list.
- Create required:
  - `bill_id` (bill not DRAFT), `payment_type` (`IBAN`, `MANUAL`, `CASH_DISCOUNT`, `QR`), `execution_date`, `is_salary_payment`
  - `amount` (≤ bill `pending_amount`), `currency_code` (= bill currency), `exchange_rate`
  - `sender_bank_account_id` (integer bank account `id`; none for CASH_DISCOUNT)
- IBAN / QR: + sender + receiver name, IBAN, street, house no, postcode, city, country.
- Update: id in `payload.payment_id` (or `id`); PUT body: no `currency_code` / `exchange_rate` · UI: edits IBAN / QR only, in pending / failed; sender account + type fixed.
