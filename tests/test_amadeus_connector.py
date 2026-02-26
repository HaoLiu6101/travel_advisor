from __future__ import annotations

from datetime import date

import httpx
import pytest

from travel_advisor.connectors.amadeus import AmadeusConnector
from travel_advisor.connectors.base import ConnectorError
from travel_advisor.models import RouteProfile, TravelWindow


def test_amadeus_connector_normalizes_outbound_and_return_options():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/security/oauth2/token":
            return httpx.Response(200, json={"access_token": "token-1", "expires_in": 1800})

        if request.url.path == "/v2/shopping/flight-offers":
            params = dict(request.url.params)
            origin = params.get("originLocationCode")
            destination = params.get("destinationLocationCode")

            if origin == "SHA" and destination == "CGQ":
                return httpx.Response(
                    200,
                    json={
                        "data": [
                            {
                                "price": {"currency": "CNY", "grandTotal": "650.50"},
                                "itineraries": [
                                    {
                                        "segments": [
                                            {
                                                "carrierCode": "MU",
                                                "number": "5111",
                                                "departure": {"at": "2026-03-28T18:10:00+08:00"},
                                                "arrival": {"at": "2026-03-28T20:20:00+08:00"},
                                            }
                                        ]
                                    }
                                ],
                            },
                            {"price": {"currency": "CNY"}},
                        ]
                    },
                )

            if origin == "CGQ" and destination == "SHA":
                return httpx.Response(
                    200,
                    json={
                        "data": [
                            {
                                "price": {"currency": "CNY", "total": "580.00"},
                                "itineraries": [
                                    {
                                        "segments": [
                                            {
                                                "carrierCode": "MU",
                                                "number": "5222",
                                                "departure": {"at": "2026-03-30T17:40:00+08:00"},
                                                "arrival": {"at": "2026-03-30T19:20:00+08:00"},
                                            },
                                            {
                                                "carrierCode": "MU",
                                                "number": "5223",
                                                "departure": {"at": "2026-03-30T19:50:00+08:00"},
                                                "arrival": {"at": "2026-03-30T21:35:00+08:00"},
                                            },
                                        ]
                                    }
                                ],
                            }
                        ]
                    },
                )

        return httpx.Response(404, json={"error": "not found"})

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport, base_url="https://test.api.amadeus.com")
    connector = AmadeusConnector(
        client_id="cid",
        client_secret="secret",
        http_client=client,
    )

    route_profile = RouteProfile(origins=["SHA"], destination="CGQ")
    window = TravelWindow(
        outbound_date=date(2026, 3, 28),
        return_date=date(2026, 3, 30),
        working_days_used=1,
        non_working_days=2,
    )
    options = connector.search_fares(route_profile, window)

    assert len(options) == 2
    outbound = [item for item in options if item.leg_type == "outbound"][0]
    ret = [item for item in options if item.leg_type == "return"][0]

    assert outbound.provider == "amadeus"
    assert outbound.flight_number == "MU5111"
    assert outbound.price_cny == 650.50
    assert outbound.depart_at.isoformat() == "2026-03-28T18:10:00+08:00"

    assert ret.flight_number == "MU5222"
    assert ret.price_cny == 580.00
    assert ret.arrive_at.isoformat() == "2026-03-30T21:35:00+08:00"


def test_amadeus_connector_raises_connector_error_for_http_failures():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/security/oauth2/token":
            return httpx.Response(200, json={"access_token": "token-1", "expires_in": 1800})
        if request.url.path == "/v2/shopping/flight-offers":
            return httpx.Response(429, json={"errors": [{"detail": "rate limit"}]})
        return httpx.Response(404, json={"error": "not found"})

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport, base_url="https://test.api.amadeus.com")
    connector = AmadeusConnector(
        client_id="cid",
        client_secret="secret",
        http_client=client,
    )

    route_profile = RouteProfile(origins=["SHA"], destination="CGQ")
    window = TravelWindow(
        outbound_date=date(2026, 3, 28),
        return_date=date(2026, 3, 30),
        working_days_used=1,
        non_working_days=2,
    )

    with pytest.raises(ConnectorError, match="status 429"):
        connector.search_fares(route_profile, window)
