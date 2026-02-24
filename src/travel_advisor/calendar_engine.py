from __future__ import annotations

from datetime import date, timedelta

from .models import TRIP_ANCHOR_WEEKEND_OR_HOLIDAY, TravelWindow


def is_working_day(
    day: date,
    holiday_dates: set[date],
    make_up_workdays: set[date],
) -> bool:
    if day in make_up_workdays:
        return True
    if day in holiday_dates:
        return False
    return day.weekday() < 5


def generate_candidate_windows(
    start_date: date,
    end_date: date,
    max_extension_workdays: int,
    trip_anchor: str,
    holiday_dates: set[date] | None = None,
    make_up_workdays: set[date] | None = None,
    min_trip_days: int = 2,
    max_trip_days: int = 6,
) -> list[TravelWindow]:
    if start_date > end_date:
        return []
    if trip_anchor != TRIP_ANCHOR_WEEKEND_OR_HOLIDAY:
        raise ValueError(f"Unsupported trip_anchor: {trip_anchor}")

    holiday_dates = holiday_dates or set()
    make_up_workdays = make_up_workdays or set()

    windows: list[TravelWindow] = []
    current = start_date
    while current <= end_date:
        for trip_days in range(min_trip_days, max_trip_days + 1):
            return_date = current + timedelta(days=trip_days - 1)
            if return_date > end_date:
                break

            working_days = 0
            non_working_days = 0
            walk = current
            while walk <= return_date:
                if is_working_day(walk, holiday_dates, make_up_workdays):
                    working_days += 1
                else:
                    non_working_days += 1
                walk += timedelta(days=1)

            if non_working_days < 2:
                continue
            if working_days > max_extension_workdays:
                continue

            windows.append(
                TravelWindow(
                    outbound_date=current,
                    return_date=return_date,
                    working_days_used=working_days,
                    non_working_days=non_working_days,
                )
            )
        current += timedelta(days=1)

    return windows
