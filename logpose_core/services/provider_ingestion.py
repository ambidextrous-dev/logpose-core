from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from logpose_core.db.models import CanonicalProvider, ChildcareProvider, SourceRecord
from logpose_core.services.provider_standardization import standardize_provider_identity


SOURCE_PRECEDENCE = [
    "BC Child Care Map Data",
    "Fraser Health Licensed Child Care",
    "VCH Child Care Disclosure",
]

UNKNOWN_VALUE = "unknown"
YES_VALUE = "yes"
NO_VALUE = "no"


@dataclass(frozen=True)
class NormalizedProviderRecord:
    source_name: str
    source_record_id: str
    source_facility_id: str
    source_sequence_id: int | None
    source_last_updated_at: date | None
    health_authority: str | None
    name: str
    service_type: str | None
    address_line_1: str | None
    address_line_2: str | None
    postal_code: str | None
    locality_raw: str | None
    locality_normalized: str | None
    full_address: str | None
    latitude: float
    longitude: float
    phone: str | None
    email: str | None
    website_url: str | None
    manager_name: str | None
    licensed_capacity: int | None
    service_capacity: dict[str, int] | None
    is_ccfri_authorized: bool | None
    is_multi_location: bool | None
    serves_under_36_months: str
    serves_30_months_to_5_years: str
    serves_licensed_preschool: str
    serves_oos_kindergarten: str
    serves_oos_grade_1_to_12: str
    programs_description: str | None
    provides_meals: str | None
    provides_pickup: str | None
    accommodates_special_needs: str
    aboriginal_programming: str
    ece_certification: str
    open_weekdays: str
    open_weekends: str
    open_stat_holidays: str
    open_overnight: str
    open_before_6am_weekdays: str
    open_after_7pm_weekdays: str
    hours_description: str | None
    language_cantonese: str
    language_punjabi: str
    language_mandarin: str
    language_french: str
    language_spanish: str
    language_other: str
    languages_description: str | None
    has_reported_vacancy: str
    vacancy_under_36_months: str
    vacancy_30_months_to_5_years: str
    vacancy_licensed_preschool: str
    vacancy_oos_grade_1_to_12: str
    vacancy_for_license: str | None
    vacancy_reported_at: date | None

    def raw_identity(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "address_line_1": self.address_line_1,
            "address_line_2": self.address_line_2,
            "postal_code": self.postal_code,
            "locality_raw": self.locality_raw,
            "locality_normalized": self.locality_normalized,
            "full_address": self.full_address,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "phone": self.phone,
            "email": self.email,
            "website_url": self.website_url,
            "manager_name": self.manager_name,
            "licensed_capacity": self.licensed_capacity,
            "service_capacity": self.service_capacity,
            "health_authority": self.health_authority,
        }


def hash_payload(payload: dict[str, Any]) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    normalized = value.casefold().strip()
    normalized = normalized.replace("â€™", "'").replace("â€˜", "'")
    normalized = normalized.replace("'", "").replace("’", "")
    normalized = normalized.replace("&", " and ")
    normalized = re.sub(r"\bchild\s*care\b", "childcare", normalized)
    normalized = re.sub(r"\bcentre\b", "center", normalized)
    normalized = re.sub(r"\bfirst\b", "1", normalized)
    normalized = re.sub(r"\bsecond\b", "2", normalized)
    normalized = re.sub(r"\bthird\b", "3", normalized)
    normalized = re.sub(r"\bfourth\b", "4", normalized)
    normalized = re.sub(r"\bfifth\b", "5", normalized)
    normalized = re.sub(r"\bsixth\b", "6", normalized)
    normalized = re.sub(r"\bseventh\b", "7", normalized)
    normalized = re.sub(r"\beighth\b", "8", normalized)
    normalized = re.sub(r"\bninth\b", "9", normalized)
    normalized = re.sub(r"\btenth\b", "10", normalized)
    normalized = re.sub(r"\beleventh\b", "11", normalized)
    normalized = re.sub(r"\btwelfth\b", "12", normalized)
    normalized = re.sub(r"\bthirteenth\b", "13", normalized)
    normalized = re.sub(r"\bfourteenth\b", "14", normalized)
    normalized = re.sub(r"\bfifteenth\b", "15", normalized)
    normalized = re.sub(r"\bsixteenth\b", "16", normalized)
    normalized = re.sub(r"\bseventeenth\b", "17", normalized)
    normalized = re.sub(r"\beighteenth\b", "18", normalized)
    normalized = re.sub(r"\bnineteenth\b", "19", normalized)
    normalized = re.sub(r"\btwentieth\b", "20", normalized)
    normalized = re.sub(r"\bstreet\b", "st", normalized)
    normalized = re.sub(r"\bavenue\b", "ave", normalized)
    normalized = re.sub(r"\broad\b", "rd", normalized)
    normalized = re.sub(r"\bdrive\b", "dr", normalized)
    normalized = re.sub(r"\blane\b", "ln", normalized)
    normalized = re.sub(r"\bcourt\b", "ct", normalized)
    normalized = re.sub(r"\bcrt\b", "ct", normalized)
    normalized = re.sub(r"\bplace\b", "pl", normalized)
    normalized = re.sub(r"\bboulevard\b", "blvd", normalized)
    normalized = re.sub(r"\bcrescent\b", "cres", normalized)
    normalized = re.sub(r"\bhighway\b", "hwy", normalized)
    normalized = re.sub(r"\bterrace\b", "terr", normalized)
    normalized = re.sub(r"\bcircle\b", "cir", normalized)
    normalized = re.sub(r"\bparkway\b", "pkwy", normalized)
    normalized = re.sub(r"\b(\d+)(st|nd|rd|th)\b", r"\1", normalized)
    normalized = re.sub(r"\b(\d+)\s+(nd|rd|th)\b", r"\1", normalized)
    normalized = re.sub(r"[^a-z0-9# ]+", " ", normalized)
    normalized = re.sub(r"^(\d+)\s+(?:e|east|w|west|n|north|s|south)\s+(\d+)\b", r"\1 \2", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def normalize_address_text(value: str | None) -> str:
    normalized = normalize_text(value)
    if not normalized:
        return ""
    normalized = re.sub(r"\b(\d+)\s+([a-df-mo-rt-vx-z])\b", r"\1\2", normalized)

    tokens = normalized.split()
    while len(tokens) >= 4:
        if tokens[0].isdigit() and tokens[1].isdigit():
            first_number = int(tokens[0])
            second_number = int(tokens[1])
            if first_number < second_number:
                tokens = tokens[1:]
                continue
            if first_number <= 999 and second_number <= 999 and tokens[2] not in {"st", "ave", "rd", "dr", "hwy"}:
                tokens = tokens[1:]
                continue
        if re.fullmatch(r"[a-z]{1,4}\d*[a-z]?", tokens[0]) and tokens[1].isdigit():
            tokens = tokens[1:]
            continue
        break

    return " ".join(tokens)


def normalize_phone(value: str | None) -> str | None:
    if not value:
        return None
    digits = re.sub(r"\D+", "", value)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) < 10:
        return None
    return digits or None


def build_match_key(
    *,
    name: str,
    address_line_1: str | None,
    full_address: str | None,
    locality: str | None = None,
) -> tuple[str, str, str]:
    identity = standardize_provider_identity(
        name=name,
        address_line_1=address_line_1 or full_address,
        city=locality,
    )
    return identity.standard_name, identity.standard_address, identity.match_key


def upsert_source_record(
    db: Session,
    *,
    source_import_id: uuid.UUID,
    source_name: str,
    source_record_id: str,
    raw_record: dict[str, Any],
) -> tuple[SourceRecord, str]:
    payload_hash = hash_payload(raw_record)
    source_record = db.scalar(
        select(SourceRecord).where(
            SourceRecord.source_name == source_name,
            SourceRecord.source_record_id == source_record_id,
        )
    )

    if source_record is None:
        source_record = SourceRecord(
            source_import_id=source_import_id,
            source_name=source_name,
            source_record_id=source_record_id,
            raw_payload=raw_record,
            payload_hash=payload_hash,
        )
        db.add(source_record)
        db.flush()
        return source_record, "created"

    source_record.source_import_id = source_import_id
    if source_record.payload_hash != payload_hash:
        source_record.raw_payload = raw_record
        source_record.payload_hash = payload_hash
        return source_record, "updated"

    return source_record, "unchanged"


def upsert_source_provider(
    db: Session,
    *,
    record: NormalizedProviderRecord,
    source_record: SourceRecord,
    imported_at: datetime,
) -> tuple[ChildcareProvider, str]:
    provider_data = build_source_provider_data(record=record, source_record_id=source_record.id, imported_at=imported_at)
    provider = db.scalar(
        select(ChildcareProvider).where(
            ChildcareProvider.source_name == record.source_name,
            ChildcareProvider.source_facility_id == record.source_facility_id,
        )
    )

    if provider is None:
        provider = ChildcareProvider(**provider_data)
        db.add(provider)
        db.flush()
        return provider, "created"

    changed = False
    for key, value in provider_data.items():
        if key == "imported_at":
            continue
        if getattr(provider, key) != value:
            setattr(provider, key, value)
            changed = True

    if changed:
        provider.imported_at = imported_at
        provider.updated_at = imported_at
        db.flush()
        return provider, "updated"

    return provider, "unchanged"


def build_source_provider_data(
    *,
    record: NormalizedProviderRecord,
    source_record_id: uuid.UUID,
    imported_at: datetime,
) -> dict[str, Any]:
    identity = standardize_provider_identity(
        name=record.name,
        address_line_1=record.address_line_1 or record.full_address,
        city=record.locality_normalized or record.locality_raw,
    )
    return {
        "source_name": record.source_name,
        "source_facility_id": record.source_facility_id,
        "source_sequence_id": record.source_sequence_id,
        "source_record_ref": source_record_id,
        "standard_name": identity.standard_name,
        "standard_address": identity.standard_address,
        "standard_city": identity.standard_city,
        "match_key": identity.match_key,
        "name": record.name,
        "service_type": record.service_type,
        "address_line_1": record.address_line_1,
        "address_line_2": record.address_line_2,
        "postal_code": record.postal_code,
        "locality_raw": record.locality_raw,
        "locality_normalized": record.locality_normalized,
        "full_address": record.full_address,
        "latitude": record.latitude,
        "longitude": record.longitude,
        "phone": record.phone,
        "email": record.email,
        "website_url": record.website_url,
        "manager_name": record.manager_name,
        "licensed_capacity": record.licensed_capacity,
        "service_capacity_json": record.service_capacity,
        "health_authority": record.health_authority,
        "is_ccfri_authorized": record.is_ccfri_authorized,
        "is_multi_location": record.is_multi_location,
        "serves_under_36_months": record.serves_under_36_months,
        "serves_30_months_to_5_years": record.serves_30_months_to_5_years,
        "serves_licensed_preschool": record.serves_licensed_preschool,
        "serves_oos_kindergarten": record.serves_oos_kindergarten,
        "serves_oos_grade_1_to_12": record.serves_oos_grade_1_to_12,
        "programs_description": record.programs_description,
        "provides_meals": record.provides_meals,
        "provides_pickup": record.provides_pickup,
        "accommodates_special_needs": record.accommodates_special_needs,
        "aboriginal_programming": record.aboriginal_programming,
        "ece_certification": record.ece_certification,
        "open_weekdays": record.open_weekdays,
        "open_weekends": record.open_weekends,
        "open_stat_holidays": record.open_stat_holidays,
        "open_overnight": record.open_overnight,
        "open_before_6am_weekdays": record.open_before_6am_weekdays,
        "open_after_7pm_weekdays": record.open_after_7pm_weekdays,
        "hours_description": record.hours_description,
        "language_cantonese": record.language_cantonese,
        "language_punjabi": record.language_punjabi,
        "language_mandarin": record.language_mandarin,
        "language_french": record.language_french,
        "language_spanish": record.language_spanish,
        "language_other": record.language_other,
        "languages_description": record.languages_description,
        "has_reported_vacancy": record.has_reported_vacancy,
        "vacancy_under_36_months": record.vacancy_under_36_months,
        "vacancy_30_months_to_5_years": record.vacancy_30_months_to_5_years,
        "vacancy_licensed_preschool": record.vacancy_licensed_preschool,
        "vacancy_oos_grade_1_to_12": record.vacancy_oos_grade_1_to_12,
        "vacancy_for_license": record.vacancy_for_license,
        "vacancy_reported_at": record.vacancy_reported_at,
        "source_last_updated_at": record.source_last_updated_at,
        "imported_at": imported_at,
    }


def attach_to_canonical_provider(db: Session, *, source_provider: ChildcareProvider, imported_at: datetime) -> CanonicalProvider:
    canonical = source_provider.canonical_provider_id and db.get(CanonicalProvider, source_provider.canonical_provider_id)
    if canonical is None:
        canonical = find_matching_canonical_provider(db, source_provider=source_provider)
    if canonical is None:
        canonical = create_canonical_provider(db, source_provider=source_provider, imported_at=imported_at)

    if source_provider.canonical_provider_id != canonical.id:
        source_provider.canonical_provider_id = canonical.id
        db.flush()

    refresh_canonical_provider(db, canonical=canonical, imported_at=imported_at)
    return canonical


def find_matching_canonical_provider(db: Session, *, source_provider: ChildcareProvider) -> CanonicalProvider | None:
    normalized_name, normalized_address, match_key = build_match_key(
        name=source_provider.name,
        address_line_1=source_provider.address_line_1,
        full_address=source_provider.full_address,
        locality=source_provider.locality_normalized or source_provider.locality_raw,
    )
    canonical = db.scalar(select(CanonicalProvider).where(CanonicalProvider.match_key == match_key))
    if canonical is not None:
        return canonical

    address_candidates = db.scalars(
        select(CanonicalProvider).where(CanonicalProvider.normalized_address == normalized_address)
    ).all()
    for candidate in address_candidates:
        if names_are_compatible(normalized_name, candidate.normalized_name):
            return candidate

    normalized_phone = normalize_phone(source_provider.phone)
    if normalized_phone:
        candidates = db.scalars(
            select(CanonicalProvider).where(CanonicalProvider.normalized_name == normalized_name)
        ).all()
        for candidate in candidates:
            if normalize_phone(candidate.phone) == normalized_phone:
                return candidate
            if candidate.normalized_address == normalized_address:
                return candidate
    return None


def create_canonical_provider(db: Session, *, source_provider: ChildcareProvider, imported_at: datetime) -> CanonicalProvider:
    normalized_name, normalized_address, match_key = build_match_key(
        name=source_provider.name,
        address_line_1=source_provider.address_line_1,
        full_address=source_provider.full_address,
        locality=source_provider.locality_normalized or source_provider.locality_raw,
    )
    identity = standardize_provider_identity(
        name=source_provider.name,
        address_line_1=source_provider.address_line_1 or source_provider.full_address,
        city=source_provider.locality_normalized or source_provider.locality_raw,
    )
    canonical = CanonicalProvider(
        match_key=match_key,
        normalized_name=normalized_name,
        normalized_address=normalized_address,
        standard_city=identity.standard_city,
        name=source_provider.name,
        service_type=source_provider.service_type,
        address_line_1=source_provider.address_line_1,
        address_line_2=source_provider.address_line_2,
        postal_code=source_provider.postal_code,
        locality_raw=source_provider.locality_raw,
        locality_normalized=source_provider.locality_normalized,
        full_address=source_provider.full_address,
        latitude=source_provider.latitude,
        longitude=source_provider.longitude,
        phone=source_provider.phone,
        email=source_provider.email,
        website_url=source_provider.website_url,
        manager_name=source_provider.manager_name,
        licensed_capacity=source_provider.licensed_capacity,
        service_capacity_json=source_provider.service_capacity_json,
        health_authority=source_provider.health_authority,
        is_ccfri_authorized=source_provider.is_ccfri_authorized,
        is_multi_location=source_provider.is_multi_location,
        serves_under_36_months=source_provider.serves_under_36_months,
        serves_30_months_to_5_years=source_provider.serves_30_months_to_5_years,
        serves_licensed_preschool=source_provider.serves_licensed_preschool,
        serves_oos_kindergarten=source_provider.serves_oos_kindergarten,
        serves_oos_grade_1_to_12=source_provider.serves_oos_grade_1_to_12,
        programs_description=source_provider.programs_description,
        provides_meals=source_provider.provides_meals,
        provides_pickup=source_provider.provides_pickup,
        accommodates_special_needs=source_provider.accommodates_special_needs,
        aboriginal_programming=source_provider.aboriginal_programming,
        ece_certification=source_provider.ece_certification,
        open_weekdays=source_provider.open_weekdays,
        open_weekends=source_provider.open_weekends,
        open_stat_holidays=source_provider.open_stat_holidays,
        open_overnight=source_provider.open_overnight,
        open_before_6am_weekdays=source_provider.open_before_6am_weekdays,
        open_after_7pm_weekdays=source_provider.open_after_7pm_weekdays,
        hours_description=source_provider.hours_description,
        language_cantonese=source_provider.language_cantonese,
        language_punjabi=source_provider.language_punjabi,
        language_mandarin=source_provider.language_mandarin,
        language_french=source_provider.language_french,
        language_spanish=source_provider.language_spanish,
        language_other=source_provider.language_other,
        languages_description=source_provider.languages_description,
        has_reported_vacancy=source_provider.has_reported_vacancy,
        vacancy_under_36_months=source_provider.vacancy_under_36_months,
        vacancy_30_months_to_5_years=source_provider.vacancy_30_months_to_5_years,
        vacancy_licensed_preschool=source_provider.vacancy_licensed_preschool,
        vacancy_oos_grade_1_to_12=source_provider.vacancy_oos_grade_1_to_12,
        vacancy_for_license=source_provider.vacancy_for_license,
        vacancy_reported_at=source_provider.vacancy_reported_at,
        source_last_updated_at=source_provider.source_last_updated_at,
        imported_at=imported_at,
        updated_at=imported_at,
    )
    db.add(canonical)
    db.flush()
    return canonical


def refresh_canonical_provider(db: Session, *, canonical: CanonicalProvider, imported_at: datetime) -> None:
    linked_sources = db.scalars(
        select(ChildcareProvider).where(ChildcareProvider.canonical_provider_id == canonical.id)
    ).all()
    if not linked_sources:
        return

    linked_sources.sort(key=source_sort_key)
    primary = linked_sources[0]
    normalized_name, normalized_address, match_key = build_match_key(
        name=primary.name,
        address_line_1=primary.address_line_1,
        full_address=primary.full_address,
        locality=primary.locality_normalized or primary.locality_raw,
    )
    identity = standardize_provider_identity(
        name=primary.name,
        address_line_1=primary.address_line_1 or primary.full_address,
        city=primary.locality_normalized or primary.locality_raw,
    )

    canonical.match_key = match_key
    canonical.normalized_name = normalized_name
    canonical.normalized_address = normalized_address
    canonical.standard_city = identity.standard_city
    canonical.name = first_value(linked_sources, "name") or primary.name
    canonical.service_type = first_value(linked_sources, "service_type")
    canonical.address_line_1 = first_value(linked_sources, "address_line_1")
    canonical.address_line_2 = first_value(linked_sources, "address_line_2")
    canonical.postal_code = first_value(linked_sources, "postal_code")
    canonical.locality_raw = first_value(linked_sources, "locality_raw")
    canonical.locality_normalized = first_value(linked_sources, "locality_normalized")
    canonical.full_address = first_value(linked_sources, "full_address")
    canonical.latitude = first_value(linked_sources, "latitude", allow_zero=True) or primary.latitude
    canonical.longitude = first_value(linked_sources, "longitude", allow_zero=True) or primary.longitude
    canonical.phone = first_value(linked_sources, "phone")
    canonical.email = first_value(linked_sources, "email")
    canonical.website_url = first_value(linked_sources, "website_url")
    canonical.manager_name = first_value(linked_sources, "manager_name")
    canonical.licensed_capacity = first_value(linked_sources, "licensed_capacity", allow_zero=True)
    canonical.service_capacity_json = first_value(linked_sources, "service_capacity_json")
    canonical.health_authority = first_value(linked_sources, "health_authority")
    canonical.is_ccfri_authorized = first_value(linked_sources, "is_ccfri_authorized", include_false=True)
    canonical.is_multi_location = first_value(linked_sources, "is_multi_location", include_false=True)
    canonical.serves_under_36_months = first_indicator(linked_sources, "serves_under_36_months")
    canonical.serves_30_months_to_5_years = first_indicator(linked_sources, "serves_30_months_to_5_years")
    canonical.serves_licensed_preschool = first_indicator(linked_sources, "serves_licensed_preschool")
    canonical.serves_oos_kindergarten = first_indicator(linked_sources, "serves_oos_kindergarten")
    canonical.serves_oos_grade_1_to_12 = first_indicator(linked_sources, "serves_oos_grade_1_to_12")
    canonical.programs_description = first_value(linked_sources, "programs_description")
    canonical.provides_meals = first_value(linked_sources, "provides_meals")
    canonical.provides_pickup = first_value(linked_sources, "provides_pickup")
    canonical.accommodates_special_needs = first_indicator(linked_sources, "accommodates_special_needs")
    canonical.aboriginal_programming = first_indicator(linked_sources, "aboriginal_programming")
    canonical.ece_certification = first_indicator(linked_sources, "ece_certification")
    canonical.open_weekdays = first_indicator(linked_sources, "open_weekdays")
    canonical.open_weekends = first_indicator(linked_sources, "open_weekends")
    canonical.open_stat_holidays = first_indicator(linked_sources, "open_stat_holidays")
    canonical.open_overnight = first_indicator(linked_sources, "open_overnight")
    canonical.open_before_6am_weekdays = first_indicator(linked_sources, "open_before_6am_weekdays")
    canonical.open_after_7pm_weekdays = first_indicator(linked_sources, "open_after_7pm_weekdays")
    canonical.hours_description = first_value(linked_sources, "hours_description")
    canonical.language_cantonese = first_indicator(linked_sources, "language_cantonese")
    canonical.language_punjabi = first_indicator(linked_sources, "language_punjabi")
    canonical.language_mandarin = first_indicator(linked_sources, "language_mandarin")
    canonical.language_french = first_indicator(linked_sources, "language_french")
    canonical.language_spanish = first_indicator(linked_sources, "language_spanish")
    canonical.language_other = first_indicator(linked_sources, "language_other")
    canonical.languages_description = first_value(linked_sources, "languages_description")
    canonical.has_reported_vacancy = first_indicator(linked_sources, "has_reported_vacancy")
    canonical.vacancy_under_36_months = first_indicator(linked_sources, "vacancy_under_36_months")
    canonical.vacancy_30_months_to_5_years = first_indicator(linked_sources, "vacancy_30_months_to_5_years")
    canonical.vacancy_licensed_preschool = first_indicator(linked_sources, "vacancy_licensed_preschool")
    canonical.vacancy_oos_grade_1_to_12 = first_indicator(linked_sources, "vacancy_oos_grade_1_to_12")
    canonical.vacancy_for_license = first_value(linked_sources, "vacancy_for_license")
    canonical.vacancy_reported_at = first_value(linked_sources, "vacancy_reported_at")
    canonical.source_last_updated_at = first_value(linked_sources, "source_last_updated_at")
    canonical.imported_at = imported_at
    canonical.updated_at = imported_at
    db.flush()


def source_sort_key(provider: ChildcareProvider) -> tuple[int, str]:
    try:
        index = SOURCE_PRECEDENCE.index(provider.source_name)
    except ValueError:
        index = len(SOURCE_PRECEDENCE)
    return index, provider.source_name


def first_value(
    providers: list[ChildcareProvider],
    attribute: str,
    *,
    allow_zero: bool = False,
    include_false: bool = False,
):
    for provider in providers:
        value = getattr(provider, attribute)
        if value is None:
            continue
        if value is False and not include_false:
            continue
        if value == 0 and not allow_zero:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return value
    return None


def first_indicator(providers: list[ChildcareProvider], attribute: str) -> str:
    for provider in providers:
        value = getattr(provider, attribute)
        if value == YES_VALUE:
            return YES_VALUE
    for provider in providers:
        value = getattr(provider, attribute)
        if value == NO_VALUE:
            return NO_VALUE
    return UNKNOWN_VALUE


def names_are_compatible(left: str, right: str) -> bool:
    if left == right:
        return True
    if left and right and (left in right or right in left):
        return True
    left_tokens = {token for token in left.split(" ") if token}
    right_tokens = {token for token in right.split(" ") if token}
    if not left_tokens or not right_tokens:
        return False
    overlap = len(left_tokens & right_tokens)
    return overlap >= min(len(left_tokens), len(right_tokens), 2)
