from datetime import datetime

from travel_advisor.models import FlightOption, ItineraryPair, TimePreferences
from travel_advisor.scoring import rank_itineraries


def _flight(leg, depart, arrive, price, origin, destination):
    return FlightOption(
        leg_type=leg,
        origin=origin,
        destination=destination,
        depart_at=depart,
        arrive_at=arrive,
        provider="test",
        flight_number="T1",
        price_cny=price,
    )


def test_weekday_outbound_time_preference_scoring():
    prefs = TimePreferences()

    pair_1730 = ItineraryPair(
        outbound=_flight(
            "outbound",
            datetime(2026, 3, 16, 17, 30),
            datetime(2026, 3, 16, 19, 40),
            500,
            "SHA",
            "CGQ",
        ),
        return_flight=_flight(
            "return",
            datetime(2026, 3, 18, 19, 0),
            datetime(2026, 3, 18, 21, 50),
            300,
            "CGQ",
            "SHA",
        ),
        total_price_cny=800,
    )
    pair_1810 = pair_1730.model_copy(
        update={
            "outbound": _flight(
                "outbound",
                datetime(2026, 3, 16, 18, 10),
                datetime(2026, 3, 16, 20, 20),
                500,
                "SHA",
                "CGQ",
            )
        }
    )

    ranked = rank_itineraries([pair_1730, pair_1810], prefs)
    assert ranked[0].outbound.depart_at.hour == 18


def test_weekend_outbound_no_time_bias():
    prefs = TimePreferences()

    pair_1600 = ItineraryPair(
        outbound=_flight(
            "outbound",
            datetime(2026, 3, 14, 16, 0),
            datetime(2026, 3, 14, 18, 0),
            500,
            "SHA",
            "CGQ",
        ),
        return_flight=_flight(
            "return",
            datetime(2026, 3, 16, 19, 30),
            datetime(2026, 3, 16, 22, 0),
            300,
            "CGQ",
            "SHA",
        ),
        total_price_cny=800,
    )
    pair_2000 = pair_1600.model_copy(
        update={
            "outbound": _flight(
                "outbound",
                datetime(2026, 3, 14, 20, 0),
                datetime(2026, 3, 14, 22, 0),
                500,
                "SHA",
                "CGQ",
            )
        }
    )

    ranked = rank_itineraries([pair_1600, pair_2000], prefs)
    assert ranked[0].score.time_score == ranked[1].score.time_score


def test_return_2150_beats_1930_when_prices_close():
    prefs = TimePreferences()

    near_target = ItineraryPair(
        outbound=_flight(
            "outbound",
            datetime(2026, 3, 17, 18, 30),
            datetime(2026, 3, 17, 20, 30),
            500,
            "SHA",
            "CGQ",
        ),
        return_flight=_flight(
            "return",
            datetime(2026, 3, 20, 19, 30),
            datetime(2026, 3, 20, 21, 50),
            500,
            "CGQ",
            "SHA",
        ),
        total_price_cny=1000,
    )
    cheap_but_early = near_target.model_copy(
        update={
            "return_flight": _flight(
                "return",
                datetime(2026, 3, 20, 17, 10),
                datetime(2026, 3, 20, 19, 30),
                480,
                "CGQ",
                "SHA",
            ),
            "total_price_cny": 980,
        }
    )

    ranked = rank_itineraries([cheap_but_early, near_target], prefs)
    assert ranked[0].return_flight.arrive_at.hour == 21
    assert ranked[0].return_flight.arrive_at.minute == 50
