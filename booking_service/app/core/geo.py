from __future__ import annotations

SPB_LAT_MIN = 59.75
SPB_LAT_MAX = 60.10
SPB_LNG_MIN = 29.50
SPB_LNG_MAX = 30.75

_COUNTRY_ALIASES = {"россия", "рф", "russia", "russian federation"}
_CITY_ALIASES = {"санкт-петербург", "санкт петербург", "saint petersburg", "st petersburg"}


def normalize_text(value: str) -> str:
    return " ".join(value.lower().strip().split())


def is_supported_country(value: str) -> bool:
    return normalize_text(value) in _COUNTRY_ALIASES


def is_supported_city(value: str) -> bool:
    return normalize_text(value) in _CITY_ALIASES


def is_spb_point(latitude: float, longitude: float) -> bool:
    return SPB_LAT_MIN <= latitude <= SPB_LAT_MAX and SPB_LNG_MIN <= longitude <= SPB_LNG_MAX
