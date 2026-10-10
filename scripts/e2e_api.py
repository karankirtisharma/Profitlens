"""Start an isolated synthetic API for browser tests; requires a _test database."""

import os

from sqlalchemy.engine import make_url


def main():
    url = os.environ.get("E2E_DATABASE_URL", "")
    if not url or not make_url(url).database.endswith("_test"):
        raise SystemExit(
            "Set E2E_DATABASE_URL to a dedicated PostgreSQL database ending in _test"
        )
    os.environ["DATABASE_URL"] = url
    web_port = int(os.environ.get("E2E_WEB_PORT", "3001"))
    api_port = int(os.environ.get("E2E_API_PORT", "8001"))
    os.environ["WEB_ORIGIN"] = f"http://localhost:{web_port}"
    os.environ["STORAGE_DIR"] = "data/private/e2e-uploads"
    from alembic import command
    from alembic.config import Config
    from profitlens.manage import seed_demo

    command.upgrade(Config("alembic.ini"), "head")
    seed_demo("browser-test-only-password")
    import uvicorn

    uvicorn.run("profitlens.main:app", host="127.0.0.1", port=api_port)


if __name__ == "__main__":
    main()
