from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from logpose_core.db.models import CanonicalProvider, ChildcareProvider
from logpose_core.services.provider_ingestion import attach_to_canonical_provider, source_sort_key


def rebuild_canonical_providers(db: Session) -> dict[str, int]:
    source_provider_count = db.scalar(select(func.count()).select_from(ChildcareProvider))
    if not source_provider_count:
        return {"source_providers": 0, "canonical_providers": 0}

    db.execute(update(ChildcareProvider).values(canonical_provider_id=None))
    db.execute(delete(CanonicalProvider))
    db.flush()

    imported_at = datetime.now(UTC)
    providers = db.scalars(select(ChildcareProvider)).all()
    providers.sort(key=source_sort_key)
    for provider in providers:
        attach_to_canonical_provider(db, source_provider=provider, imported_at=imported_at)

    db.commit()
    canonical_provider_count = db.scalar(select(func.count()).select_from(CanonicalProvider))
    return {
        "source_providers": int(source_provider_count or 0),
        "canonical_providers": int(canonical_provider_count or 0),
    }
