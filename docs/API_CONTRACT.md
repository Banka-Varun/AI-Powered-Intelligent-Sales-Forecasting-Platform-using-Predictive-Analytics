Base URL for local use: `http://127.0.0.1:8000`. Version 0.1.0. Agree with the frontend and database owners before integration.

| Method | Path | Request | Success |
|---|---|---|---|
| GET | /health | None | 200 status/database |
| POST | /leads | LeadCreate JSON | 201 saved lead |
| GET | /leads | Optional q, stage, offset=0, limit=20 | 200 items,total,offset,limit |
| GET | /leads/{id} | Integer ID | 200 saved lead |
| PATCH | /leads/{id} | At least one changed field | 200 saved lead |
| DELETE | /leads/{id} | Integer ID | 204 empty body |
| POST | /leads/import | multipart file field named file | 200 imported,duplicates,rejected,issues |

LeadCreate: name (1-120 chars), email (valid, max 254 chars), company (1-160 chars), optional phone (null or up to 40 chars), stage defaults to new. Proposed stages: new/contacted/qualified/won/lost. Any listed stage can replace another; no transition restrictions are specified yet. Phone is length-checked only, not verified as a telephone number.

Output adds integer id and created_at/updated_at timestamps (UTC intent; SQLite may return timestamps without an offset). The email is stripped and lowercased, then stored with a database unique constraint. Duplicate rule is EMAIL ONLY; this does not detect the same person using different emails.

PATCH accepts any subset. Null may clear phone; name/email/company/stage cannot be null. Unknown fields and empty updates are rejected. Search is a case-insensitive literal substring over name, email and company. Stage filtering is exact. Pagination is ordered by id, limit is 1-100, offset is non-negative.

CSV: UTF-8 (BOM allowed), exact headers name,email,company required, phone/stage optional. No extra or repeated headers. At most 2 MiB and 1000 data records. Blank optional stage means new. Duplicate emails (existing or repeated in the same file) and invalid rows are skipped and reported. `row` means data-record index + 2, not physical line number for multiline quoted cells. Valid rows commit together. Structural file errors reject the whole upload. A concurrent uniqueness conflict rejects/rolls back the valid-row batch with 409; retry after checking existing records.

Error statuses: 400 invalid file structure/encoding, 404 missing lead, 409 database conflict, 413 file/row limit, 422 validation, 503 database failure. Errors have a `detail` field; FastAPI validation errors use a detail list.

This local demo has no login/JWT/RBAC and no AI/CRM endpoints. Streamlit can make server-side HTTP requests; a browser-JavaScript frontend would need an explicit agreed CORS policy. Automatic docs are at /docs and the machine-readable schema is at /openapi.json.
