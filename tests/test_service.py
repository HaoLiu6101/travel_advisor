from __future__ import annotations

from collections import Counter

from travel_advisor.connectors.base import Connector, ConnectorError
from travel_advisor.connectors.sample import SampleConnector
from travel_advisor.models import FlightOption, RouteProfile, SearchRequest, TravelWindow
from travel_advisor.service import SearchService


def test_end_to_end_fixture_case_returns_ranked_results():
    service = SearchService(connector=SampleConnector())
    request = SearchRequest.model_validate(
        {
            "route_profile": {"origins": ["SHA", "PVG"], "destination": "CGQ"},
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
    )

    response = service.search(request)

    assert response.results
    assert len(response.results) <= 5
    assert response.debug.candidate_dates_count > 0
    assert response.debug.evaluated_pairs_count > 0
    for result in response.results:
        assert result.total_price_cny == result.outbound.price_cny + result.return_flight.price_cny


class CountingEmptyRealConnector(Connector):
    is_real_connector = True

    def __init__(self):
        self.calls = 0
        self.by_window = Counter()

    def search_fares(self, route_profile: RouteProfile, travel_window: TravelWindow) -> list[FlightOption]:
        self.calls += 1
        self.by_window[(travel_window.outbound_date, travel_window.return_date)] += 1
        return []


class FailingConnector(Connector):
    def search_fares(self, route_profile: RouteProfile, travel_window: TravelWindow) -> list[FlightOption]:
        raise ConnectorError("upstream unavailable")


def test_real_mode_window_cap_applies(monkeypatch):
    connector = CountingEmptyRealConnector()
    monkeypatch.setenv("TRAVEL_ADVISOR_REAL_MAX_WINDOWS", "2")

    service = SearchService(connector=connector)
    response = service.search(SearchRequest(date_window_months="1-3"))

    assert response.debug.candidate_dates_count > 2
    assert connector.calls == 2
    assert "Real connector window cap applied" in " ".join(response.debug.warnings)


def test_connector_error_returns_warning_without_exception():
    service = SearchService(connector=FailingConnector())
    response = service.search(SearchRequest(date_window_months="1-2"))

    assert response.results == []
    assert "Connector error: upstream unavailable" in response.debug.warnings
