---
name: bexio-items
description: 'Use when a Bexio request is about the article master: items / products / services (Artikel, Produkt, Dienstleistung, Artikelstamm), their sale or purchase price fields, tax and account defaults, or Bexio stock locations and areas (Lager, Lagerort) — find, create, update or delete an article master record. Load the core skill bexio first.'
---

# Bexio items — articles, stock locations, stock areas

Core `bexio` first (router, gate, flags). All 10 ops: `reference.md`.

## Use / not here
- Find an article for a position (`article_id`), its accounts + taxes · create, update, delete.
- Not here: units list → `bexio-admin` · an article on a document position → `bexio-sales`.

## Tools
| Tool | Actions | Gated |
|---|---|---|
| `bexio_items` | list, search, get, create, update, delete | – |
| `bexio_stock` | list_locations, search_locations, list_areas, search_areas | – (read-only) |
- Scopes: items `article_show` / `article_edit`; `bexio_stock` needs `stock_edit` even to read [D:v2ListStockLocations].

## Items (`/2.0/article`, integer ids)
- Create: no field marked required [D:v2CreateItem]; minimum n.d. → send `intern_name`. Search `intern_code` `=` first; create only without match.
- `article_type_id`: 1 physical product, 2 service; fixed after create [D:v2EditItem].
- Fields: `intern_code`, `intern_name`, `intern_description`, `purchase_price`, `sale_price` (decimal strings, max 6 decimals), `currency_id`, `tax_income_id`, `tax_expense_id`, `unit_id`, `account_id`, `expense_account_id`, `article_group_id`, `contact_id`, `deliverer_code`, `remarks`, dimensions.
- `is_stock` needs `stock_edit`; `stock_nr` only before the first stock booking; `html_text` deprecated [D:v2CreateItem], [D§Changelog].
- `update` = POST with changed fields.
- Search fields `intern_name`, `intern_code`; `order_by` id, intern_name [D:v2SearchItems].
- Delete permanent [D:DeleteItem].

## Stock locations + areas (read-only)
- `list_locations` / `search_locations` (`name`), `list_areas` / `search_areas` (`name`, `stock_id`). No write endpoints [D:v2ListStockLocations], [D:v2ListStockAreas].

## Gate
- No gated action here (core §3.1). `bexio_items.delete` runs directly on the user's request → report id, `intern_code`, `intern_name`.

## Gotchas
1. Stock locations: read needs `stock_edit`.
2. `article_type_id` fixed after create → create the right type.
3. Prices strings, totals (`purchase_total`, `sale_total`) numbers.

---
Sources: https://docs.bexio.com/ (OpenAPI 3.0.2; ops cited above; full list `reference.md`; §Changelog), fetched 2026-09-24.
