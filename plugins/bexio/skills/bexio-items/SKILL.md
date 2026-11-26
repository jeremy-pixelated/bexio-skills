---
name: bexio-items
description: 'Use when a Bexio request is about the article master: items / products / services (Artikel, Produkt, Dienstleistung, Artikelstamm), their sale or purchase price fields, tax and account defaults, Bexio stock locations and areas (Lager, Lagerort). Find, create, update or delete an article master record. Load the core skill bexio first.'
---

# Bexio items

Load core `bexio` first; route by §8. Read `references/article-fields.md` for `bexio_items` and `bexio_stock` fields and actions.

## Items (`/2.0/article`, integer ids)
- Create: no field marked required; minimum n.d. → send `intern_name` · search `intern_code` `=` first; create only without match.
- `article_type_id`: fixed after create → pick type at create.
- `purchase_price`, `sale_price`: max 6 decimals.
- `is_stock` needs `stock_edit` · `stock_nr` only before first stock booking.
- Delete permanent.

## Stock locations + areas (read-only)
- `bexio_stock` needs `stock_edit` even to read.

## Gate
- None (core §3.1). `bexio_items.delete` direct → report id, `intern_code`, `intern_name`.
