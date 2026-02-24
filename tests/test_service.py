from travel_advisor.connectors.sample import SampleConnector
from travel_advisor.models import SearchRequest
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
