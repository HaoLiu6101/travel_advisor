from __future__ import annotations

import json
from pathlib import Path

import typer

from .connectors.sample import SampleConnector
from .models import SearchRequest
from .profiles import request_from_profile
from .service import SearchService

app = typer.Typer(help="Travel Advisor CLI")


@app.callback()
def main() -> None:
    """Travel Advisor CLI entrypoint."""


@app.command("search")
def search_command(
    profile: str = typer.Option("changchun_weekend_plus", help="Preset profile name"),
    request_json: Path | None = typer.Option(None, help="Path to JSON request override"),
    output: Path | None = typer.Option(None, help="Path to write JSON result"),
) -> None:
    if request_json is not None:
        payload = json.loads(request_json.read_text(encoding="utf-8"))
        request = SearchRequest.model_validate(payload)
    else:
        request = request_from_profile(profile)

    service = SearchService(connector=SampleConnector())
    response = service.search(request)
    result_json = response.model_dump_json(indent=2)

    if output is not None:
        output.write_text(result_json, encoding="utf-8")
        typer.echo(f"Wrote results to {output}")
        return

    typer.echo(result_json)


def run() -> None:
    app()


if __name__ == "__main__":
    run()
