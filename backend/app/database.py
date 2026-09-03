import logging

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.schema import CreateColumn
from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# Handle different database URLs for production (PostgreSQL) vs dev (SQLite)
db_url = settings.database_url
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+asyncpg://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# Render internal Postgres hosts do not require SSL; external public URLs do.
connect_args = {}
if db_url.startswith("postgresql+asyncpg://") and "render.com" in db_url and "dpg-" not in db_url:
    connect_args = {"ssl": "require"}

engine = create_async_engine(
    db_url,
    echo=settings.app_env == "development",
    connect_args=connect_args,
    pool_pre_ping=True,
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        yield session


def _reconcile_columns(sync_conn) -> list[str]:
    """Add columns that exist on the models but not yet in the database.

    `create_all` only ever CREATEs missing *tables* - it never ALTERs an
    existing one. So when a column is added to a model (as `users.email`,
    `google_sub`, `avatar_url` and `auth_provider` were), a database created
    before that change keeps the old table and every `SELECT users.*` fails
    with a ProgrammingError, while `SELECT 1 FROM users` still succeeds.

    This walks the model metadata and issues an idempotent
    ALTER TABLE ... ADD COLUMN for anything missing. New columns are added
    without NOT NULL so the statement is safe on a table that already has
    rows; nullability is enforced by the application layer.
    """
    inspector = inspect(sync_conn)
    existing_tables = set(inspector.get_table_names())
    dialect = sync_conn.dialect
    applied: list[str] = []

    for table in Base.metadata.sorted_tables:
        if table.name not in existing_tables:
            continue  # create_all just made it, so it is already current
        present = {c["name"] for c in inspector.get_columns(table.name)}
        for column in table.columns:
            if column.name in present:
                continue

            # Render the column DDL the way this dialect spells it, then strip
            # the constraints that cannot be applied to a populated table.
            ddl = str(CreateColumn(column).compile(dialect=dialect)).strip()
            ddl = ddl.replace(" NOT NULL", "")
            for token in (" PRIMARY KEY", " UNIQUE"):
                ddl = ddl.replace(token, "")

            stmt = f'ALTER TABLE "{table.name}" ADD COLUMN {ddl}'
            sync_conn.execute(text(stmt))
            applied.append(f"{table.name}.{column.name}")

            # Re-apply a unique index separately; it is allowed post-hoc and
            # is what the model actually relies on for lookups.
            if column.unique:
                idx = f"ix_uq_{table.name}_{column.name}"
                sync_conn.execute(
                    text(
                        f'CREATE UNIQUE INDEX IF NOT EXISTS "{idx}" '
                        f'ON "{table.name}" ("{column.name}")'
                    )
                )
            elif column.index:
                idx = f"ix_{table.name}_{column.name}"
                sync_conn.execute(
                    text(
                        f'CREATE INDEX IF NOT EXISTS "{idx}" '
                        f'ON "{table.name}" ("{column.name}")'
                    )
                )

    return applied


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        added = await conn.run_sync(_reconcile_columns)

    if added:
        logger.warning(
            "Schema drift repaired - added missing columns: %s", ", ".join(added)
        )
    else:
        logger.info("Schema is up to date")
