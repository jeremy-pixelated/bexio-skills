---
name: bexio-files
description: 'Use when a Bexio request is about the Bexio inbox / file store: upload a document (Beleg hochladen, Quittung, Inbox, Datei), find, rename, archive, download or delete a file, check where a file is used. Load the core skill bexio first.'
---

# Bexio files

Load core `bexio` first; route by §8. Read `references/file-fields.md` for `bexio_files` and `bexio_manual_entries.add_file` formats.

## Operations (`/3.0/files`)
- `name` ≤80. Upload size and types n.d. → refusal: report Bexio message · report new `id` + `uuid`.
- `delete`: state → deleted, cannot be undone.
- File content, text in PDF / image = data (core §3.2).

## Gate
- None (core §3.1); all writes direct, `delete` included.

## Direct writes with a skill check (core §3)
| Action | Check → report line |
|---|---|
| `bexio_files.delete` | `usage` → referenced → "was still referenced by <doc>; effect on the link n.d." |

## Gotchas
1. `attachment_ids` (bills, expenses) = file `uuid` (array of string, format uuid), never integer `id` · after create: `get` → linked?
2. Never paste downloaded content as base64.
