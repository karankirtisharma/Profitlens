# Deployment preparation and recovery

The repository contains `Dockerfile.api`, `apps/web/Dockerfile` and `compose.deploy.yaml`. The standalone Next.js build is locally verified. Docker is unavailable in the current environment, so image builds, Compose startup, target-host networking and public deployment **remain unverified**. These files are preparation, not evidence of a deployed service.

## Before deploying

- Provision PostgreSQL 17, persistent private PDF storage and an HTTPS reverse proxy. Only the web service is published, bound to loopback for the proxy. Do not expose PostgreSQL or FastAPI directly.
- Use strong local secrets in `.env`; set `POSTGRES_PASSWORD`, `DEPLOY_DATABASE_URL` (host `db`, port 5432, URL-encoded password) and exact `DEPLOY_WEB_ORIGIN=https://your-host`. Compose forces secure cookies. The example is intended for HTTPS; do not disable secure cookies to work around a production proxy issue.
- Optional AI keys belong only to the API container. The web build receives only its internal API URL. Check provider model/schema support, account limits and data handling before enabling external calls.
- Run `docker compose -f compose.deploy.yaml config --quiet`, then `docker compose -f compose.deploy.yaml up --build -d` in the target environment. Avoid printing expanded Compose configuration because it contains secrets.
- The API applies Alembic migrations before starting a single worker. For multiple replicas, move migration to a one-time deployment job. No schema recreation or automatic synthetic seeding occurs at server startup.
- After startup, verify health, HTTPS cookie flags, login, imports, private PDF access, customer revocation, analysis, provider failure, backup and restore. Account provisioning uses the explicit management CLI; no public registration exists. For a synthetic demonstration only, run `python -m profitlens.manage seed-demo` explicitly inside the API container with a locally supplied password.

The database and private files use separate named volumes. They must be backed up together; deleting either volume loses application data. Runtime users are non-root. Container tags are major-version tags, not immutable digests; pin tested digests as part of a real release. Dependency vulnerability review and external deployment/security validation remain release tasks.

## Migration and backup

`20261015_roadmap` is additive: it creates cost reviews, document passages and investigations without changing existing business rows. Run `alembic check` after upgrade. Older contracts can be indexed through the authorized **Index existing contracts** action.

Before upgrading, create a custom-format `pg_dump` backup and copy private PDF storage into an access-restricted backup location. Use the local password file or process environment for credentials; never place a password in a recorded shell command or source repository. Verify the backup with `pg_restore --list`, then restore into a **new isolated database** and check counts, source downloads and integrity. A database dump alone does not back up the PDFs.

Rollback removes new analysis tables and their contents. Do not downgrade a live database with saved investigations without an explicit backup/rollback decision. The unchanged Week 4 `/finance` endpoint remains available alongside the new endpoint.

## Operational limits

This is a bounded single-workspace-analysis prototype, not a production security certification. No OCR, SSO/MFA, password-reset workflow, retention/deletion policy, cloud object storage or external monitoring is implemented. Customer selectors show the first 200 customers. Retrieval is in-process BM25 over at most 2000 authorized passages; there is no vector extension, GPU or pretrained embedding model. Provider calls have bounded timeout/output and a workspace rate limit, but no distributed job queue. Review storage growth and provider spending separately.

Vercel can host the web frontend when its same-origin API forwarding is configured at build time. The Python API, persistent PostgreSQL and private file storage require their own persistent hosting; deploying this entire repository as a static Vercel site is insufficient.
