"""Create all tables from the current models. Simple approach for now
(no Alembic yet) — safe to re-run, only creates what's missing.

Run: python -m app.db.init_db
"""

from __future__ import annotations

from app.db.models import Base
from app.db.session import engine


def main() -> None:
    Base.metadata.create_all(engine)
    print("Tables created (or already existed): transactions, sync_log")


if __name__ == "__main__":
    main()
