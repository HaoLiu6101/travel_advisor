from __future__ import annotations

from datetime import datetime

from .models import ItineraryPair, RankedItinerary, RankingScoreBreakdown, TimePreferences, hhmm_to_minutes


def rank_itineraries(
    pairs: list[ItineraryPair],
    preferences: TimePreferences,
    price_weight: float = 0.7,
    time_weight: float = 0.3,
) -> list[RankedItinerary]:
    if not pairs:
        return []

    min_price = min(pair.total_price_cny for pair in pairs)
    ranked: list[RankedItinerary] = []

    for pair in pairs:
        price_score = _price_score(pair.total_price_cny, min_price)
        time_score, reason_codes = _time_score(pair, preferences)
        final_score = round(price_weight * price_score + time_weight * time_score, 2)
        ranked.append(
            RankedItinerary(
                outbound=pair.outbound,
                return_flight=pair.return_flight,
                total_price_cny=pair.total_price_cny,
                score=RankingScoreBreakdown(
                    price_score=round(price_score, 2),
                    time_score=round(time_score, 2),
                    final_score=final_score,
                ),
                reason_codes=reason_codes,
            )
        )

    ranked.sort(
        key=lambda item: (
            -item.score.final_score,
            item.total_price_cny,
            item.outbound.depart_at,
            item.return_flight.arrive_at,
        )
    )
    return ranked


def _price_score(price: float, min_price: float) -> float:
    if min_price <= 0:
        return 0.0
    gap_ratio = max(0.0, (price - min_price) / min_price)
    # 0% gap -> 100, 10% gap -> 50, >=20% gap -> 0
    return max(0.0, 100.0 - gap_ratio * 500.0)


def _time_score(pair: ItineraryPair, preferences: TimePreferences) -> tuple[float, list[str]]:
    reasons: list[str] = []

    outbound_score = _outbound_score(pair.outbound.depart_at, preferences.outbound_weekday_depart_after, reasons)
    return_score = _return_score(
        pair.return_flight.arrive_at,
        preferences.return_arrival_target,
        preferences.return_arrival_soft_window,
        reasons,
    )

    combined = (outbound_score + return_score) / 2.0
    return combined, reasons


def _outbound_score(depart_at: datetime, threshold_hhmm: str, reasons: list[str]) -> float:
    if depart_at.weekday() >= 5:
        reasons.append("outbound_weekend_no_time_bias")
        return 100.0

    threshold_minutes = hhmm_to_minutes(threshold_hhmm)
    depart_minutes = depart_at.hour * 60 + depart_at.minute
    if depart_minutes >= threshold_minutes:
        reasons.append("weekday_outbound_preference_matched")
        return 100.0

    delta = threshold_minutes - depart_minutes
    reasons.append("weekday_outbound_preference_not_met")
    # 4 hours early or more -> 0
    return max(0.0, 100.0 - (delta / 240.0) * 100.0)


def _return_score(
    arrive_at: datetime,
    target_hhmm: str,
    soft_window: tuple[str, str],
    reasons: list[str],
) -> float:
    target = hhmm_to_minutes(target_hhmm)
    window_start = hhmm_to_minutes(soft_window[0])
    window_end = hhmm_to_minutes(soft_window[1])
    arrival = arrive_at.hour * 60 + arrive_at.minute

    if window_start <= arrival <= window_end:
        reasons.append("return_arrival_in_soft_window")
        diff = abs(arrival - target)
        # at target -> 100, at +-60 minutes -> 50
        return max(50.0, 100.0 - (diff / 60.0) * 50.0)

    reasons.append("return_arrival_outside_soft_window")
    if arrival < window_start:
        outside_delta = window_start - arrival
    else:
        outside_delta = arrival - window_end

    # beyond soft window, decay from 50 down to 0 over 2 hours
    return max(0.0, 50.0 - (outside_delta / 120.0) * 50.0)
