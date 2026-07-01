#!/usr/bin/env python3
"""Initialize database tables from SQLAlchemy models."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import inspect, text

from logpose_core.db.base import Base
from logpose_core.db.session import engine
from logpose_core.db import models  # noqa: F401
from logpose_core.db.session import SessionLocal
from logpose_core.db.models import CanonicalProvider, ChildcareProvider
from logpose_core.services.canonical_backfill import rebuild_canonical_providers
from logpose_core.services.provider_standardization_backfill import backfill_standardized_provider_identities


ADDITIVE_CHILDCARE_PROVIDER_COLUMNS = {
    "canonical_provider_id": "UUID NULL",
    "standard_name": "TEXT NULL",
    "standard_address": "TEXT NULL",
    "standard_city": "TEXT NULL",
    "match_key": "TEXT NULL",
    "manager_name": "TEXT NULL",
    "licensed_capacity": "INTEGER NULL",
    "service_capacity": "JSONB NULL",
    "health_authority": "TEXT NULL",
}

ADDITIVE_CANONICAL_PROVIDER_COLUMNS = {
    "standard_city": "TEXT NULL",
    "vch_disclosure_program_id": "TEXT NULL",
    "vch_facility_id": "TEXT NULL",
    "vch_inspection_reports_url": "TEXT NULL",
    "vch_last_inspection_date": "DATE NULL",
    "vch_inspection_count": "INTEGER NULL",
    "vch_outstanding_critical_infractions": "INTEGER NULL",
    "vch_outstanding_noncritical_infractions": "INTEGER NULL",
}

ADDITIVE_FRASER_HEALTH_FACILITY_COLUMNS = {
    "standard_name": "TEXT NULL",
    "standard_address": "TEXT NULL",
    "standard_city": "TEXT NULL",
    "match_key": "TEXT NULL",
}


def init_db(*, drop_existing: bool = False) -> None:
    """Create all tables defined in models."""
    if drop_existing:
        print("Dropping existing tables...")
        Base.metadata.drop_all(bind=engine)
    
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    apply_additive_schema_updates()
    backfill_canonical_if_needed()
    backfill_standardized_identities()
    print("Database initialized successfully.")


def apply_additive_schema_updates() -> None:
    """Apply simple in-place additive schema changes for existing dev databases."""
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    with engine.begin() as connection:
        add_missing_columns(
            connection=connection,
            inspector=inspector,
            table_names=table_names,
            table_name="childcare_providers",
            columns=ADDITIVE_CHILDCARE_PROVIDER_COLUMNS,
        )
        add_missing_columns(
            connection=connection,
            inspector=inspector,
            table_names=table_names,
            table_name="canonical_providers",
            columns=ADDITIVE_CANONICAL_PROVIDER_COLUMNS,
        )
        add_missing_columns(
            connection=connection,
            inspector=inspector,
            table_names=table_names,
            table_name="fraser_health_facilities",
            columns=ADDITIVE_FRASER_HEALTH_FACILITY_COLUMNS,
        )


def add_missing_columns(*, connection, inspector, table_names: set[str], table_name: str, columns: dict[str, str]) -> None:
    if table_name not in table_names:
        return
    existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
    for column_name, column_sql in columns.items():
        if column_name in existing_columns:
            continue
        connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}"))


def backfill_canonical_if_needed() -> None:
    """Populate canonical providers from existing source providers when needed."""
    db = SessionLocal()
    try:
        source_provider_count = db.query(ChildcareProvider).count()
        canonical_provider_count = db.query(CanonicalProvider).count()
        if source_provider_count > 0 and canonical_provider_count == 0:
            print("Backfilling canonical providers from existing source providers...")
            result = rebuild_canonical_providers(db)
            print(
                f"Backfilled {result['canonical_providers']} canonical providers from "
                f"{result['source_providers']} source providers."
            )
    finally:
        db.close()


def backfill_standardized_identities() -> None:
    db = SessionLocal()
    try:
        result = backfill_standardized_provider_identities(db)
        if any(result.values()):
            print(
                "Backfilled standardized identities: "
                f"{result['childcare_providers']} source providers, "
                f"{result['canonical_providers']} canonical providers, "
                f"{result['fraser_health_facilities']} Fraser staged facilities, "
                f"{result['vch_childcare_facilities']} VCH staged facilities."
            )
    finally:
        db.close()


if __name__ == "__main__":
    drop = "--drop" in sys.argv
    if drop:
        confirm = input("This will drop all existing tables. Continue? (yes/no): ")
        if confirm.lower() != "yes":
            print("Aborted.")
            sys.exit(1)
    
    init_db(drop_existing=drop)
