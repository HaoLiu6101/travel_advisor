from __future__ import annotations

import os
from typing import Mapping

from ..models import FlightOption, RouteProfile, TravelWindow
from .amadeus import AmadeusConnector
from .base import Connector, ConnectorError
from .sample import SampleConnector


class MisconfiguredConnector(Connector):
    is_real_connector = True

    def __init__(self, message: str):
        self._message = message

    def search_fares(self, route_profile: RouteProfile, travel_window: TravelWindow) -> list[FlightOption]:
        raise ConnectorError(self._message)


def build_connector_from_env(env: Mapping[str, str] | None = None) -> Connector:
    active_env = env if env is not None else os.environ
    mode = active_env.get("TRAVEL_ADVISOR_CONNECTOR_MODE", "sample").strip().lower()

    if mode in {"", "sample"}:
        return SampleConnector()

    if mode == "amadeus":
        client_id = active_env.get("TRAVEL_ADVISOR_AMADEUS_CLIENT_ID", "").strip()
        client_secret = active_env.get("TRAVEL_ADVISOR_AMADEUS_CLIENT_SECRET", "").strip()
        if not client_id or not client_secret:
            return MisconfiguredConnector(
                "Amadeus connector misconfigured: set TRAVEL_ADVISOR_AMADEUS_CLIENT_ID and "
                "TRAVEL_ADVISOR_AMADEUS_CLIENT_SECRET."
            )

        base_url = active_env.get("TRAVEL_ADVISOR_AMADEUS_BASE_URL", "https://test.api.amadeus.com").strip()
        timeout_seconds = _read_float(
            active_env,
            key="TRAVEL_ADVISOR_AMADEUS_TIMEOUT_SECONDS",
            default=12.0,
            minimum=1.0,
        )
        max_offers_per_leg = _read_int(
            active_env,
            key="TRAVEL_ADVISOR_AMADEUS_MAX_OFFERS_PER_LEG",
            default=5,
            minimum=1,
        )
        return AmadeusConnector(
            client_id=client_id,
            client_secret=client_secret,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            max_offers_per_leg=max_offers_per_leg,
        )

    return MisconfiguredConnector(
        "Unsupported connector mode. Set TRAVEL_ADVISOR_CONNECTOR_MODE to 'sample' or 'amadeus'."
    )


def _read_int(env: Mapping[str, str], *, key: str, default: int, minimum: int) -> int:
    raw = env.get(key)
    if raw is None:
        return default
    try:
        parsed = int(raw)
    except ValueError:
        return default
    return parsed if parsed >= minimum else default


def _read_float(env: Mapping[str, str], *, key: str, default: float, minimum: float) -> float:
    raw = env.get(key)
    if raw is None:
        return default
    try:
        parsed = float(raw)
    except ValueError:
        return default
    return parsed if parsed >= minimum else default
