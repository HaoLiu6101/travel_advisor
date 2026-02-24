from datetime import date

from travel_advisor.calendar_engine import generate_candidate_windows


def _has_window(windows, outbound, ret):
    return any(w.outbound_date == outbound and w.return_date == ret for w in windows)


def test_weekend_only_window_generated():
    windows = generate_candidate_windows(
        start_date=date(2026, 3, 13),
        end_date=date(2026, 3, 17),
        max_extension_workdays=0,
        trip_anchor="weekend_or_holiday",
    )
    assert _has_window(windows, date(2026, 3, 14), date(2026, 3, 15))


def test_weekend_plus_one_workday_extension_generated():
    windows = generate_candidate_windows(
        start_date=date(2026, 3, 13),
        end_date=date(2026, 3, 17),
        max_extension_workdays=1,
        trip_anchor="weekend_or_holiday",
    )
    assert _has_window(windows, date(2026, 3, 14), date(2026, 3, 16))


def test_weekend_plus_two_workday_extension_generated():
    windows = generate_candidate_windows(
        start_date=date(2026, 3, 13),
        end_date=date(2026, 3, 17),
        max_extension_workdays=2,
        trip_anchor="weekend_or_holiday",
    )
    assert _has_window(windows, date(2026, 3, 13), date(2026, 3, 16))


def test_make_up_workday_boundary_case():
    windows = generate_candidate_windows(
        start_date=date(2026, 3, 13),
        end_date=date(2026, 3, 17),
        max_extension_workdays=1,
        trip_anchor="weekend_or_holiday",
        make_up_workdays={date(2026, 3, 14)},
    )
    assert not _has_window(windows, date(2026, 3, 14), date(2026, 3, 16))
