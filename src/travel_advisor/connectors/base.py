from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import FlightOption, RouteProfile, TravelWindow


class Connector(ABC):
    @abstractmethod
    def search_fares(self, route_profile: RouteProfile, travel_window: TravelWindow) -> list[FlightOption]:
        """Return normalized fare options for a single travel window."""
