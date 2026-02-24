# Travel Fare Advisor (Shanghai) - Decision-Complete Build Plan

## MVP Addendum (Implemented)
The concrete Piggy-like weekend-to-Monday MVP scope and acceptance criteria are captured in [piggy-weekend-mvp-spec.md](./piggy-weekend-mvp-spec.md).

## Summary
Build a local-first, backend-first application that automatically finds flight fares from Shanghai to configurable destinations (China, Japan, Korea in v1), using a holiday/weekend-aware date engine and sends alerts when deals meet your rules.
V1 is for personal use on your machine, with a clean path to later public deployment.

## Scope (Locked)
1. Origin: `SHA` + `PVG` (Shanghai airports).
2. Destinations: configurable route profiles; initial set includes China cities + Japan + Korea.
3. Date logic: only trips anchored on China weekends/public holidays, with up to 2 extension workdays.
4. Search window: departures in next 1-3 months.
5. Decision logic: lowest-fare-first, plus alert by threshold + top-N ranking.
6. Booking: out of scope; app only alerts and links to source.
7. UI language: Chinese-first.

## Architecture (Locked)
1. Backend: `Python 3.12 + FastAPI`.
2. Scheduler: `APScheduler` (twice daily by default; user-adjustable cron).
3. Data store (local-first): `SQLite` via `SQLModel` + Alembic migrations.
4. Connector layer:
- API connectors first (preferred/compliant providers).
- Crawler connectors fallback (Playwright) only where API coverage is missing.
- Unified normalized fare schema across connectors.
5. Notification layer:
- Email SMTP notifier.
- WeChat notifier adapter interface (implemented when your preferred channel is finalized, e.g., WeCom bot/service account).
6. Frontend (v1): lightweight responsive web dashboard served by FastAPI templates (config + run history + deals list).
7. Future public scale path: swap SQLite to Postgres, move scheduler/worker to containerized service, keep API contracts unchanged.

## Public APIs / Interfaces / Types (Locked)
1. REST endpoints:
- `POST /api/runs/collect` trigger one collection run.
- `GET /api/runs` list run history/status.
- `GET /api/deals` query normalized fare results with filters.
- `POST /api/routes` create route profile.
- `PUT /api/routes/{id}` update route profile.
- `GET /api/routes` list profiles.
- `POST /api/alerts/test` send test alert.
- `GET /api/calendar/candidates` preview generated travel dates.
2. Core types:
- `RouteProfile`: origin, destination, tags, budget cap, trip-length preference, enable flags.
- `TravelWindowRule`: min/max advance months, max_extension_workdays.
- `FareQuote`: provider, fetched_at, outbound_date, return_date, price_total, currency, deep_link, confidence.
- `DealDecision`: rank, threshold_hit, reason_codes.
3. Connector interface:
- `search_fares(route_profile, candidate_dates) -> list[FareQuote]`
- `healthcheck() -> ConnectorHealth`
4. Notification interface:
- `send_alert(deal_batch, channel_config) -> DeliveryResult`

## Calendar & Fare Decision Logic (Locked)
1. Generate candidate trips from China weekends/public holidays only.
2. Allow adjacent extension days up to 2 workdays total per trip.
3. Generate trip options for 1-3 months ahead rolling window.
4. For each route/date pair, query providers and normalize prices to CNY.
5. Deduplicate by same route/date/provider-link fingerprint.
6. Rank by lowest total fare.
7. Trigger alert if:
- price <= route threshold, or
- result is in top-N cheapest for this run.

## UX Plan (Nice UI/UX without delaying delivery)
1. V1 dashboard pages:
- `概览`: latest top deals, trend sparkline, last run status.
- `路线配置`: route profiles, budget thresholds, tags (shopping/relax/skiing/etc.).
- `日历预览`: generated eligible travel dates.
- `运行记录`: provider success/failure and data freshness.
2. UX behaviors:
- One-click "Run now".
- Clear source attribution and booking deep link.
- Explainability badges: "低于阈值", "本轮Top-N", "节假日延展".
- Mobile-friendly responsive layout.

## Implementation Phases
1. Phase 0 - Foundations
- Repo scaffold, env config, migration setup, logging.
- Domain models + normalized schemas.
2. Phase 1 - Calendar + Rules Engine
- China holiday/weekend generator.
- Extension-day constraint engine.
- Candidate-date preview API.
3. Phase 2 - Connectors
- Implement API connector(s) first.
- Add fallback crawler connector(s) with retry/rate-limit.
- Normalize/deduplicate fare pipeline.
4. Phase 3 - Decision + Alerts
- Ranking/threshold evaluator.
- Email notifier + WeChat adapter skeleton + test endpoint.
5. Phase 4 - Web Dashboard
- Config CRUD, run history, deals table, filters, explanation tags.
6. Phase 5 - Hardening
- Caching, observability, connector health checks, backoff, anti-block safeguards.

## Test Cases and Scenarios
1. Calendar correctness:
- National holiday week, weekend-only, and edge month boundaries.
- Verify max 2 extension workdays constraint is never violated.
2. Fare pipeline:
- Multi-provider normalization to CNY.
- Dedup logic across connector duplicates.
- Missing/partial provider response handling.
3. Decision logic:
- Threshold hit only, Top-N only, both hit.
- Ties in fare ranking.
4. Alerting:
- Delivery success/failure retries.
- No duplicate alerts for same deal within cooldown window.
5. API and UI:
- Route profile CRUD validation.
- Deals filtering, pagination, and explainability fields.
6. Non-functional:
- Scheduler twice-daily stability.
- Connector timeout/backoff behavior.
- Local machine restart recovery.

## Assumptions and Defaults
1. Personal-use first; local execution is default.
2. Collection cadence default is twice daily, but configurable.
3. "All travel agents" is interpreted as "multiple major providers through a hybrid connector strategy," not literal exhaustive crawling.
4. Booking remains external to this app.
5. Chinese-first UI/content.
6. Compliance-first policy: prefer official APIs/allowed access; crawler usage is restricted to permitted terms.

## Deliverables for V1
1. Running FastAPI service with scheduler and SQLite.
2. Configurable route profiles and calendar-rule engine.
3. At least one API connector + one fallback crawler connector integrated via common interface.
4. Deals ranking and threshold alerts (email + WeChat-ready interface).
5. Chinese-first responsive dashboard for config, run control, and deal review.
