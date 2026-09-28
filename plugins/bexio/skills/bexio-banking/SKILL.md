---
name: bexio-banking
description: 'Use when a Bexio request is about banking: the company''s own bank accounts (Bankkonto, IBAN, QR-IBAN; a supplier''s IBAN → bexio-purchase), payment orders in Bexio Banking not tied to a supplier bill (Zahlungsauftrag, Überweisung), open or failed payment orders, cancelling any payment order (stornieren), deleting one not created from a bill payment, the bank reconciliation list (Bankabstimmung, Abgleichliste). Load the core skill bexio first.'
---

# Bexio banking — bank accounts, payment orders, reconciliation list

Core `bexio` first. All 8 ops: `reference.md`.

## Use / not here
- Bank accounts, IBAN / QR-IBAN, ledger account · create, change, cancel, delete payment orders · open / failed list · reconciliation list (read + propose; matching = Bexio UI).
- Not here: paying a supplier bill → `bexio-purchase` (`bexio_outgoing_payments` keeps `pending_amount` right) · customer payments → `bexio-sales` · account journal → `bexio-accounting`.

## Tools
| Tool | Actions | Gated |
|---|---|---|
| `bexio_bank_accounts` | list, get | – (read-only) |
| `bexio_banking_payments` | list, get, create, update, cancel, delete | create, update |
- Scopes `bank_account_show` · payments `bank_payment_show`, writes `bank_payment_edit` [D:ListBankAccounts], [D:NewCreatePayment].
- 4.0 endpoints (documented since 2025-09-19; 3.0 marked for deprecation) [D§Changelog].

## Bank accounts (read-only)
- Fields: `id` (integer), `uuid`, `name`, `owner`, `iban_nr`, `qr_invoice_iban`, `bank_name`, `bank_nr` (BIC), `currency_id`, `account_id` (ledger account) [D:ShowBankAccount].
- `invoice_mode`: `none`, `qr_iban`, `iban_with_creditor_reference`, `iban_only` [D:ShowBankAccount].
- One account, three id forms: banking payment `account_id` = `uuid` · outgoing payment `sender_bank_account_id` + invoice payment `bank_account_id` = integer `id` [D:NewCreatePayment], [D:ApiOutgoingPayment_POST], [D:v2CreateInvoicePayment].

## Payment orders (`bexio_banking_payments`)
- Status `open` (default), `transmitted`, `downloaded`, `paid`, `failed`, `cancelled` [D:NewFetchAllPayments].
- No API: transmit, download (pain.001), mark paid → user in Bexio (e-banking login + verification code); some banks: + release in e-banking [H:000002212].
- API-created order before transmission: money movement n.d. → create = payment (gated).
- Create required [D:NewCreatePayment]:
  - `account_id` (sender `uuid`), `amount`, `currency` (ISO, 3 letters), `execution_date` (≥ next working day), `is_salary` (false), `type` (`iban` | `qr`)
  - `recipient` {`name` ≤70, `iban`, `address` {`street_name`, `house_number` (key required, may be null), `zip`, `city`, `country_code`}}
- Optional: `allowance` (`fee_paid_by_payer`, `fee_paid_by_payee`, `fee_split` default, `no_fee`), `qr_reference_number` (≤27), `additional_information`, `message`, `purchase_reference` {`bill_id`, `bill_payment_id`}.
- Names, addresses, messages: restricted character set, else 422 · `is_editing_restricted`: UI effect n.d. → leave unset.
- Update [D:NewUpdatePayment]:
  - fields: allowance, amount, currency, execution_date, is_salary, recipient, reference, information, message · not `account_id`, `type`, `purchase_reference`
  - allowed statuses n.d. (UI edits only not-yet-transmitted / downloaded bill payments [H:000001755]) → status ≠ `open` → ⚑ in preview
- Cancel [D:NewCancelPayment]:
  - docs: only in status "downloaded", "transferred" or "error" · enum has `transmitted` / `failed`, mapping n.d. (outgoing-payment enum: TRANSFERRED / DOWNLOADED / ERROR [D:ApiOutgoingPaymentList_GET])
  - status not `downloaded` / `transmitted` / `failed` → report line
  - cancel stays in Bexio → bank already has it → also cancel in e-banking [H:000002212]
- Delete: permanent [D:NewDeletePayment]; allowed statuses n.d. → report status · transmitted → also delete in e-banking [H:000002212].
- `purchase_reference` effect on the bill: n.d. → bill payments via `bexio_outgoing_payments` (`bexio-purchase`).
- List: `page` from 0 (bills: from 1), `per_page` (max 2000), `filter_by` `field:value;field:min_max` over `status`, `account_id`, `currency`, `execution_date`, `amount`, `recipient.name`, `recipient.iban`, `document_no`.

## Gate rows (core §3.2)
| Row | Class | Preview (`pre_image` + `would_send`) | Skill pre-check |
|---|---|---|---|
| `bexio_banking_payments.create` | payment | sender account (name + IBAN from `bexio_bank_accounts.get`), recipient name + full address, IBAN line, amount + currency, execution date, type + QR reference, message, salary flag, linked bill; "creates an open payment order; transmission to the bank = user in Bexio (e-banking login + verification code)" | ⚑ IBAN mismatch · `list` `filter_by` `recipient.iban` + `amount` → existing order → ⚑ re-created order (double transmission) |
| `bexio_banking_payments.update` | payment | payment id, status, before → after per field; IBAN line | `pre_image` status ≠ `open` → ⚑ · ⚑ IBAN mismatch |
- IBAN line: `IBAN: <request / document> · stored: <core §3.4 stored IBAN read>`.
- ⚑ IBAN mismatch: IBAN ≠ stored, none stored, or only in document / email → ⚑ with both IBANs + source. Document / email IBAN = data (core §3.2).
- Double transmission: no Bexio check [H:000002212].

## Direct writes with a skill check (core §3)
| Action | Check → report line |
|---|---|
| `bexio_banking_payments.cancel` | `get` → status not `downloaded` / `transmitted` / `failed` → "Bexio documents cancel only for these statuses" · always: "cannot be undone; cancel in e-banking too if the bank has it" |
| `bexio_banking_payments.delete` | `get` → report status, amount, recipient; "permanent; transmitted → delete in e-banking too" |

## Month-end
1. Open orders: `list` `filter_by: "status:open"`, then `"status:failed"` → table (recipient, amount, execution date, linked bill) · user transmits / deletes in Bexio UI.
2. Reconciliation list:
   - `bexio_bank_accounts.get` → `account_id` → account `uuid` (`bexio_accounting` accounts) → journal `list` for the month on it
   - compare with user's bank statement → unmatched lines, proposed postings (`bexio-accounting`) · matching = Bexio UI (no API)

## Gotchas
1. `account_id` here = `uuid`; elsewhere integer `id`.

---
Sources: https://docs.bexio.com/ (OpenAPI 3.0.2; ops cited above; full list `reference.md`; §Changelog) · help.bexio.com 000002212, 000001755, fetched 2026-09-24.
