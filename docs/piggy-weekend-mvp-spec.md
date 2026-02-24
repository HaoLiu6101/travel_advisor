# Piggy-Like Weekend-to-Monday Fare Flow MVP Spec

## 1. User Story (Concrete)
As a Shanghai traveler, I want to start from weekend-friendly dates, optionally extend by up to 2 workdays, lock destination to Changchun by default, prefer later weekday outbound flights, and prefer return arrival around 22:00 so I can quickly choose a practical and low-price round trip.

## 2. Locked Defaults
- Origins: `SHA`, `PVG`
- Default destination: `CGQ` (Changchun), still configurable
- Date window: `1-3` months ahead
- Trip anchor: `weekend_or_holiday`
- Max extension workdays: `2`
- Time preferences (soft score):
  - Weekday outbound departure after `18:00`
  - Return arrival target `22:00`
  - Return arrival soft window `21:00-23:00`
- Result limit: top `5` itinerary pairs
- Ranking weights: price `70%`, time preference `30%`

## 3. Public Contracts

### API
`POST /api/search`

Request body (`SearchRequest`):
- `origins`: default `["SHA","PVG"]`
- `destination`: default `"CGQ"`
- `profile_name`: default `"changchun_weekend_plus"`
- `date_window_months`: `"1-3"`
- `max_extension_workdays`: integer
- `trip_anchor`: `"weekend_or_holiday"`
- `time_preferences` (`TimePreferences`)
- `result_limit`: integer
- `holiday_dates`: optional date list
- `make_up_workdays`: optional date list

Response body (`SearchResponse`):
- `results: RankedItinerary[]`
- `debug`:
  - `candidate_dates_count`
  - `evaluated_pairs_count`
  - `scoring_weights`
  - `dropped_reason_counts`
  - `warnings`

### CLI
- Command: `travel-advisor search --profile changchun_weekend_plus`
- Optional JSON override input: `--request-json <path>`
- JSON output file: `--output <path>`

## 4. Core Types
- `RouteProfile`
- `TravelWindow`
- `FlightOption`
- `ItineraryPair`
- `RankingScoreBreakdown`
- `RankedItinerary`
- `Connector` interface: `search_fares(route_profile, travel_window) -> list[FlightOption]`

## 5. Engine Rules

### Calendar engine
Generate candidate travel windows in the configured horizon where:
- the interval contains at least 2 non-working days (weekend/holiday), and
- working-day usage in the interval is `<= max_extension_workdays`.

Weekend make-up workdays can be explicitly marked in `make_up_workdays` and are treated as working days.

### Pair builder
Within each travel window, outbound and return options are combined into legal itinerary pairs. Invalid combinations are dropped with reason-code counters.

### Scoring and ranking
- `price_score`: lowest fare baseline with penalty for price gap.
- `time_score`:
  - weekday outbound preference applies only on Monday-Friday,
  - weekend outbound has no time bias,
  - return arrival is rewarded near `22:00`, with soft preference in `21:00-23:00`.
- final score = `0.7 * price_score + 0.3 * time_score`
- top-N ranked results returned with explanation reason codes.

## 6. Connector Strategy
V1 is connector-pluggable and ships with a deterministic `SampleConnector` fixture for Shanghai -> Changchun development and tests. Real provider connectors are phase-2.

## 7. Acceptance Criteria
1. API accepts empty request and returns normalized response shape with debug block.
2. CLI `travel-advisor search --profile changchun_weekend_plus` prints JSON result.
3. Calendar engine supports:
- weekend-only windows,
- weekend + 1 workday extension,
- weekend + 2 workday extension,
- make-up workday exclusion behavior.
4. Scoring behavior validates:
- weekday outbound `18:10` preferred over `17:30` when prices are equal,
- weekend outbound has no late-day bias,
- return `21:50` can beat `19:30` when prices are close.
5. Ranking behavior validates:
- much cheaper option beats much pricier option under 70/30 weighting,
- top-5 limit and deterministic tie ordering.
6. Empty-result path returns `results: []` with non-empty warning list.
