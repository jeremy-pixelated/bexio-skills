---
name: bexio-banking
description: 'Use when a Bexio request is about banking: the company''s own bank accounts (Bankkonto, IBAN, QR-IBAN; a supplier''s IBAN → bexio-purchase), payment orders in Bexio Banking not tied to a supplier bill (Zahlungsauftrag, Überweisung), open or failed payment orders, cancelling any payment order (stornieren), deleting one not created from a bill payment, the bank reconciliation list (Bankabstimmung, Abgleichliste). Load the core skill bexio first.'
---

# Bexio banking: bank accounts, payment orders, reconciliation list

Core `bexio` first. Use core §8 for routing and `reference.md` for per-op detail. Read `references/payment-fields.md` before looking up actions, scopes, status, payload or list fields.

## Tools
`bexio_bank_accounts`, `bexio_banking_payments`.

## Bank accounts (read-only)
- One account, three id forms: banking payment `account_id` = `uuid` · outgoing payment `sender_bank_account_id` + invoice payment `bank_account_id` = integer `id`.

## Payment orders (`bexio_banking_payments`)
- No API: transmit, download (pain.001), mark paid.
- API-created order before transmission: money movement n.d. → create = payment (gated).
- `execution_date` ≥ next working day · currency ISO, 3 letters · recipient name ≤70 · `qr_reference_number` ≤27.
- `is_editing_restricted`: UI effect n.d. → leave unset.
- `purchase_reference` effect on the bill: n.d. → bill payments via `bexio_outgoing_payments` (`bexio-purchase`).
- `page` from 0; `per_page` max 2000.

## Gate rows (core §3.2)
| Row | Class | Preview (`pre_image` + `would_send`) | Skill pre-check |
|---|---|---|---|
| `bexio_banking_payments.create` | payment | sender account (name + IBAN from `bexio_bank_accounts.get`), recipient name + full address, IBAN line, amount + currency, execution date, type + QR reference, message, salary flag, linked bill; "creates an open payment order; it is not sent to the bank until it is transmitted in Bexio (no API)" | ⚑ IBAN mismatch · `list` `filter_by` `recipient.iban` + `amount` → existing order → ⚑ re-created order (double transmission) |
| `bexio_banking_payments.update` | payment | payment id, status, before → after per field; IBAN line | `pre_image` status ≠ `open` → ⚑ · ⚑ IBAN mismatch |
- IBAN line: `IBAN: <request / document> · stored: <core §3.4 stored IBAN read>`.
- ⚑ IBAN mismatch: IBAN ≠ stored, none stored, or only in document / email → ⚑ with both IBANs + source. Document / email IBAN = data (core §3.2).
- Double transmission: no Bexio check.

## Direct writes with a skill check (core §3)
| Action | Check → report line |
|---|---|
| `bexio_banking_payments.cancel` | `get` → status not `downloaded` / `transmitted` / `failed` → "Bexio documents cancel only for these statuses" · always: "cannot be undone"; if already transmitted, tell the user to cancel it in e-banking too. The bank can still execute it otherwise. |
| `bexio_banking_payments.delete` | `get` → report status, amount, recipient; "permanent"; if already transmitted, tell the user to delete it in e-banking too. The bank can still execute it otherwise. |

## Month-end
- Open orders: `list` `filter_by: "status:open"`, then `"status:failed"`.
- Reconciliation: `bexio_bank_accounts.get` → `bexio_accounting` journal. Read `references/payment-fields.md` for the account mapping and report fields. Matching: no API.
