from __future__ import annotations

from .models import SearchRequest

PRESET_REQUESTS: dict[str, dict] = {
    "changchun_weekend_plus": {
        "profile_name": "changchun_weekend_plus",
        "origins": ["SHA", "PVG"],
        "destination": "CGQ",
        "date_window_months": "1-3",
        "max_extension_workdays": 2,
        "trip_anchor": "weekend_or_holiday",
        "time_preferences": {
            "outbound_weekday_depart_after": "18:00",
            "return_arrival_target": "22:00",
            "return_arrival_soft_window": ["21:00", "23:00"],
        },
        "result_limit": 5,
    }
}


def request_from_profile(profile_name: str) -> SearchRequest:
    data = PRESET_REQUESTS.get(profile_name)
    if data is None:
        available = ", ".join(sorted(PRESET_REQUESTS))
        raise ValueError(f"Unknown profile '{profile_name}'. Available: {available}")
    return SearchRequest.model_validate(data)
