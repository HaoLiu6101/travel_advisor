# Travel Price-Based Destination Advisor
## Requirements Document (Draft v0.1)

### 1. Purpose
Build an application that helps the user decide where to travel from Shanghai based primarily on flight ticket prices, constrained by China holiday/weekend calendars and short leave extensions.

### 2. Background
- User is based in Shanghai.
- User wants destination suggestions driven by fare opportunities.
- User can extend trips with up to 2 additional workdays around weekends/public holidays.
- User wants configurable destinations and preferences.
- User wants automatic fare collection for departures in 1-3 months ahead.

### 3. Product Goals
- Reduce manual effort of checking many travel platforms.
- Surface low-fare opportunities aligned with realistic travel windows.
- Send actionable alerts so user can book in preferred external apps.
- Start as personal-use tool, with possible future public release.

### 4. Target Users
- Primary: single user (personal use).
- Future: broader users with similar short-leave + holiday-based planning behavior.

### 5. In Scope (Functional Requirements)
- Route planning from Shanghai airports (`PVG`, `SHA`).
- Configurable destination profiles (initial interests include Japan, Korea, China cities, optional US West Coast).
- Calendar engine that generates candidate trip dates based on:
- China weekends and official public holidays.
- Up to 2 adjacent extension workdays.
- Fare search for candidate dates in rolling 1-3 month horizon.
- Aggregation of fares from multiple travel sources.
- Ranking results primarily by lowest fare.
- Alerting when:
- Fare is under configured threshold.
- Fare appears in top-N cheapest options.
- UI for:
- Managing destination/rule configuration.
- Viewing candidate dates.
- Viewing top fare options and source links.
- Viewing run/collection history.

### 6. Out of Scope (V1)
- In-app ticket booking and payment.
- Guaranteed complete coverage of all travel agencies.
- Fully global route coverage from day one.
- Advanced AI trip itinerary generation beyond fare-based destination decision.

### 7. Non-Functional Requirements
- Clean, intuitive UI/UX (Chinese-first experience).
- Configurable and explainable decision output ("why this alert was sent").
- Reliable scheduled runs (default twice daily, user-adjustable).
- Local-first operation on user machine.
- Scalable architecture path for future public deployment.
- Compliance-aware data collection strategy.

### 8. Data Acquisition Requirements
- Preferred strategy: official APIs/partner feeds first.
- Secondary strategy: controlled browser automation/AI agent fallback for gaps.
- Normalize and deduplicate fare data across sources.
- Store timestamped results for trend and alert logic.

### 9. Configuration Requirements
- Destination-level settings:
- Enable/disable route.
- Interest tags (shopping, relaxing, skiing, etc.).
- Budget threshold.
- Ranking/alert preferences.
- Global settings:
- Advance search window (1-3 months default).
- Max extension days (default 2).
- Schedule frequency.
- Alert channels (WeChat, email).

### 10. Success Criteria (Investigation KPIs)
- Alert precision: share of alerts considered useful by user.
- Time saved versus manual fare checking.
- Click-through rate from alert to booking platform.
- Weekly usage consistency over trial period.

### 11. Risks & Investigation Topics
- Legal/compliance limits on scraping/crawling across travel sites.
- Data freshness and fare volatility causing trust issues.
- Anti-bot mechanisms and maintenance burden for browser automation.
- Source coverage gaps across regions/routes.
- Notification channel implementation details (especially WeChat route).

### 12. Open Questions for Investigation
- Which providers can be integrated via stable APIs for Shanghai-focused routes?
- Which WeChat channel is best for personal alerts (WeCom bot vs service path)?
- What minimal UI level is enough for V1 before polishing?
- Should US West Coast be enabled in V1 or phase 2?
