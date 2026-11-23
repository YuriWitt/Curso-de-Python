"""Estatisticas descritivas e sugestao heuristica de combinacao."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import random
from typing import Iterable

from .games import GameSpec
from .models import Draw
from .probability import exact_match_probability, full_hit_probability


@dataclass(frozen=True)
class Analysis:
    game: str
    draw_count: int
    latest_contest: int
    frequencies: dict[int, int]
    overdue: dict[int, int]
    suggested_numbers: tuple[int, ...]
    full_hit_cases: int
    full_hit_probability: float
    prize_probabilities: dict[int, float]

    def as_dict(self) -> dict[str, object]:
        return {
            "game": self.game,
            "draw_count": self.draw_count,
            "latest_contest": self.latest_contest,
            "frequencies": self.frequencies,
            "overdue_draws": self.overdue,
            "suggested_numbers": list(self.suggested_numbers),
            "probability": {
                "exact_full_hit": self.full_hit_probability,
                "exact_full_hit_percent": self.full_hit_probability * 100,
                "one_in": self.full_hit_cases,
                "matches": self.prize_probabilities,
            },
            "warning": (
                "A sugestao e uma heuristica baseada no historico. Em um sorteio "
                "justo, cada combinacao continua tendo a mesma probabilidade."
            ),
        }


def _scores(spec: GameSpec, draws: list[Draw]):
    frequencies = Counter(number for draw in draws for number in draw.numbers)
    latest = draws[-1].contest
    last_seen = {number: None for number in range(1, spec.max_number + 1)}
    for draw in draws:
        for number in draw.numbers:
            last_seen[number] = draw.contest
    overdue = {
        number: latest - contest if contest is not None else len(draws)
        for number, contest in last_seen.items()
    }
    max_frequency = max(frequencies.values(), default=1)
    max_overdue = max(overdue.values(), default=1)
    scores = {
        number: 0.65 * frequencies.get(number, 0) / max_frequency
        + 0.35 * overdue[number] / max_overdue
        for number in range(1, spec.max_number + 1)
    }
    frequency_map = {
        number: frequencies.get(number, 0) for number in range(1, spec.max_number + 1)
    }
    return frequency_map, overdue, scores


def analyze(spec: GameSpec, draws: Iterable[Draw], seed: int | None = None) -> Analysis:
    """Analisa os concursos e cria uma sugestao deterministica quando ha seed."""

    ordered = sorted(draws, key=lambda draw: draw.contest)
    if not ordered:
        raise ValueError(f"nao ha resultados importados para {spec.display_name}")
    frequencies, overdue, scores = _scores(spec, ordered)
    rng = random.Random(seed)
    ranked = sorted(
        range(1, spec.max_number + 1),
        key=lambda number: (scores[number] + rng.random() * 1e-9, -number),
        reverse=True,
    )
    suggestion = tuple(sorted(ranked[: spec.numbers_per_draw]))
    cases, probability = full_hit_probability(spec.max_number, spec.numbers_per_draw)
    prize_probabilities = {
        matches: exact_match_probability(spec.max_number, spec.numbers_per_draw, matches)[1]
        for matches in range(spec.minimum_prize_matches, spec.numbers_per_draw + 1)
    }
    return Analysis(
        game=spec.key,
        draw_count=len(ordered),
        latest_contest=ordered[-1].contest,
        frequencies=frequencies,
        overdue=dict(sorted(overdue.items())),
        suggested_numbers=suggestion,
        full_hit_cases=cases,
        full_hit_probability=probability,
        prize_probabilities=prize_probabilities,
    )
