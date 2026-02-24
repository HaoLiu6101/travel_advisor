from datetime import datetime, timedelta

from travel_advisor.models import FlightOption, ItineraryPair, TimePreferences
from travel_advisor.scoring import rank_itineraries


def _pair(price: float, out_hour: int, ret_hour: int) -> ItineraryPair:
    outbound = FlightOption(
        leg_type="outbound",
        origin="SHA",
        destination="CGQ",
        depart_at=datetime(2026, 3, 17, out_hour, 0),
        arrive_at=datetime(2026, 3, 17, out_hour + 2, 10),
        provider="test",
        flight_number="X1",
        price_cny=price / 2,
    )
    ret = FlightOption(
        leg_type="return",
        origin="CGQ",
        destination="SHA",
        depart_at=datetime(2026, 3, 20, ret_hour - 2, 0),
        arrive_at=datetime(2026, 3, 20, ret_hour, 0),
        provider="test",
        flight_number="X2",
        price_cny=price / 2,
    )
    return ItineraryPair(outbound=outbound, return_flight=ret, total_price_cny=price)


def test_cheaper_beats_much_pricier_under_70_30_weighting():
    prefs = TimePreferences()
    cheap_bad_time = _pair(800, 17, 19)
    pricey_good_time = _pair(1300, 20, 22)

    ranked = rank_itineraries([pricey_good_time, cheap_bad_time], prefs)
    assert ranked[0].total_price_cny == 800


def test_top_five_limit_and_deterministic_tie_breaker():
    prefs = TimePreferences()
    pairs = [_pair(900, 18, 22) for _ in range(7)]

    # force deterministic ordering by staggering outbound minute in already-equal scores
    for index, pair in enumerate(pairs):
        pair.outbound.depart_at = pair.outbound.depart_at + timedelta(minutes=index)

    ranked = rank_itineraries(pairs, prefs)
    top_five = ranked[:5]

    assert len(top_five) == 5
    assert top_five[0].outbound.depart_at.minute == 0
    assert top_five[-1].outbound.depart_at.minute == 4
