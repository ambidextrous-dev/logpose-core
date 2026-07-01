"""Marshmallow schemas for data validation and normalization."""

from __future__ import annotations

from datetime import date, datetime
from marshmallow import Schema, fields, post_load, EXCLUDE


LOCALITY_NORMALIZATION = {
    "Bunaby": "Burnaby",
    "Langely": "Langley",
    "New Westminister": "New Westminster",
    "New Westmister": "New Westminster",
}


def normalize_indicator(value: str | None) -> str:
    """Normalize Y/N/Unknown indicators to yes/no/unknown."""
    if not value or value.strip() == "":
        return "unknown"
    normalized = value.strip().upper()
    if normalized == "Y":
        return "yes"
    if normalized == "N":
        return "no"
    return "unknown"


def normalize_locality(value: str | None) -> str | None:
    """Normalize known locality typos."""
    if not value:
        return None
    return LOCALITY_NORMALIZATION.get(value, value)


def normalize_date(value: str | None) -> date | None:
    """Parse YYYY/MM/DD date strings."""
    if not value or value.strip() == "":
        return None
    try:
        return datetime.strptime(value.strip(), "%Y/%m/%d").date()
    except (ValueError, AttributeError):
        return None


class BCChildcareRecordSchema(Schema):
    """Schema for BC Child Care Map API records."""
    
    class Meta:
        unknown = EXCLUDE
    
    # Source identity
    facility_id = fields.Str(required=True, data_key="FACILITY_ID")
    sequence_id = fields.Int(required=True, data_key="SEQUENCE_ID")
    
    # Provider identity
    name = fields.Str(required=True, data_key="OCCUPANT_NAME")
    service_type = fields.Str(allow_none=True, data_key="SERVICE_TYPE_DESC")
    
    # Location
    street_address = fields.Str(allow_none=True, data_key="STREET_ADDRESS")
    address_line_2 = fields.Str(allow_none=True, data_key="ADDRESS_LINE_2")
    postal_code = fields.Str(allow_none=True, data_key="POSTAL_CODE")
    locality = fields.Str(allow_none=True, data_key="LOCALITY")
    full_address = fields.Str(allow_none=True, data_key="DESC_FULL_ADDRESS")
    latitude = fields.Float(required=True, data_key="LATITUDE")
    longitude = fields.Float(required=True, data_key="LONGITUDE")
    
    # Contact
    phone = fields.Str(allow_none=True, data_key="CONTACT_PHONE")
    email = fields.Str(allow_none=True, data_key="CONTACT_EMAIL")
    website_url = fields.Str(allow_none=True, data_key="WEBSITE_URL")
    
    # Services
    serves_under_36_months = fields.Str(required=True, data_key="SRVC_UNDER36_IND")
    serves_30_months_to_5_years = fields.Str(required=True, data_key="SRVC_30MOS_5YRS_IND")
    serves_licensed_preschool = fields.Str(required=True, data_key="SRVC_LICPRE_IND")
    serves_oos_kindergarten = fields.Str(required=True, data_key="SRVC_OOS_KINDER_IND")
    serves_oos_grade_1_to_12 = fields.Str(required=True, data_key="SRVC_OOS_GR1_AGE12_IND")
    programs_description = fields.Str(allow_none=True, data_key="DESC_PROGRAMS_PROVIDED")
    
    # Features
    provides_meals = fields.Str(allow_none=True, data_key="PROVIDE_MEALS_DESC")
    provides_pickup = fields.Str(allow_none=True, data_key="PROVIDE_PICKUP_DESC")
    accommodates_special_needs = fields.Str(required=True, data_key="ACCOMMODATE_SPECIAL_NEEDS_IND")
    aboriginal_programming = fields.Str(required=True, data_key="ABORIGINAL_PROGRAMMING_IND")
    ece_certification = fields.Str(required=True, data_key="ECE_CERTIFICATION_IND")
    is_ccfri_authorized = fields.Str(allow_none=True, data_key="IS_CCFRI_AUTH_IND")
    is_multi_location = fields.Str(allow_none=True, data_key="IS_MULTI_LOCN_IND")
    
    # Hours
    open_weekdays = fields.Str(required=True, data_key="OP_WEEKDAY_IND")
    open_weekends = fields.Str(required=True, data_key="OP_WEEKEND_IND")
    open_stat_holidays = fields.Str(required=True, data_key="OP_STAT_HOLIDAY_IND")
    open_overnight = fields.Str(required=True, data_key="OP_OVERNIGHT_IND")
    open_before_6am_weekdays = fields.Str(required=True, data_key="OP_EXT_WEEKDAY_BEFORE6AM_IND")
    open_after_7pm_weekdays = fields.Str(required=True, data_key="OP_EXT_WEEKDAY_AFTER7PM_IND")
    hours_description = fields.Str(allow_none=True, data_key="DESC_HOURS_OF_OPERATION")
    
    # Languages
    language_cantonese = fields.Str(required=True, data_key="LANG_CANTONESE_IND")
    language_punjabi = fields.Str(required=True, data_key="LANG_PUNJABI_IND")
    language_mandarin = fields.Str(required=True, data_key="LANG_MANDARIN_IND")
    language_french = fields.Str(required=True, data_key="LANG_FRENCH_IND")
    language_spanish = fields.Str(required=True, data_key="LANG_SPANISH_IND")
    language_other = fields.Str(required=True, data_key="LANG_OTHER_IND")
    languages_description = fields.Str(allow_none=True, data_key="DESC_ADDITIONAL_LANGUAGES")
    
    # Vacancy
    has_reported_vacancy = fields.Str(required=True, data_key="VACANCY_IND")
    vacancy_under_36_months = fields.Str(required=True, data_key="VACANCY_SRVC_UNDER36_IND")
    vacancy_30_months_to_5_years = fields.Str(required=True, data_key="VACANCY_SRVC_30MOS_5YRS_IND")
    vacancy_licensed_preschool = fields.Str(required=True, data_key="VACANCY_SRVC_LICPRE_IND")
    vacancy_oos_grade_1_to_12 = fields.Str(required=True, data_key="VACANCY_SRVC_OOS_GR1_AGE12_IND")
    vacancy_for_license = fields.Str(allow_none=True, data_key="VACANCY_FOR_LICENSE")
    vacancy_reported_at = fields.Str(allow_none=True, data_key="VACANCY_LAST_UPDATE_DATE")
    
    @post_load
    def normalize_fields(self, data: dict, **kwargs) -> dict:
        """Normalize indicators, localities, and dates."""
        # Normalize Y/N indicators
        indicator_fields = [
            "serves_under_36_months", "serves_30_months_to_5_years", "serves_licensed_preschool",
            "serves_oos_kindergarten", "serves_oos_grade_1_to_12", "accommodates_special_needs",
            "aboriginal_programming", "ece_certification", "open_weekdays", "open_weekends",
            "open_stat_holidays", "open_overnight", "open_before_6am_weekdays", "open_after_7pm_weekdays",
            "language_cantonese", "language_punjabi", "language_mandarin", "language_french",
            "language_spanish", "language_other", "has_reported_vacancy", "vacancy_under_36_months",
            "vacancy_30_months_to_5_years", "vacancy_licensed_preschool", "vacancy_oos_grade_1_to_12",
        ]
        for field in indicator_fields:
            if field in data:
                data[field] = normalize_indicator(data[field])
        
        # Normalize boolean indicators
        if "is_ccfri_authorized" in data:
            data["is_ccfri_authorized"] = data["is_ccfri_authorized"] == "Y" if data["is_ccfri_authorized"] else None
        if "is_multi_location" in data:
            data["is_multi_location"] = data["is_multi_location"] == "Y" if data["is_multi_location"] else None
        
        # Normalize locality
        if "locality" in data:
            data["locality_raw"] = data["locality"]
            data["locality_normalized"] = normalize_locality(data["locality"])
            del data["locality"]
        
        # Normalize date
        if "vacancy_reported_at" in data:
            data["vacancy_reported_at"] = normalize_date(data["vacancy_reported_at"])
        
        return data
