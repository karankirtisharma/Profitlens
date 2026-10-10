# Workspace access and import guarantees

## Access model

| Role | Business records and PDF evidence | CSV imports and term review | Customer assignments |
| --- | --- | --- | --- |
| Admin | All within own organization | Allowed | Allowed |
| Finance | All within own organization | Allowed | Denied |
| Analyst | Assigned customers only, read-only | Denied | Denied |

Every request resolves the session, organization membership and current role on the server. Analyst customer grants are applied in SQL before records are returned; a direct URL or guessed ID cannot bypass the checks. PDF downloads use the same authorization path. Cross-organization requests return 404. Membership/grant changes take effect on subsequent requests. There is no PostgreSQL RLS in this release: API scoping and composite relational constraints enforce the boundary; direct database access is administrative access.

Sessions use random 256-bit tokens, Argon2 password hashes, HttpOnly/SameSite cookies, an expiry and logout revocation. Mutating requests must carry the configured `Origin`, including login/logout, to prevent cross-site submission. Failed logins are limited to five attempts per email in 15 minutes, stored transactionally in PostgreSQL. This local account model deliberately has no public registration or automatic invitation flow.

## CSV preview and confirmation

The [data contracts](DATA_CONTRACTS.md) still define input columns. Upload one CSV type at a time; create/import customers first. The authenticated workspace determines organization scope, never an uploaded column. The server also enforces workspace currency, supported ID characters, length/amount bounds and references.

1. **Preview:** preserve the SHA-256 fingerprint, original filename, validated rows, row numbers, issues and creator. States are `ready` or `invalid`. This persists an import batch only, not business records. The interface displays at most ten preview rows but validates all rows.
2. **Confirm:** lock the workspace and import batch, recheck all rows against current data, and insert records in one PostgreSQL transaction. Success is sent only after commit. A validation error or failed transaction writes no partial business records.
3. **Retry:** the same organization/type/fingerprint returns the original confirmed batch. Concurrent confirmations serialize. For a different file, an identical existing record is skipped; the same ID with different values is rejected. Imports never silently overwrite existing business records.
4. **Trace:** imported records retain file, row, batch ID and fingerprint. Manual corrections keep original provenance and append an actor/time/snapshot audit event. IDs cannot be changed through the editor.

Persistent IDs are unique per organization. There is one canonical source-ID namespace per record type in this release; separate source-system namespaces are a later extension. Record IDs contain 1–80 letters, digits, dots, underscores or hyphens and begin with a letter or digit. Amounts use decimal arithmetic, PostgreSQL `NUMERIC(14,2)`, and decimal strings in JSON responses; browser formatting is display-only.

## Contracts

PDF uploads are limited to 10 MiB and 100 pages and must contain selectable text. Storage keys are generated server-side; uploaded filenames are metadata, not filesystem paths. Each contract is linked through a composite organization/customer foreign key. Re-uploading identical bytes for the same customer returns the existing contract.

Extracted pages are evidence, not verified terms. A finance/admin user must review the effective dates, fixed monthly rate and discount, currency and source page. The server rejects negative amounts, discount above rate, end dates before start dates, an unavailable source page, and overlapping reviewed contract periods for one customer. The reviewer and review timestamp are retained. Only fixed monthly billing is supported; no model infers or approves terms.

The test suite covers guessed IDs, other organizations, unassigned customers, revoked grants, private file reads, malformed and conflicting imports, simultaneous retry, mid-transaction failure, failed commit and decimal serialization. These checks establish prototype behavior, not a claim of a full security audit.
