# Banking API lookup

## Tools
- `bexio_bank_accounts`: `list`, `get` (read-only).
- `bexio_banking_payments`: `list`, `get`, `create`, `update`, `cancel`, `delete`.
- Scopes `bank_account_show` · payments `bank_payment_show`, writes `bank_payment_edit`.
- 4.0 endpoints (documented since 2025-09-19; 3.0 marked for deprecation).

## Bank accounts (read-only)
- Fields: `id` (integer), `uuid`, `name`, `owner`, `iban_nr`, `qr_invoice_iban`, `bank_name`, `bank_nr` (BIC), `currency_id`, `account_id` (ledger account).
- `invoice_mode`: `none`, `qr_iban`, `iban_with_creditor_reference`, `iban_only`.

## Payment orders (`bexio_banking_payments`)
- Status `open` (default), `transmitted`, `downloaded`, `paid`, `failed`, `cancelled`.
- Create required:
  - `account_id` (sender `uuid`), `amount`, `currency` (ISO, 3 letters), `execution_date` (≥ next working day), `is_salary` (false), `type` (`iban` | `qr`)
  - `recipient` {`name` ≤70, `iban`, `address` {`street_name`, `house_number` (key required, may be null), `zip`, `city`, `country_code`}}
- Optional: `allowance` (`fee_paid_by_payer`, `fee_paid_by_payee`, `fee_split` default, `no_fee`), `qr_reference_number` (≤27), `additional_information`, `message`, `purchase_reference` {`bill_id`, `bill_payment_id`}.
- Names, addresses, messages: restricted character set, else 422.
- Update: fields allowance, amount, currency, execution_date, is_salary, recipient, reference, information, message · not `account_id`, `type`, `purchase_reference`.
- Cancel: docs: only in status "downloaded", "transferred" or "error" · enum has `transmitted` / `failed`, mapping n.d. (outgoing-payment enum: TRANSFERRED / DOWNLOADED / ERROR).
- List: `page` from 0 (bills: from 1), `per_page` (max 2000), `filter_by` `field:value;field:min_max` over `status`, `account_id`, `currency`, `execution_date`, `amount`, `recipient.name`, `recipient.iban`, `document_no`.

## Month-end
1. Open orders: `list` `filter_by: "status:open"`, then `"status:failed"` → table (recipient, amount, execution date, linked bill).
2. Reconciliation list:
   - `bexio_bank_accounts.get` → `account_id` → account `uuid` (`bexio_accounting` accounts) → journal `list` for the month on it
   - compare with user's bank statement → unmatched lines, proposed postings (`bexio-accounting`) · matching: no API
