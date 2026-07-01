from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Literal

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import Session

from logpose_core.db.models import CanonicalProvider, ChildcareProvider
from logpose_core.services.provider_ingestion import source_sort_key


AgeGroup = Literal[
    "under_36_months",
    "30_months_to_5_years",
    "licensed_preschool",
    "oos_kindergarten",
    "oos_grade_1_to_12",
]
Language = Literal["cantonese", "punjabi", "mandarin", "french", "spanish", "other"]
Vacancy = Literal["reported", "none", "unknown"]
Sort = Literal["distance", "name", "locality", "recent"]


AGE_GROUP_COLUMNS = {
    "under_36_months": CanonicalProvider.serves_under_36_months,
    "30_months_to_5_years": CanonicalProvider.serves_30_months_to_5_years,
    "licensed_preschool": CanonicalProvider.serves_licensed_preschool,
    "oos_kindergarten": CanonicalProvider.serves_oos_kindergarten,
    "oos_grade_1_to_12": CanonicalProvider.serves_oos_grade_1_to_12,
}

LANGUAGE_COLUMNS = {
    "cantonese": CanonicalProvider.language_cantonese,
    "punjabi": CanonicalProvider.language_punjabi,
    "mandarin": CanonicalProvider.language_mandarin,
    "french": CanonicalProvider.language_french,
    "spanish": CanonicalProvider.language_spanish,
    "other": CanonicalProvider.language_other,
}


@dataclass(frozen=True)
class ProviderSearchResult:
    items: list[dict]
    total: int
    limit: int
    offset: int


def search_providers(
    db: Session,
    *,
    q: str | None = None,
    locality: list[str] | None = None,
    service_type: str | None = None,
    age_group: list[AgeGroup] | None = None,
    language: list[Language] | None = None,
    vacancy: Vacancy | None = None,
    ccfri_authorized: bool | None = None,
    open_weekends: bool | None = None,
    open_overnight: bool | None = None,
    open_before_6am_weekdays: bool | None = None,
    open_after_7pm_weekdays: bool | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_km: float | None = None,
    sort: Sort = "name",
    limit: int = 50,
    offset: int = 0,
) -> ProviderSearchResult:
    distance_expr = build_distance_expr(latitude=latitude, longitude=longitude)
    filters = build_filters(
        q=q,
        locality=locality,
        service_type=service_type,
        age_group=age_group,
        language=language,
        vacancy=vacancy,
        ccfri_authorized=ccfri_authorized,
        open_weekends=open_weekends,
        open_overnight=open_overnight,
        open_before_6am_weekdays=open_before_6am_weekdays,
        open_after_7pm_weekdays=open_after_7pm_weekdays,
        distance_expr=distance_expr,
        radius_km=radius_km,
    )

    total = db.scalar(select(func.count()).select_from(CanonicalProvider).where(*filters)) or 0

    stmt: Select = select(CanonicalProvider)
    if distance_expr is not None:
        stmt = select(CanonicalProvider, distance_expr.label("distance_km"))

    stmt = stmt.where(*filters)
    stmt = apply_sort(stmt, sort=sort, distance_expr=distance_expr)
    stmt = stmt.limit(limit).offset(offset)

    rows = db.execute(stmt).all()
    items = []
    for row in rows:
        if distance_expr is None:
            provider = row[0]
            distance_km = None
        else:
            provider = row[0]
            distance_km = float(row[1]) if row[1] is not None else None
        items.append(serialize_provider_summary(provider, distance_km=distance_km))

    return ProviderSearchResult(items=items, total=total, limit=limit, offset=offset)


def get_provider(db: Session, provider_id: uuid.UUID) -> dict | None:
    provider = db.get(CanonicalProvider, provider_id)
    if provider is None:
        return None
    sources = db.scalars(
        select(ChildcareProvider).where(ChildcareProvider.canonical_provider_id == provider.id)
    ).all()
    return serialize_provider_detail(provider, sources=sources)


def build_filters(
    *,
    q: str | None,
    locality: list[str] | None,
    service_type: str | None,
    age_group: list[AgeGroup] | None,
    language: list[Language] | None,
    vacancy: Vacancy | None,
    ccfri_authorized: bool | None,
    open_weekends: bool | None,
    open_overnight: bool | None,
    open_before_6am_weekdays: bool | None,
    open_after_7pm_weekdays: bool | None,
    distance_expr,
    radius_km: float | None,
) -> list:
    filters = []

    if q:
        pattern = f"%{q.strip()}%"
        filters.append(
            or_(
                CanonicalProvider.name.ilike(pattern),
                CanonicalProvider.full_address.ilike(pattern),
                CanonicalProvider.address_line_1.ilike(pattern),
                CanonicalProvider.locality_normalized.ilike(pattern),
            )
        )

    if locality:
        filters.append(func.lower(CanonicalProvider.locality_normalized).in_([item.lower() for item in locality]))

    if service_type:
        filters.append(CanonicalProvider.service_type.ilike(f"%{service_type.strip()}%"))

    if age_group:
        filters.append(and_(*(AGE_GROUP_COLUMNS[item] == "yes" for item in age_group)))

    if language:
        filters.append(and_(*(LANGUAGE_COLUMNS[item] == "yes" for item in language)))

    if vacancy == "reported":
        filters.append(CanonicalProvider.has_reported_vacancy == "yes")
    elif vacancy == "none":
        filters.append(CanonicalProvider.has_reported_vacancy == "no")
    elif vacancy == "unknown":
        filters.append(CanonicalProvider.has_reported_vacancy == "unknown")

    if ccfri_authorized is not None:
        filters.append(CanonicalProvider.is_ccfri_authorized.is_(ccfri_authorized))

    add_indicator_filter(filters, CanonicalProvider.open_weekends, open_weekends)
    add_indicator_filter(filters, CanonicalProvider.open_overnight, open_overnight)
    add_indicator_filter(filters, CanonicalProvider.open_before_6am_weekdays, open_before_6am_weekdays)
    add_indicator_filter(filters, CanonicalProvider.open_after_7pm_weekdays, open_after_7pm_weekdays)

    if radius_km is not None and distance_expr is not None:
        filters.append(distance_expr <= radius_km)

    return filters


def add_indicator_filter(filters: list, column, value: bool | None) -> None:
    if value is True:
        filters.append(column == "yes")
    elif value is False:
        filters.append(column == "no")


def build_distance_expr(*, latitude: float | None, longitude: float | None):
    if latitude is None or longitude is None:
        return None

    lat_delta = func.radians(CanonicalProvider.latitude - latitude)
    lon_delta = func.radians(CanonicalProvider.longitude - longitude)
    a = (
        func.pow(func.sin(lat_delta / 2), 2)
        + func.cos(func.radians(latitude))
        * func.cos(func.radians(CanonicalProvider.latitude))
        * func.pow(func.sin(lon_delta / 2), 2)
    )
    return 6371.0 * 2 * func.asin(func.sqrt(a))


def apply_sort(stmt: Select, *, sort: Sort, distance_expr) -> Select:
    if sort == "distance" and distance_expr is not None:
        return stmt.order_by(distance_expr.asc(), CanonicalProvider.name.asc())
    if sort == "locality":
        return stmt.order_by(CanonicalProvider.locality_normalized.asc(), CanonicalProvider.name.asc())
    if sort == "recent":
        return stmt.order_by(CanonicalProvider.imported_at.desc(), CanonicalProvider.name.asc())
    return stmt.order_by(CanonicalProvider.name.asc())


def serialize_provider_summary(provider: CanonicalProvider, *, distance_km: float | None = None) -> dict:
    return {
        "id": provider.id,
        "name": provider.name,
        "service_type": provider.service_type,
        "locality": provider.locality_normalized,
        "full_address": provider.full_address,
        "latitude": provider.latitude,
        "longitude": provider.longitude,
        "phone": provider.phone,
        "email": provider.email,
        "website_url": provider.website_url,
        "vch_inspection_reports_url": provider.vch_inspection_reports_url,
        "vch_last_inspection_date": provider.vch_last_inspection_date,
        "vch_inspection_count": provider.vch_inspection_count,
        "vch_outstanding_critical_infractions": provider.vch_outstanding_critical_infractions,
        "vch_outstanding_noncritical_infractions": provider.vch_outstanding_noncritical_infractions,
        "is_ccfri_authorized": provider.is_ccfri_authorized,
        "age_groups": serialize_age_groups(provider),
        "hours": serialize_hours(provider),
        "languages": serialize_languages(provider),
        "vacancy": serialize_vacancy(provider),
        "distance_km": round(distance_km, 2) if distance_km is not None else None,
        "imported_at": provider.imported_at,
        "updated_at": provider.updated_at,
    }


def serialize_provider_detail(provider: CanonicalProvider, *, sources: list[ChildcareProvider]) -> dict:
    data = serialize_provider_summary(provider)
    ordered_sources = sorted(sources, key=source_sort_key)
    primary_source = ordered_sources[0] if ordered_sources else None
    data.update(
        {
            "source_name": primary_source.source_name if primary_source else None,
            "source_facility_id": primary_source.source_facility_id if primary_source else None,
            "source_sequence_id": primary_source.source_sequence_id if primary_source else None,
            "address_line_1": provider.address_line_1,
            "address_line_2": provider.address_line_2,
            "postal_code": provider.postal_code,
            "locality_raw": provider.locality_raw,
            "programs_description": provider.programs_description,
            "provides_meals": provider.provides_meals,
            "provides_pickup": provider.provides_pickup,
            "accommodates_special_needs": provider.accommodates_special_needs,
            "aboriginal_programming": provider.aboriginal_programming,
            "ece_certification": provider.ece_certification,
            "hours_description": provider.hours_description,
            "languages_description": provider.languages_description,
            "is_multi_location": provider.is_multi_location,
            "source_last_updated_at": provider.source_last_updated_at,
            "created_at": provider.created_at,
            "manager_name": provider.manager_name,
            "licensed_capacity": provider.licensed_capacity,
            "service_capacity": provider.service_capacity_json,
            "health_authority": provider.health_authority,
            "vch_inspection_reports_url": provider.vch_inspection_reports_url,
            "vch_last_inspection_date": provider.vch_last_inspection_date,
            "vch_inspection_count": provider.vch_inspection_count,
            "vch_outstanding_critical_infractions": provider.vch_outstanding_critical_infractions,
            "vch_outstanding_noncritical_infractions": provider.vch_outstanding_noncritical_infractions,
            "sources": [
                {
                    "source_name": source.source_name,
                    "source_facility_id": source.source_facility_id,
                    "source_sequence_id": source.source_sequence_id,
                    "manager_name": source.manager_name,
                    "licensed_capacity": source.licensed_capacity,
                    "service_capacity": source.service_capacity_json,
                    "health_authority": source.health_authority,
                    "imported_at": source.imported_at,
                    "updated_at": source.updated_at,
                }
                for source in ordered_sources
            ],
        }
    )
    return data


def serialize_age_groups(provider: CanonicalProvider) -> dict[str, str]:
    return {
        "under_36_months": provider.serves_under_36_months,
        "30_months_to_5_years": provider.serves_30_months_to_5_years,
        "licensed_preschool": provider.serves_licensed_preschool,
        "oos_kindergarten": provider.serves_oos_kindergarten,
        "oos_grade_1_to_12": provider.serves_oos_grade_1_to_12,
    }


def serialize_hours(provider: CanonicalProvider) -> dict[str, str]:
    return {
        "weekdays": provider.open_weekdays,
        "weekends": provider.open_weekends,
        "stat_holidays": provider.open_stat_holidays,
        "overnight": provider.open_overnight,
        "before_6am_weekdays": provider.open_before_6am_weekdays,
        "after_7pm_weekdays": provider.open_after_7pm_weekdays,
    }


def serialize_languages(provider: CanonicalProvider) -> dict[str, str]:
    return {
        "cantonese": provider.language_cantonese,
        "punjabi": provider.language_punjabi,
        "mandarin": provider.language_mandarin,
        "french": provider.language_french,
        "spanish": provider.language_spanish,
        "other": provider.language_other,
    }


def serialize_vacancy(provider: CanonicalProvider) -> dict[str, object]:
    return {
        "reported": provider.has_reported_vacancy,
        "under_36_months": provider.vacancy_under_36_months,
        "30_months_to_5_years": provider.vacancy_30_months_to_5_years,
        "licensed_preschool": provider.vacancy_licensed_preschool,
        "oos_grade_1_to_12": provider.vacancy_oos_grade_1_to_12,
        "for_license": provider.vacancy_for_license,
        "reported_at": provider.vacancy_reported_at,
    }
