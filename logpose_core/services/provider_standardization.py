from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass


WORD_ORDINALS = {
    "first": "1",
    "second": "2",
    "third": "3",
    "fourth": "4",
    "fifth": "5",
    "sixth": "6",
    "seventh": "7",
    "eighth": "8",
    "ninth": "9",
    "tenth": "10",
    "eleventh": "11",
    "twelfth": "12",
    "thirteenth": "13",
    "fourteenth": "14",
    "fifteenth": "15",
    "sixteenth": "16",
    "seventeenth": "17",
    "eighteenth": "18",
    "nineteenth": "19",
    "twentieth": "20",
}

STREET_SUFFIXES = {
    "st": "street",
    "street": "street",
    "ave": "avenue",
    "av": "avenue",
    "avenue": "avenue",
    "rd": "road",
    "road": "road",
    "dr": "drive",
    "drive": "drive",
    "ln": "lane",
    "lane": "lane",
    "ct": "court",
    "crt": "court",
    "court": "court",
    "pl": "place",
    "place": "place",
    "blvd": "boulevard",
    "boulevard": "boulevard",
    "cres": "crescent",
    "crescent": "crescent",
    "hwy": "highway",
    "highway": "highway",
    "terr": "terrace",
    "terrace": "terrace",
    "cir": "circle",
    "circle": "circle",
    "pkwy": "parkway",
    "parkway": "parkway",
}

NAME_NOISE_TOKENS = {
    "inc",
    "incorporated",
    "ltd",
    "limited",
    "corp",
    "corporation",
}

UNIT_PREFIX_TOKENS = {"unit", "suite", "ste", "room", "rm"}
STREET_SUFFIX_WORDS = set(STREET_SUFFIXES.values())


@dataclass(frozen=True)
class StandardizedProviderIdentity:
    standard_name: str
    standard_address: str
    standard_city: str
    match_key: str


def standardize_provider_identity(
    *,
    name: str | None,
    address_line_1: str | None,
    city: str | None,
) -> StandardizedProviderIdentity:
    standard_name = standardize_name(name)
    standard_address = standardize_address(address_line_1)
    standard_city = standardize_city(city)
    match_key = hashlib.sha256(
        f"{standard_name}|{standard_address}|{standard_city}".encode("utf-8")
    ).hexdigest()
    return StandardizedProviderIdentity(
        standard_name=standard_name,
        standard_address=standard_address,
        standard_city=standard_city,
        match_key=match_key,
    )


def standardize_name(value: str | None) -> str:
    normalized = normalize_common_text(value)
    normalized = re.sub(r"\bchild\s+care\b", "childcare", normalized)
    normalized = re.sub(r"\bcentre\b", "center", normalized)
    tokens = [token for token in normalized.split() if token not in NAME_NOISE_TOKENS]
    return " ".join(tokens)


def standardize_city(value: str | None) -> str:
    return normalize_common_text(value)


def standardize_address(value: str | None) -> str:
    normalized = normalize_common_text(value)
    if not normalized:
        return ""

    normalized = replace_word_ordinals(normalized)
    normalized = re.sub(r"\b(\d+)(st|nd|rd|th)\b", r"\1", normalized)
    normalized = re.sub(r"\b(\d+)\s+(nd|rd|th)\b", r"\1", normalized)
    normalized = re.sub(r"^(\d+)\s+(?:e|east|w|west|n|north|s|south)\s+(\d+)\b", r"\1 \2", normalized)
    normalized = re.sub(r"\b(\d+)\s+([a-df-mo-rt-vx-z])\b", r"\1\2", normalized)

    tokens = [STREET_SUFFIXES.get(token, token) for token in normalized.split()]
    tokens = strip_unit_prefix(tokens)
    return " ".join(tokens)


def normalize_common_text(value: str | None) -> str:
    if not value:
        return ""
    normalized = value.casefold().strip()
    normalized = normalized.replace("â€™", "'").replace("â€˜", "'")
    normalized = normalized.replace("'", "").replace("’", "")
    normalized = normalized.replace("&", " and ")
    normalized = re.sub(r"[^a-z0-9 ]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def replace_word_ordinals(value: str) -> str:
    tokens = [WORD_ORDINALS.get(token, token) for token in value.split()]
    return " ".join(tokens)


def strip_unit_prefix(tokens: list[str]) -> list[str]:
    stripped = list(tokens)
    while len(stripped) >= 4:
        if stripped[0] in UNIT_PREFIX_TOKENS:
            stripped = stripped[1:]
            continue
        if stripped[0].isdigit() and stripped[1].isdigit():
            first_number = int(stripped[0])
            second_number = int(stripped[1])
            if first_number < second_number:
                stripped = stripped[1:]
                continue
            if first_number <= 999 and second_number <= 999 and stripped[2] not in STREET_SUFFIX_WORDS:
                stripped = stripped[1:]
                continue
        if re.fullmatch(r"[a-z]{1,4}\d*[a-z]?", stripped[0]) and stripped[1].isdigit():
            stripped = stripped[1:]
            continue
        break
    return stripped
