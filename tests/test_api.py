from travel_advisor import api
from travel_advisor.connectors.base import Connector
from travel_advisor.models import FlightOption, RouteProfile, SearchRequest, TravelWindow
from travel_advisor.service import SearchService
from pydantic import ValidationError


class EmptyConnector(Connector):
    def search_fares(self, route_profile: RouteProfile, travel_window: TravelWindow) -> list[FlightOption]:
        return []


def test_search_success_contract_shape():
    response = api.search(SearchRequest())
    payload = response.model_dump()

    assert "results" in payload
    assert "debug" in payload
    assert payload["debug"]["scoring_weights"] == {"price": 0.7, "time": 0.3}


def test_invalid_time_validation_error():
    try:
        SearchRequest.model_validate(
            {
                "time_preferences": {
                    "outbound_weekday_depart_after": "24:00",
                    "return_arrival_target": "22:00",
                    "return_arrival_soft_window": ["21:00", "23:00"],
                }
            }
        )
    except ValidationError:
        return

    raise AssertionError("Expected ValidationError for invalid time input")


def test_empty_results_response_is_clean(monkeypatch):
    monkeypatch.setattr(api, "service", SearchService(connector=EmptyConnector()))

    response = api.search(SearchRequest(date_window_months="1-1"))
    payload = response.model_dump()

    assert payload["results"] == []
    assert payload["debug"]["warnings"]
