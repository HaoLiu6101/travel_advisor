from __future__ import annotations

from fastapi import FastAPI

from .connectors.sample import SampleConnector
from .models import SearchRequest, SearchResponse
from .service import SearchService

app = FastAPI(title="Travel Advisor MVP", version="0.1.0")
service = SearchService(connector=SampleConnector())


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/search", response_model=SearchResponse)
def search(request: SearchRequest) -> SearchResponse:
    return service.search(request)
