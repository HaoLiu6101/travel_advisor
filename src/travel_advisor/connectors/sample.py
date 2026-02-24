from __future__ import annotations

import hashlib
from datetime import datetime, time, timedelta

from ..models import FlightOption, RouteProfile, TravelWindow
from .base import Connector


class SampleConnector(Connector):
    """Deterministic in-memory fixture connector for MVP development/testing."""

    provider_name = "sample"

    def search_fares(self, route_profile: RouteProfile, travel_window: TravelWindow) -> list[FlightOption]:
        options: list[FlightOption] = []

        outbound_slots = [time(17, 30), time(18, 10), time(19, 40), time(20, 25)]
        return_arrivals = [time(19, 30), time(21, 50), time(22, 35)]

        for origin in route_profile.origins:
            for slot in outbound_slots:
                depart_at = datetime.combine(travel_window.outbound_date, slot)
                arrive_at = depart_at + timedelta(hours=2, minutes=20)
                options.append(
                    FlightOption(
                        leg_type="outbound",
                        origin=origin,
                        destination=route_profile.destination,
                        depart_at=depart_at,
                        arrive_at=arrive_at,
                        provider=self.provider_name,
                        flight_number=f"SC{1000 + self._stable_mod(origin + slot.isoformat(), 8999)}",
                        price_cny=float(
                            380
                            + self._stable_mod(f"out-{origin}-{travel_window.outbound_date}", 200)
                            + self._slot_bias(slot)
                        ),
                    )
                )

            for arrival_slot in return_arrivals:
                arrive_at = datetime.combine(travel_window.return_date, arrival_slot)
                depart_at = arrive_at - timedelta(hours=2, minutes=30)
                options.append(
                    FlightOption(
                        leg_type="return",
                        origin=route_profile.destination,
                        destination=origin,
                        depart_at=depart_at,
                        arrive_at=arrive_at,
                        provider=self.provider_name,
                        flight_number=f"SC{1000 + self._stable_mod(origin + arrival_slot.isoformat(), 8999)}",
                        price_cny=float(
                            260
                            + self._stable_mod(f"ret-{origin}-{travel_window.return_date}", 170)
                            + self._return_slot_bias(arrival_slot)
                        ),
                    )
                )

        return options

    @staticmethod
    def _stable_mod(seed: str, mod: int) -> int:
        digest = hashlib.md5(seed.encode("utf-8")).hexdigest()  # nosec B324: deterministic fixture only
        return int(digest[:8], 16) % mod

    @staticmethod
    def _slot_bias(slot: time) -> int:
        if slot.hour >= 20:
            return 40
        if slot.hour >= 19:
            return 20
        if slot.hour >= 18:
            return 10
        return 0

    @staticmethod
    def _return_slot_bias(slot: time) -> int:
        if slot.hour >= 22:
            return 50
        if slot.hour >= 21:
            return 35
        return 0
