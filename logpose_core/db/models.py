from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from logpose_core.db.base import Base


class SourceImport(Base):
    __tablename__ = "source_imports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    source_name: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    record_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint("status IN ('running', 'succeeded', 'failed')", name="source_imports_status_check"),
    )


class SourceRecord(Base):
    __tablename__ = "source_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    source_import_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("source_imports.id"), nullable=True)
    source_name: Mapped[str] = mapped_column(Text, nullable=False)
    source_record_id: Mapped[str] = mapped_column(Text, nullable=False)
    raw_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    payload_hash: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

    __table_args__ = (
        CheckConstraint("length(payload_hash) > 0", name="source_records_payload_hash_check"),
        UniqueConstraint("source_name", "source_record_id", name="uq_source_records_source_name_source_record_id"),
    )


class CanonicalProvider(Base):
    __tablename__ = "canonical_providers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    match_key: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    normalized_name: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_address: Mapped[str] = mapped_column(Text, nullable=False)
    standard_city: Mapped[str | None] = mapped_column(Text, nullable=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    service_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    address_line_1: Mapped[str | None] = mapped_column(Text, nullable=True)
    address_line_2: Mapped[str | None] = mapped_column(Text, nullable=True)
    postal_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    locality_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    locality_normalized: Mapped[str | None] = mapped_column(Text, nullable=True)
    full_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    latitude: Mapped[float] = mapped_column(nullable=False)
    longitude: Mapped[float] = mapped_column(nullable=False)
    phone: Mapped[str | None] = mapped_column(Text, nullable=True)
    email: Mapped[str | None] = mapped_column(Text, nullable=True)
    website_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    manager_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    licensed_capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    service_capacity_json: Mapped[dict | None] = mapped_column("service_capacity", JSONB, nullable=True)
    health_authority: Mapped[str | None] = mapped_column(Text, nullable=True)
    vch_disclosure_program_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    vch_facility_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    vch_inspection_reports_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    vch_last_inspection_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    vch_inspection_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    vch_outstanding_critical_infractions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    vch_outstanding_noncritical_infractions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_ccfri_authorized: Mapped[bool | None] = mapped_column(nullable=True)
    is_multi_location: Mapped[bool | None] = mapped_column(nullable=True)
    serves_under_36_months: Mapped[str] = mapped_column(Text, nullable=False)
    serves_30_months_to_5_years: Mapped[str] = mapped_column(Text, nullable=False)
    serves_licensed_preschool: Mapped[str] = mapped_column(Text, nullable=False)
    serves_oos_kindergarten: Mapped[str] = mapped_column(Text, nullable=False)
    serves_oos_grade_1_to_12: Mapped[str] = mapped_column(Text, nullable=False)
    programs_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    provides_meals: Mapped[str | None] = mapped_column(Text, nullable=True)
    provides_pickup: Mapped[str | None] = mapped_column(Text, nullable=True)
    accommodates_special_needs: Mapped[str] = mapped_column(Text, nullable=False)
    aboriginal_programming: Mapped[str] = mapped_column(Text, nullable=False)
    ece_certification: Mapped[str] = mapped_column(Text, nullable=False)
    open_weekdays: Mapped[str] = mapped_column(Text, nullable=False)
    open_weekends: Mapped[str] = mapped_column(Text, nullable=False)
    open_stat_holidays: Mapped[str] = mapped_column(Text, nullable=False)
    open_overnight: Mapped[str] = mapped_column(Text, nullable=False)
    open_before_6am_weekdays: Mapped[str] = mapped_column(Text, nullable=False)
    open_after_7pm_weekdays: Mapped[str] = mapped_column(Text, nullable=False)
    hours_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    language_cantonese: Mapped[str] = mapped_column(Text, nullable=False)
    language_punjabi: Mapped[str] = mapped_column(Text, nullable=False)
    language_mandarin: Mapped[str] = mapped_column(Text, nullable=False)
    language_french: Mapped[str] = mapped_column(Text, nullable=False)
    language_spanish: Mapped[str] = mapped_column(Text, nullable=False)
    language_other: Mapped[str] = mapped_column(Text, nullable=False)
    languages_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    has_reported_vacancy: Mapped[str] = mapped_column(Text, nullable=False)
    vacancy_under_36_months: Mapped[str] = mapped_column(Text, nullable=False)
    vacancy_30_months_to_5_years: Mapped[str] = mapped_column(Text, nullable=False)
    vacancy_licensed_preschool: Mapped[str] = mapped_column(Text, nullable=False)
    vacancy_oos_grade_1_to_12: Mapped[str] = mapped_column(Text, nullable=False)
    vacancy_for_license: Mapped[str | None] = mapped_column(Text, nullable=True)
    vacancy_reported_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_last_updated_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))


class ChildcareProvider(Base):
    __tablename__ = "childcare_providers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    canonical_provider_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical_providers.id"), nullable=True)
    source_name: Mapped[str] = mapped_column(Text, nullable=False)
    source_facility_id: Mapped[str] = mapped_column(Text, nullable=False)
    source_sequence_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_record_ref: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("source_records.id"), nullable=True)
    standard_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    standard_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    standard_city: Mapped[str | None] = mapped_column(Text, nullable=True)
    match_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    service_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    address_line_1: Mapped[str | None] = mapped_column(Text, nullable=True)
    address_line_2: Mapped[str | None] = mapped_column(Text, nullable=True)
    postal_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    locality_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    locality_normalized: Mapped[str | None] = mapped_column(Text, nullable=True)
    full_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    latitude: Mapped[float] = mapped_column(nullable=False)
    longitude: Mapped[float] = mapped_column(nullable=False)
    phone: Mapped[str | None] = mapped_column(Text, nullable=True)
    email: Mapped[str | None] = mapped_column(Text, nullable=True)
    website_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    manager_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    licensed_capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    service_capacity_json: Mapped[dict | None] = mapped_column("service_capacity", JSONB, nullable=True)
    health_authority: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_ccfri_authorized: Mapped[bool | None] = mapped_column(nullable=True)
    is_multi_location: Mapped[bool | None] = mapped_column(nullable=True)
    serves_under_36_months: Mapped[str] = mapped_column(Text, nullable=False)
    serves_30_months_to_5_years: Mapped[str] = mapped_column(Text, nullable=False)
    serves_licensed_preschool: Mapped[str] = mapped_column(Text, nullable=False)
    serves_oos_kindergarten: Mapped[str] = mapped_column(Text, nullable=False)
    serves_oos_grade_1_to_12: Mapped[str] = mapped_column(Text, nullable=False)
    programs_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    provides_meals: Mapped[str | None] = mapped_column(Text, nullable=True)
    provides_pickup: Mapped[str | None] = mapped_column(Text, nullable=True)
    accommodates_special_needs: Mapped[str] = mapped_column(Text, nullable=False)
    aboriginal_programming: Mapped[str] = mapped_column(Text, nullable=False)
    ece_certification: Mapped[str] = mapped_column(Text, nullable=False)
    open_weekdays: Mapped[str] = mapped_column(Text, nullable=False)
    open_weekends: Mapped[str] = mapped_column(Text, nullable=False)
    open_stat_holidays: Mapped[str] = mapped_column(Text, nullable=False)
    open_overnight: Mapped[str] = mapped_column(Text, nullable=False)
    open_before_6am_weekdays: Mapped[str] = mapped_column(Text, nullable=False)
    open_after_7pm_weekdays: Mapped[str] = mapped_column(Text, nullable=False)
    hours_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    language_cantonese: Mapped[str] = mapped_column(Text, nullable=False)
    language_punjabi: Mapped[str] = mapped_column(Text, nullable=False)
    language_mandarin: Mapped[str] = mapped_column(Text, nullable=False)
    language_french: Mapped[str] = mapped_column(Text, nullable=False)
    language_spanish: Mapped[str] = mapped_column(Text, nullable=False)
    language_other: Mapped[str] = mapped_column(Text, nullable=False)
    languages_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    has_reported_vacancy: Mapped[str] = mapped_column(Text, nullable=False)
    vacancy_under_36_months: Mapped[str] = mapped_column(Text, nullable=False)
    vacancy_30_months_to_5_years: Mapped[str] = mapped_column(Text, nullable=False)
    vacancy_licensed_preschool: Mapped[str] = mapped_column(Text, nullable=False)
    vacancy_oos_grade_1_to_12: Mapped[str] = mapped_column(Text, nullable=False)
    vacancy_for_license: Mapped[str | None] = mapped_column(Text, nullable=True)
    vacancy_reported_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_last_updated_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

    __table_args__ = (
        UniqueConstraint("source_name", "source_facility_id", name="uq_childcare_providers_source_name_source_facility_id"),
    )


class FraserHealthFacility(Base):
    __tablename__ = "fraser_health_facilities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    source_import_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("source_imports.id"), nullable=True)
    source_record_id: Mapped[str] = mapped_column(Text, nullable=False)
    region_key: Mapped[str] = mapped_column(Text, nullable=False)
    service_type: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    address_line_1: Mapped[str] = mapped_column(Text, nullable=False)
    locality_raw: Mapped[str] = mapped_column(Text, nullable=False)
    locality_normalized: Mapped[str | None] = mapped_column(Text, nullable=True)
    licensed_capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    manager_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(Text, nullable=True)
    standard_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    standard_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    standard_city: Mapped[str | None] = mapped_column(Text, nullable=True)
    match_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    service_capacity_json: Mapped[dict | None] = mapped_column("service_capacity", JSONB, nullable=True)
    health_authority: Mapped[str] = mapped_column(Text, nullable=False)
    raw_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    payload_hash: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

    __table_args__ = (
        CheckConstraint("length(payload_hash) > 0", name="fraser_health_facilities_payload_hash_check"),
        UniqueConstraint("source_record_id", name="uq_fraser_health_facilities_source_record_id"),
    )


class VchChildcareFacility(Base):
    __tablename__ = "vch_childcare_facilities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    source_import_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("source_imports.id"), nullable=True)
    source_record_id: Mapped[str] = mapped_column(Text, nullable=False)
    disclosure_program_id: Mapped[str] = mapped_column(Text, nullable=False)
    service_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    address_line_1: Mapped[str | None] = mapped_column(Text, nullable=True)
    postal_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    locality_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    locality_normalized: Mapped[str | None] = mapped_column(Text, nullable=True)
    full_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(Text, nullable=True)
    website_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    operator_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    licensed_capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_inspection_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    inspection_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    outstanding_critical_infractions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    outstanding_noncritical_infractions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    standard_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    standard_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    standard_city: Mapped[str | None] = mapped_column(Text, nullable=True)
    match_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    health_authority: Mapped[str] = mapped_column(Text, nullable=False)
    raw_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    payload_hash: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

    __table_args__ = (
        CheckConstraint("length(payload_hash) > 0", name="vch_childcare_facilities_payload_hash_check"),
        UniqueConstraint("source_record_id", name="uq_vch_childcare_facilities_source_record_id"),
    )
