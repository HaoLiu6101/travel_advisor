from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .models import FlightOption, ItineraryPair


@dataclass
class PairBuildResult:
    pairs: list[ItineraryPair]
    dropped_reason_counts: dict[str, int]


def build_itinerary_pairs(flights: list[FlightOption]) -> PairBuildResult:
    outbound = [f for f in flights if f.leg_type == "outbound"]
    returns = [f for f in flights if f.leg_type == "return"]

    drops: Counter[str] = Counter()
    pairs: list[ItineraryPair] = []

    for out in outbound:
        for ret in returns:
            if ret.depart_at <= out.arrive_at:
                drops["return_before_outbound_arrival"] += 1
                continue
            if ret.origin != out.destination:
                drops["return_origin_mismatch"] += 1
                continue
            if ret.destination not in {out.origin, "SHA", "PVG"}:
                drops["return_destination_not_supported"] += 1
                continue
            pairs.append(
                ItineraryPair(
                    outbound=out,
                    return_flight=ret,
                    total_price_cny=round(out.price_cny + ret.price_cny, 2),
                )
            )

    return PairBuildResult(pairs=pairs, dropped_reason_counts=dict(drops))
