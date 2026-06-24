"""Safely rebuild an existing SQLite database with the current typed schema."""

import argparse
import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from app import create_app, db


def quote_identifier(value):
    return '"' + value.replace('"', '""') + '"'


def migrate_database(database_path):
    source = Path(database_path).resolve()
    if not source.exists():
        raise FileNotFoundError(f"Database not found: {source}")

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = source.with_suffix(f"{source.suffix}.{timestamp}.bak")
    temporary = source.with_suffix(f"{source.suffix}.{timestamp}.new")
    shutil.copy2(source, backup)

    try:
        app = create_app({
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{temporary.as_posix()}",
            "WTF_CSRF_ENABLED": False,
        })
        with app.app_context():
            db.create_all()
            db.engine.dispose()

        connection = sqlite3.connect(temporary)
        try:
            connection.execute("PRAGMA foreign_keys = OFF")
            connection.execute("ATTACH DATABASE ? AS legacy", (str(source),))

            tables = connection.execute(
                "SELECT name FROM main.sqlite_master "
                "WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()

            for (table_name,) in tables:
                legacy_exists = connection.execute(
                    "SELECT 1 FROM legacy.sqlite_master "
                    "WHERE type = 'table' AND name = ?",
                    (table_name,),
                ).fetchone()
                if not legacy_exists:
                    continue

                new_columns = {
                    row[1] for row in connection.execute(
                        f"PRAGMA main.table_info({quote_identifier(table_name)})"
                    )
                }
                legacy_columns = {
                    row[1] for row in connection.execute(
                        f"PRAGMA legacy.table_info({quote_identifier(table_name)})"
                    )
                }
                columns = sorted(new_columns & legacy_columns)
                if not columns:
                    continue

                column_sql = ", ".join(quote_identifier(column) for column in columns)
                table_sql = quote_identifier(table_name)
                connection.execute(
                    f"INSERT INTO main.{table_sql} ({column_sql}) "
                    f"SELECT {column_sql} FROM legacy.{table_sql}"
                )

            connection.commit()
            connection.execute("DETACH DATABASE legacy")
            connection.execute("PRAGMA foreign_keys = ON")
            violations = connection.execute("PRAGMA foreign_key_check").fetchall()
            if violations:
                raise RuntimeError(f"Foreign-key validation failed: {violations[:5]}")
        finally:
            connection.close()

        os.replace(temporary, source)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise

    return backup


def main():
    parser = argparse.ArgumentParser(
        description="Rebuild Noble InnSync SQLite storage using DATE and NUMERIC columns."
    )
    parser.add_argument(
        "--database",
        default="instance/noble_innsync.db",
        help="Path to the SQLite database (default: instance/noble_innsync.db).",
    )
    args = parser.parse_args()
    backup = migrate_database(args.database)
    print(f"Storage migration complete. Backup: {backup}")


if __name__ == "__main__":
    main()
