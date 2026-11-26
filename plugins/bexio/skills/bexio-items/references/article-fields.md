# Item API lookup

## Tools
- `bexio_items`: list, search, get, create, update, delete. Scopes `article_show` / `article_edit`.
- `bexio_stock`: list_locations, search_locations, list_areas, search_areas (read-only).

## Items (`/2.0/article`, integer ids)
- `article_type_id`: 1 physical product, 2 service.
- Fields: `intern_code`, `intern_name`, `intern_description`, `currency_id`, `tax_income_id`, `tax_expense_id`, `unit_id`, `account_id`, `expense_account_id`, `article_group_id`, `contact_id`, `deliverer_code`, `remarks`, dimensions.
- `purchase_price`, `sale_price`: decimal strings, max 6 decimals · totals (`purchase_total`, `sale_total`): numbers.
- `html_text` deprecated.
- `update` = POST, changed fields.
- Search fields `intern_name`, `intern_code` · `order_by` id, intern_name.

## Stock locations + areas (read-only)
- `list_locations` / `search_locations` (`name`) · `list_areas` / `search_areas` (`name`, `stock_id`) · no write endpoints.
