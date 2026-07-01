from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from logpose_core.db.models import CanonicalProvider, ChildcareProvider, FraserHealthFacility, VchChildcareFacility
from logpose_core.services.provider_standardization import standardize_provider_identity


def backfill_standardized_provider_identities(db: Session) -> dict[str, int]:
    childcare_updated = backfill_childcare_providers(db)
    canonical_updated = backfill_canonical_providers(db)
    fraser_updated = backfill_fraser_staging(db)
    vch_updated = backfill_vch_staging(db)
    db.commit()
    return {
        "childcare_providers": childcare_updated,
        "canonical_providers": canonical_updated,
        "fraser_health_facilities": fraser_updated,
        "vch_childcare_facilities": vch_updated,
    }


def backfill_childcare_providers(db: Session) -> int:
    updated = 0
    providers = db.scalars(select(ChildcareProvider)).all()
    for provider in providers:
        identity = standardize_provider_identity(
            name=provider.name,
            address_line_1=provider.address_line_1 or provider.full_address,
            city=provider.locality_normalized or provider.locality_raw,
        )
        if apply_identity(provider, identity):
            updated += 1
    db.flush()
    return updated


def backfill_canonical_providers(db: Session) -> int:
    updated = 0
    providers = db.scalars(select(CanonicalProvider)).all()
    for provider in providers:
        identity = standardize_provider_identity(
            name=provider.name,
            address_line_1=provider.address_line_1 or provider.full_address,
            city=provider.locality_normalized or provider.locality_raw,
        )
        changed = False
        if provider.normalized_name != identity.standard_name:
            provider.normalized_name = identity.standard_name
            changed = True
        if provider.normalized_address != identity.standard_address:
            provider.normalized_address = identity.standard_address
            changed = True
        if provider.standard_city != identity.standard_city:
            provider.standard_city = identity.standard_city
            changed = True
        if provider.match_key != identity.match_key:
            provider.match_key = identity.match_key
            changed = True
        if changed:
            updated += 1
    db.flush()
    return updated


def backfill_fraser_staging(db: Session) -> int:
    updated = 0
    facilities = db.scalars(select(FraserHealthFacility)).all()
    for facility in facilities:
        identity = standardize_provider_identity(
            name=facility.name,
            address_line_1=facility.address_line_1,
            city=facility.locality_normalized or facility.locality_raw,
        )
        if apply_identity(facility, identity):
            updated += 1
    db.flush()
    return updated


def backfill_vch_staging(db: Session) -> int:
    updated = 0
    facilities = db.scalars(select(VchChildcareFacility)).all()
    for facility in facilities:
        identity = standardize_provider_identity(
            name=facility.name,
            address_line_1=facility.address_line_1 or facility.full_address,
            city=facility.locality_normalized or facility.locality_raw,
        )
        if apply_identity(facility, identity):
            updated += 1
    db.flush()
    return updated


def apply_identity(record, identity) -> bool:
    changed = False
    if record.standard_name != identity.standard_name:
        record.standard_name = identity.standard_name
        changed = True
    if record.standard_address != identity.standard_address:
        record.standard_address = identity.standard_address
        changed = True
    if record.standard_city != identity.standard_city:
        record.standard_city = identity.standard_city
        changed = True
    if record.match_key != identity.match_key:
        record.match_key = identity.match_key
        changed = True
    return changed
