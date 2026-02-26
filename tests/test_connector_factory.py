from __future__ import annotations

from datetime import date

import pytest

from travel_advisor.connectors.amadeus import AmadeusConnector
from travel_advisor.connectors.base import ConnectorError
from travel_advisor.connectors.factory import MisconfiguredConnector, build_connector_from_env
from travel_advisor.connectors.sample import SampleConnector
from travel_advisor.models import RouteProfile, TravelWindow


def test_default_connector_mode_is_sample():
    connector = build_connector_from_env({})
    assert isinstance(connector, SampleConnector)


def test_amadeus_mode_returns_amadeus_connector():
    connector = build_connector_from_env(
        {
            "TRAVEL_ADVISOR_CONNECTOR_MODE": "amadeus",
            "TRAVEL_ADVISOR_AMADEUS_CLIENT_ID": "cid",
            "TRAVEL_ADVISOR_AMADEUS_CLIENT_SECRET": "secret",
            "TRAVEL_ADVISOR_AMADEUS_MAX_OFFERS_PER_LEG": "7",
        }
    )
    assert isinstance(connector, AmadeusConnector)


def test_amadeus_mode_without_credentials_raises_connector_error_on_search():
    connector = build_connector_from_env({"TRAVEL_ADVISOR_CONNECTOR_MODE": "amadeus"})
    assert isinstance(connector, MisconfiguredConnector)

    request_profile = RouteProfile(origins=["SHA"], destination="CGQ")
    window = TravelWindow(
        outbound_date=date(2026, 3, 28),
        return_date=date(2026, 3, 30),
        working_days_used=1,
        non_working_days=2,
    )

    with pytest.raises(ConnectorError, match="Amadeus connector misconfigured"):
        connector.search_fares(request_profile, window)
