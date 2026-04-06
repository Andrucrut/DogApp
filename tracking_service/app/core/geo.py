from __future__ import annotations

SPB_LAT_MIN = 59.75
SPB_LAT_MAX = 60.10
SPB_LNG_MIN = 29.50
SPB_LNG_MAX = 30.75


def is_spb_point(latitude: float, longitude: float) -> bool:
    return SPB_LAT_MIN <= latitude <= SPB_LAT_MAX and SPB_LNG_MIN <= longitude <= SPB_LNG_MAX
