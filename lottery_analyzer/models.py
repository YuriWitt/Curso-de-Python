"""Modelos de dados e validacao de concursos."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable

from .games import GameSpec


@dataclass(frozen=True)
class Draw:
    """Um concurso normalizado, independentemente da fonte dos dados."""

    contest: int
    numbers: tuple[int, ...]
    draw_date: date | None = None

    @classmethod
    def create(
        cls,
        contest: int,
        numbers: Iterable[int],
        draw_date: date | None = None,
        *,
        spec: GameSpec,
    ) -> "Draw":
        normalized = tuple(sorted(int(number) for number in numbers))
        if contest < 1:
            raise ValueError("o numero do concurso deve ser positivo")
        if len(normalized) != spec.numbers_per_draw:
            raise ValueError(
                f"{spec.display_name} exige {spec.numbers_per_draw} numeros; "
                f"recebidos {len(normalized)}"
            )
        if len(set(normalized)) != len(normalized):
            raise ValueError("um concurso nao pode conter numeros repetidos")
        if not all(1 <= number <= spec.max_number for number in normalized):
            raise ValueError(
                f"os numeros de {spec.display_name} devem estar entre 1 e {spec.max_number}"
            )
        return cls(contest=int(contest), numbers=normalized, draw_date=draw_date)
