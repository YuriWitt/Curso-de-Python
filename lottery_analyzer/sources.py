"""Leitura de arquivos e sincronizacao com a API publica da Caixa."""

from __future__ import annotations

import csv
from datetime import date, datetime
import json
from pathlib import Path
import time
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .games import GameSpec
from .models import Draw


CAIXA_API = "https://servicebus2.caixa.gov.br/portaldeloterias/api"
_CAIXA_SLUGS = {"mega-sena": "megasena", "lotofacil": "lotofacil"}


def _date(value: Any) -> date | None:
    if not value:
        return None
    text = str(value).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return date.fromisoformat(text) if fmt == "%Y-%m-%d" else datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _extract_numbers(value: Any) -> list[int]:
    if isinstance(value, str):
        return [int(part) for part in value.replace(";", ",").split(",") if part.strip()]
    if isinstance(value, (list, tuple)):
        return [int(part) for part in value]
    raise ValueError("campo de numeros precisa ser lista ou texto separado por virgulas")


def _record(item: dict[str, Any], spec: GameSpec) -> Draw:
    contest_value = item.get(
        "contest",
        item.get("numero", item.get("numeroConcurso", item.get("concurso"))),
    )
    number_value = item.get(
        "numbers",
        item.get("listaDezenas", item.get("dezenas")),
    )
    if contest_value is None or number_value is None:
        raise ValueError("registro precisa de concurso e numeros")
    draw_date = _date(item.get("draw_date", item.get("dataApuracao", item.get("data"))))
    return Draw.create(int(contest_value), _extract_numbers(number_value), draw_date, spec=spec)


def _records(payload: Any, spec: GameSpec) -> list[Draw]:
    if isinstance(payload, dict):
        for key in ("draws", "resultados", "concursos", "data"):
            if isinstance(payload.get(key), list):
                payload = payload[key]
                break
        else:
            payload = [payload]
    if not isinstance(payload, list):
        raise ValueError("JSON precisa ser um objeto de concurso ou uma lista")
    return [_record(item, spec) for item in payload]


def load_file(path: str | Path, spec: GameSpec) -> list[Draw]:
    """Carrega JSON ou CSV local para facilitar uso offline e testes."""

    file_path = Path(path)
    if file_path.suffix.lower() == ".csv":
        with file_path.open(newline="", encoding="utf-8-sig") as stream:
            reader = csv.DictReader(stream)
            return [_record(dict(row), spec) for row in reader]
    with file_path.open(encoding="utf-8") as stream:
        return _records(json.load(stream), spec)


def fetch_draw(spec: GameSpec, contest: int | None = None, *, base_url: str = CAIXA_API) -> Draw:
    endpoint = f"{base_url.rstrip('/')}/{_CAIXA_SLUGS[spec.key]}"
    if contest is not None:
        endpoint += f"/{contest}"
    request = Request(endpoint, headers={"User-Agent": "lottery-analyzer/0.1"})
    try:
        with urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(
            f"nao foi possivel consultar a Caixa ({endpoint}): {exc}. "
            "Use --file para importar um arquivo local ou libere o dominio da API."
        ) from exc
    records = _records(payload, spec)
    if len(records) != 1:
        raise ValueError(f"a API retornou {len(records)} concursos para {endpoint}")
    return records[0]


def sync_api(
    spec: GameSpec,
    *,
    start: int,
    end: int | None = None,
    base_url: str = CAIXA_API,
    pause_seconds: float = 0.15,
) -> Iterable[Draw]:
    """Gera concursos em ordem; a importacao pode ser retomada."""

    if start < 0 or (end is not None and end < 1):
        raise ValueError("start deve ser 0 ou positivo e end deve ser positivo")
    if start == 0:
        first = fetch_draw(spec, base_url=base_url)
        start = first.contest
        yield first
    else:
        yield fetch_draw(spec, start, base_url=base_url)
    stop = start if end is None else end
    if stop > start:
        raise ValueError("end deve ser menor ou igual ao concurso inicial")
    for contest in range(start - 1, stop - 1, -1):
        yield fetch_draw(spec, contest, base_url=base_url)
        if pause_seconds:
            time.sleep(pause_seconds)
