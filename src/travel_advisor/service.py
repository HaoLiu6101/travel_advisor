from __future__ import annotations

from collections import Counter
from datetime import date, timedelta

from .calendar_engine import generate_candidate_windows
from .connectors.base import Connector
from .models import SearchDebug, SearchRequest, SearchResponse
from .pair_builder import build_itinerary_pairs
from .scoring import rank_itineraries


class SearchService:
    def __init__(self, connector: Connector):
        self.connector = connector

    def search(self, request: SearchRequest) -> SearchResponse:
        min_month, max_month = request_month_range(request)

        start_date = date.today() + timedelta(days=min_month * 30)
        end_date = date.today() + timedelta(days=max_month * 30)

        windows = generate_candidate_windows(
            start_date=start_date,
            end_date=end_date,
            max_extension_workdays=request.max_extension_workdays,
            trip_anchor=request.trip_anchor,
            holiday_dates=set(request.holiday_dates),
            make_up_workdays=set(request.make_up_workdays),
        )

        dropped: Counter[str] = Counter()
        all_pairs = []
        route_profile = request.to_route_profile()

        for window in windows:
            fares = self.connector.search_fares(route_profile, window)
            build_result = build_itinerary_pairs(fares)
            all_pairs.extend(build_result.pairs)
            dropped.update(build_result.dropped_reason_counts)

        ranked = rank_itineraries(all_pairs, request.time_preferences)
        results = ranked[: request.result_limit]

        warnings: list[str] = []
        if not windows:
            warnings.append("No candidate windows generated from current date rules.")
        if windows and not results:
            warnings.append("Candidate windows found but no itineraries matched pairing constraints.")

        debug = SearchDebug(
            candidate_dates_count=len(windows),
            evaluated_pairs_count=len(all_pairs),
            scoring_weights={"price": 0.7, "time": 0.3},
            dropped_reason_counts=dict(dropped),
            warnings=warnings,
        )

        return SearchResponse(results=results, debug=debug)


def request_month_range(request: SearchRequest) -> tuple[int, int]:
    min_s, max_s = request.date_window_months.split("-")
    return int(min_s), int(max_s)
