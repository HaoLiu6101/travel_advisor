# AGENTS.md

## Purpose
This repository implements a local-first MVP for a fare-first travel advisor focused on Shanghai-origin trips. The implemented scope is the Piggy-like weekend-to-Monday search flow with explainable ranking.

## Source Of Truth (Priority Order)
1. `README.md`: setup and day-to-day run/test commands.
2. `docs/piggy-weekend-mvp-spec.md`: locked MVP behavior and acceptance criteria.
3. `tests/`: executable contract for behavior.
4. `docs/travel-fare-advisor-plan.md` and `docs/requirements-investigation.md`: future roadmap and broader product direction.

Use the first three as implementation truth. Treat plan/requirements docs as forward-looking unless explicitly requested.

## Environment And Setup
- Python: `>=3.11` (see `pyproject.toml`)
- Package/dependency manager: `uv`
- Install deps:
  - `uv venv .venv`
  - `uv sync --extra dev`

## Run Commands
- API server:
  - `uv run uvicorn travel_advisor.api:app --reload`
- CLI:
  - `uv run travel-advisor search --profile changchun_weekend_plus`
- Tests:
  - `uv run pytest`

## Current Public Interfaces
- API:
  - `GET /health`
  - `POST /api/search` (request model: `SearchRequest`, response model: `SearchResponse`)
- CLI:
  - `travel-advisor search --profile <name> [--request-json <path>] [--output <path>]`

## Locked MVP Defaults And Rules
Keep these defaults unless a task explicitly changes product behavior.

- Default origins: `["SHA", "PVG"]`
- Default destination: `"CGQ"`
- Default profile name: `"changchun_weekend_plus"`
- Date window: `"1-3"` months
- Trip anchor: `"weekend_or_holiday"`
- Max extension workdays: `2`
- Time preferences:
  - outbound weekday depart after `18:00`
  - return target arrival `22:00`
  - return soft window `21:00-23:00`
- Result limit: top `5`
- Scoring weights: price `0.7`, time `0.3`

Core engine rules:
- Candidate windows must contain at least 2 non-working days.
- Working days used in a window must be `<= max_extension_workdays`.
- `make_up_workdays` are treated as working days even on weekends.
- Ranking uses weighted price/time score and deterministic sorting for ties.

## Code Map
- `src/travel_advisor/api.py`: FastAPI app and endpoints.
- `src/travel_advisor/cli.py`: Typer CLI entrypoints.
- `src/travel_advisor/models.py`: request/response/domain models and validation.
- `src/travel_advisor/service.py`: orchestrates window generation, fare search, pairing, ranking.
- `src/travel_advisor/calendar_engine.py`: holiday/weekend + extension-day window generation.
- `src/travel_advisor/pair_builder.py`: outbound/return pairing and dropped-reason counts.
- `src/travel_advisor/scoring.py`: price/time scoring + rank/tie-breaking.
- `src/travel_advisor/connectors/base.py`: connector interface.
- `src/travel_advisor/connectors/sample.py`: deterministic fixture connector used by API/CLI/tests.
- `src/travel_advisor/profiles.py`: preset request profiles.

## Change Guidelines For Future Agents
- Preserve API and CLI contracts unless requested to version/change them.
- Keep behavior deterministic where tests rely on ordering.
- When changing calendar, pairing, or scoring logic:
  - update/add focused tests under `tests/`
  - ensure acceptance behaviors in `docs/piggy-weekend-mvp-spec.md` still hold (or update docs if intentionally changed)
- Keep implementation local-first and MVP-focused; avoid introducing partial roadmap components (scheduler/DB/dashboard/notifiers) unless explicitly requested.

## Validation Checklist Before Finishing
1. Run `uv run pytest`.
2. If API-facing changes were made, smoke-test:
   - `GET /health`
   - `POST /api/search` with `{}` payload.
3. Ensure any contract changes are reflected in docs/tests.
