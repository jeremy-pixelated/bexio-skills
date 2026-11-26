# File API lookup

## Tools
- `bexio_files`: list, search, get, download, preview, usage, upload, update, delete.
- Scope `file` = read + write together.

## Operations (`/3.0/files`)
- `list`: `archived_state` (`all`, `archived`, `not_archived`), `offset`, `order_by` id, created_at, source_id, uuid, name, size_in_bytes · no `limit` → page with `offset` (`search` takes `limit` + `offset`).
- `search` fields: id, uuid, created_at, name, extension, size_in_bytes, mime_type, user_id, is_archived, source_id.
- Fields: `id` (integer), `uuid`, `name` (≤80), `size_in_bytes`, `extension`, `mime_type`, `uploader_email`, `user_id`, `is_archived`, `source_type` (`web`, `email`, `mobile`), `is_referenced`, `created_at`.
- `bexio_manual_entries.add_file`: own multipart upload, no file id.
- `upload`: `content_base64` + `file_name` (with extension) → one multipart field `file`.
- `update` (PATCH): `name`, `is_archived` (reversible alternative to delete), `source_type`.
- `download` / `preview` stream file · `usage` → where used (`ref_class`, `title`, `document_nr`).
