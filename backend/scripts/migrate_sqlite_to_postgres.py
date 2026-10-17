#!/usr/bin/env python3
"""Copy the legacy trading history from SQLite into a migrated PostgreSQL database."""

import argparse
import sys
from pathlib import Path

from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import MetaData, create_engine, func, inspect, select, text
from sqlalchemy.engine import Connection

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from src.trading_system.config.settings import settings
from src.trading_system.database.models import Base


def _table_count(connection: Connection, table_name: str) -> int:
    table = Base.metadata.tables[table_name]
    return connection.execute(select(func.count()).select_from(table)).scalar_one()


def migrate(source_path: Path, destination_url: str) -> dict[str, int]:
    source_path = source_path.expanduser().resolve()
    if not source_path.is_file():
        raise FileNotFoundError(f"SQLite source database does not exist: {source_path}")

    destination_engine = create_engine(destination_url)
    source_engine = create_engine(f"sqlite:///{source_path}")
    expected_tables = tuple(table.name for table in Base.metadata.sorted_tables)

    try:
        if destination_engine.dialect.name != "postgresql":
            raise ValueError("The destination DATABASE_URL must use PostgreSQL.")

        config_path = BACKEND_ROOT / "alembic.ini"
        config = Config(str(config_path))
        config.set_main_option("script_location", str(BACKEND_ROOT / "migrations"))
        expected_revision = ScriptDirectory.from_config(config).get_current_head()

        source_tables = set(inspect(source_engine).get_table_names())
        missing_source_tables = set(expected_tables) - source_tables
        if missing_source_tables:
            missing = ", ".join(sorted(missing_source_tables))
            raise RuntimeError(f"SQLite source is missing required tables: {missing}")

        source_metadata = MetaData()
        source_metadata.reflect(bind=source_engine, only=expected_tables)
        with source_engine.connect() as source_connection:
            source_counts = {
                name: _table_count(source_connection, name) for name in expected_tables
            }
            for table_name in expected_tables:
                source_columns = {
                    column.name for column in source_metadata.tables[table_name].columns
                }
                destination_columns = {
                    column.name for column in Base.metadata.tables[table_name].columns
                }
                if source_columns != destination_columns:
                    raise RuntimeError(
                        f"Column mismatch for {table_name}; source and destination "
                        "schemas must match before data transfer."
                    )

            with destination_engine.begin() as destination_connection:
                current_revision = MigrationContext.configure(
                    destination_connection
                ).get_current_revision()
                if current_revision != expected_revision:
                    raise RuntimeError(
                        f"PostgreSQL schema is at {current_revision or 'uninitialized'}; "
                        f"expected {expected_revision}. Run `alembic upgrade head` first."
                    )

                destination_tables = set(inspect(destination_connection).get_table_names())
                missing_destination_tables = set(expected_tables) - destination_tables
                if missing_destination_tables:
                    missing = ", ".join(sorted(missing_destination_tables))
                    raise RuntimeError(
                        f"PostgreSQL database is missing required tables: {missing}"
                    )

                destination_counts = {
                    name: _table_count(destination_connection, name)
                    for name in expected_tables
                }
                nonempty_destination = {
                    name: count
                    for name, count in destination_counts.items()
                    if count != 0
                }
                if nonempty_destination:
                    details = ", ".join(
                        f"{name}={count}"
                        for name, count in sorted(nonempty_destination.items())
                    )
                    raise RuntimeError(
                        "Refusing to copy into non-empty PostgreSQL tables: "
                        f"{details}. No destination data was changed."
                    )

                for table_name in expected_tables:
                    source_table = source_metadata.tables[table_name]
                    destination_table = Base.metadata.tables[table_name]
                    result = source_connection.execution_options(
                        stream_results=True
                    ).execute(select(source_table))
                    while rows := result.mappings().fetchmany(500):
                        destination_connection.execute(
                            destination_table.insert(),
                            [dict(row) for row in rows],
                        )

                for table_name in expected_tables:
                    destination_connection.execute(
                        text(
                            "SELECT setval("
                            "pg_get_serial_sequence(:table_name, 'id'), "
                            f"COALESCE((SELECT MAX(id) FROM {table_name}), 1), "
                            f"(SELECT MAX(id) FROM {table_name}) IS NOT NULL)"
                        ),
                        {"table_name": f"public.{table_name}"},
                    )

                destination_counts = {
                    name: _table_count(destination_connection, name)
                    for name in expected_tables
                }
                if destination_counts != source_counts:
                    raise RuntimeError(
                        f"Row count verification failed: source={source_counts}, "
                        f"destination={destination_counts}"
                    )

        return destination_counts
    finally:
        source_engine.dispose()
        destination_engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=BACKEND_ROOT / "trading_system.db",
        help="SQLite database to copy (default: backend/trading_system.db).",
    )
    args = parser.parse_args()

    counts = migrate(args.source, settings.DATABASE_URL)
    print("SQLite history copied and verified:")
    for table_name, count in sorted(counts.items()):
        print(f"  {table_name}: {count} rows")


if __name__ == "__main__":
    main()
