from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

TRIP_ANCHOR_WEEKEND_OR_HOLIDAY = "weekend_or_holiday"
TripAnchor = Literal["weekend_or_holiday"]


class TimePreferences(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    outbound_weekday_depart_after: str = "18:00"
    return_arrival_target: str = "22:00"
    return_arrival_soft_window: tuple[str, str] = ("21:00", "23:00")

    @field_validator(
        "outbound_weekday_depart_after",
        "return_arrival_target",
        mode="before",
    )
    @classmethod
    def validate_hhmm(cls, value: str) -> str:
        _parse_hhmm(value)
        return value

    @field_validator("return_arrival_soft_window", mode="before")
    @classmethod
    def validate_window(cls, value: tuple[str, str] | list[str]) -> tuple[str, str]:
        if isinstance(value, list):
            if len(value) != 2:
                raise ValueError("return_arrival_soft_window must contain exactly 2 values")
            value = (value[0], value[1])
        start, end = value
        start_min = _parse_hhmm(start)
        end_min = _parse_hhmm(end)
        if start_min >= end_min:
            raise ValueError("return_arrival_soft_window start must be earlier than end")
        return value


class RouteProfile(BaseModel):
    name: str = "changchun_weekend_plus"
    origins: list[str] = Field(default_factory=lambda: ["SHA", "PVG"])
    destination: str = "CGQ"


class TravelWindow(BaseModel):
    outbound_date: date
    return_date: date
    working_days_used: int
    non_working_days: int


class FlightOption(BaseModel):
    leg_type: Literal["outbound", "return"]
    origin: str
    destination: str
    depart_at: datetime
    arrive_at: datetime
    provider: str
    flight_number: str
    price_cny: float
    currency: str = "CNY"


class ItineraryPair(BaseModel):
    outbound: FlightOption
    return_flight: FlightOption
    total_price_cny: float


class RankingScoreBreakdown(BaseModel):
    price_score: float
    time_score: float
    final_score: float


class RankedItinerary(BaseModel):
    outbound: FlightOption
    return_flight: FlightOption
    total_price_cny: float
    score: RankingScoreBreakdown
    reason_codes: list[str] = Field(default_factory=list)


class SearchDebug(BaseModel):
    candidate_dates_count: int
    evaluated_pairs_count: int
    scoring_weights: dict[str, float]
    dropped_reason_counts: dict[str, int] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class SearchRequest(BaseModel):
    profile_name: str = "changchun_weekend_plus"
    origins: list[str] = Field(default_factory=lambda: ["SHA", "PVG"])
    destination: str = "CGQ"
    date_window_months: str = "1-3"
    max_extension_workdays: int = Field(default=2, ge=0, le=10)
    trip_anchor: TripAnchor = TRIP_ANCHOR_WEEKEND_OR_HOLIDAY
    time_preferences: TimePreferences = Field(default_factory=TimePreferences)
    result_limit: int = Field(default=5, ge=1, le=100)
    holiday_dates: list[date] = Field(default_factory=list)
    make_up_workdays: list[date] = Field(default_factory=list)

    @field_validator("date_window_months")
    @classmethod
    def validate_month_range(cls, value: str) -> str:
        parse_month_range(value)
        return value

    @model_validator(mode="before")
    @classmethod
    def flatten_route_profile(cls, data: dict) -> dict:
        if not isinstance(data, dict):
            return data
        route_profile = data.pop("route_profile", None)
        if isinstance(route_profile, dict):
            data.setdefault("profile_name", route_profile.get("name", "changchun_weekend_plus"))
            data.setdefault("origins", route_profile.get("origins", ["SHA", "PVG"]))
            data.setdefault("destination", route_profile.get("destination", "CGQ"))
        return data

    def to_route_profile(self) -> RouteProfile:
        return RouteProfile(
            name=self.profile_name,
            origins=self.origins,
            destination=self.destination,
        )


class SearchResponse(BaseModel):
    results: list[RankedItinerary]
    debug: SearchDebug


def parse_month_range(raw_value: str) -> tuple[int, int]:
    parts = raw_value.split("-")
    if len(parts) != 2:
        raise ValueError("date_window_months must be in format 'min-max', e.g. '1-3'")
    try:
        min_month = int(parts[0])
        max_month = int(parts[1])
    except ValueError as exc:
        raise ValueError("date_window_months must contain integers") from exc
    if min_month < 1 or max_month < 1:
        raise ValueError("date_window_months values must be >= 1")
    if min_month > max_month:
        raise ValueError("date_window_months min cannot be greater than max")
    return min_month, max_month


def hhmm_to_minutes(value: str) -> int:
    return _parse_hhmm(value)


def _parse_hhmm(value: str) -> int:
    parts = value.split(":")
    if len(parts) != 2:
        raise ValueError("Time must be in HH:MM format")
    try:
        hour = int(parts[0])
        minute = int(parts[1])
    except ValueError as exc:
        raise ValueError("Time must be in HH:MM format") from exc
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        raise ValueError("Time must be a valid 24-hour value")
    return hour * 60 + minute
