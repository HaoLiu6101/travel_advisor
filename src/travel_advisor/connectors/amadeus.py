from __future__ import annotations

import hashlib
import time
from datetime import datetime
from typing import Any

import httpx

from ..models import FlightOption, RouteProfile, TravelWindow
from .base import Connector, ConnectorError


class AmadeusConnector(Connector):
    provider_name = "amadeus"
    is_real_connector = True

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        *,
        base_url: str = "https://test.api.amadeus.com",
        timeout_seconds: float = 12.0,
        max_offers_per_leg: int = 5,
        http_client: httpx.Client | None = None,
    ):
        self._client_id = client_id
        self._client_secret = client_secret
        self._max_offers_per_leg = max(1, max_offers_per_leg)
        self._client = http_client or httpx.Client(base_url=base_url, timeout=timeout_seconds)
        self._access_token: str | None = None
        self._token_expires_at_epoch: float = 0.0

    def search_fares(self, route_profile: RouteProfile, travel_window: TravelWindow) -> list[FlightOption]:
        access_token = self._get_access_token()
        options: list[FlightOption] = []

        for origin in route_profile.origins:
            options.extend(
                self._search_leg(
                    leg_type="outbound",
                    origin=origin,
                    destination=route_profile.destination,
                    departure_date=travel_window.outbound_date.isoformat(),
                    access_token=access_token,
                )
            )
            options.extend(
                self._search_leg(
                    leg_type="return",
                    origin=route_profile.destination,
                    destination=origin,
                    departure_date=travel_window.return_date.isoformat(),
                    access_token=access_token,
                )
            )

        return options

    def _get_access_token(self) -> str:
        now = time.time()
        if self._access_token and now < self._token_expires_at_epoch - 30:
            return self._access_token

        form = {
            "grant_type": "client_credentials",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }

        try:
            response = self._client.post("/v1/security/oauth2/token", data=form)
        except httpx.HTTPError as exc:
            raise ConnectorError(f"Amadeus token request failed: {exc}") from exc

        if response.status_code >= 400:
            raise ConnectorError(
                f"Amadeus token request failed with status {response.status_code}"
            )

        payload = response.json()
        access_token = payload.get("access_token")
        expires_in = payload.get("expires_in")
        if not access_token or not isinstance(access_token, str):
            raise ConnectorError("Amadeus token response missing access_token")

        expires_seconds = 1800
        if isinstance(expires_in, int):
            expires_seconds = expires_in
        elif isinstance(expires_in, str) and expires_in.isdigit():
            expires_seconds = int(expires_in)

        self._access_token = access_token
        self._token_expires_at_epoch = now + max(60, expires_seconds)
        return access_token

    def _search_leg(
        self,
        *,
        leg_type: str,
        origin: str,
        destination: str,
        departure_date: str,
        access_token: str,
    ) -> list[FlightOption]:
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure_date,
            "adults": 1,
            "currencyCode": "CNY",
            "max": self._max_offers_per_leg,
        }

        try:
            response = self._client.get("/v2/shopping/flight-offers", headers=headers, params=params)
        except httpx.HTTPError as exc:
            raise ConnectorError(f"Amadeus fare search failed: {exc}") from exc

        if response.status_code >= 400:
            raise ConnectorError(
                f"Amadeus fare search failed with status {response.status_code}"
            )

        payload = response.json()
        offers = payload.get("data", [])
        if not isinstance(offers, list):
            return []

        mapped: list[FlightOption] = []
        for offer in offers:
            option = self._map_offer(
                offer=offer,
                leg_type=leg_type,
                origin=origin,
                destination=destination,
            )
            if option is not None:
                mapped.append(option)
        return mapped

    def _map_offer(
        self,
        *,
        offer: dict[str, Any],
        leg_type: str,
        origin: str,
        destination: str,
    ) -> FlightOption | None:
        if not isinstance(offer, dict):
            return None

        itineraries = offer.get("itineraries")
        if not isinstance(itineraries, list) or not itineraries:
            return None
        first_itinerary = itineraries[0]
        if not isinstance(first_itinerary, dict):
            return None

        segments = first_itinerary.get("segments")
        if not isinstance(segments, list) or not segments:
            return None
        first_segment = segments[0]
        last_segment = segments[-1]
        if not isinstance(first_segment, dict) or not isinstance(last_segment, dict):
            return None

        depart_at_raw = _nested_get(first_segment, ("departure", "at"))
        arrive_at_raw = _nested_get(last_segment, ("arrival", "at"))
        if not isinstance(depart_at_raw, str) or not isinstance(arrive_at_raw, str):
            return None

        try:
            depart_at = _parse_datetime(depart_at_raw)
            arrive_at = _parse_datetime(arrive_at_raw)
        except ValueError:
            return None

        price_data = offer.get("price")
        if not isinstance(price_data, dict):
            return None
        raw_price = price_data.get("grandTotal") or price_data.get("total")
        if raw_price is None:
            return None

        try:
            price_cny = float(raw_price)
        except (TypeError, ValueError):
            return None

        carrier = first_segment.get("carrierCode")
        flight_no = first_segment.get("number")
        if isinstance(carrier, str) and isinstance(flight_no, str) and carrier and flight_no:
            flight_number = f"{carrier}{flight_no}"
        else:
            flight_number = self._fallback_flight_number(origin, destination, depart_at_raw, leg_type)

        currency = price_data.get("currency")
        currency_code = currency if isinstance(currency, str) and currency else "CNY"

        return FlightOption(
            leg_type=leg_type,
            origin=origin,
            destination=destination,
            depart_at=depart_at,
            arrive_at=arrive_at,
            provider=self.provider_name,
            flight_number=flight_number,
            price_cny=price_cny,
            currency=currency_code,
        )

    @staticmethod
    def _fallback_flight_number(origin: str, destination: str, depart_at_raw: str, leg_type: str) -> str:
        seed = f"{origin}-{destination}-{depart_at_raw}-{leg_type}"
        digest = hashlib.md5(seed.encode("utf-8")).hexdigest()  # nosec B324 deterministic fallback id
        return f"AD{digest[:6].upper()}"


def _nested_get(data: dict[str, Any], path: tuple[str, ...]) -> Any:
    current: Any = data
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _parse_datetime(raw: str) -> datetime:
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    return datetime.fromisoformat(raw)
