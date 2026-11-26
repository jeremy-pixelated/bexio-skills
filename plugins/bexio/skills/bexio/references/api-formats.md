# API formats

- Per-op detail (299 ops: path, tool.action, gate, required fields, enums, scopes, anchor) → segment `reference.md`.

## 5. API conventions

| Family | Areas | Ids | Paging | Search |
|---|---|---|---|---|
| 2.0 | contacts, sales docs, positions, items, projects, timesheets, notes, tasks, master data, accounts | integer | `limit` (default 500, max 2000) + `offset` | `search` + `search_criteria` |
| 3.0 | accounting, currencies, taxes, files, bank accounts, users, purchase orders, milestones | integer (+ `uuid`) | `limit` + `offset` | files, accounts, calendar years |
| 4.0 purchase | bills, expenses, outgoing payments | UUID | `limit` (bills max 500) + `page` from 1 + `order` + `sort` | bills `search_term` 3 to 255 chars; filters |
| 4.0 banking | banking payments | UUID (+ int `id`) | `page` from 0 + `per_page` (max 2000) | `filter_by` `field:value;field:min_max` |
- `search_criteria` = `[{field, value, criteria}]`, several = AND. Criteria `=` `!=` `>` `<` `>=` `<=` `like` (default) `not_like` `is_null` `not_null` `in` `not_in`.
- Wire: dates `YYYY-MM-DD` · 2.0 money / qty = decimal strings, max 6 decimals (`"10.0000"`) · 4.0 purchase amounts = numbers, max 2 decimals · manual-entry amounts = numbers, booked gross incl. VAT · 2.0 datetimes `2019-04-08 13:17:32`, 3.0 / 4.0 ISO 8601.
- Error body `{"error_code", "message"}`.
