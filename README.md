# Travel Advisor MVP

FastAPI + CLI MVP that reproduces a Piggy-like weekend-to-Monday fare selection flow:
- Weekend/holiday anchored date generation with up to 2 extension workdays
- Changchun (`CGQ`) default destination profile
- Soft time-slot preferences (weekday outbound later in the day, return around 22:00)
- Ranked itinerary output with explainable score breakdown

## Setup with uv (venv + deps)

### 1. Install uv

macOS/Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows (PowerShell):

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Or with `pipx`:

```bash
pipx install uv
```

### 2. Create/sync virtual environment

From the project root:

```bash
uv venv .venv
uv sync --extra dev
```

Activate (optional, `uv run` below does not require activation):

```bash
source .venv/bin/activate
```

### 3. Run API

```bash
uv run uvicorn travel_advisor.api:app --reload
```

### 4. Run CLI

```bash
uv run travel-advisor search --profile changchun_weekend_plus
```

### 5. Run tests

```bash
uv run pytest
```
