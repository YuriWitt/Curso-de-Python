"""Definicoes das loterias suportadas."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GameSpec:
    """Regras necessarias para analisar uma modalidade."""

    key: str
    display_name: str
    max_number: int
    numbers_per_draw: int
    minimum_prize_matches: int


GAMES: dict[str, GameSpec] = {
    "mega-sena": GameSpec("mega-sena", "Mega-Sena", 60, 6, 4),
    "lotofacil": GameSpec("lotofacil", "Lotofacil", 25, 15, 11),
}

_ALIASES = {
    "mega": "mega-sena",
    "megasena": "mega-sena",
    "mega_sena": "mega-sena",
    "mega-sena": "mega-sena",
    "loto": "lotofacil",
    "lotofácil": "lotofacil",
    "lotofacil": "lotofacil",
}


def normalize_game(value: str) -> GameSpec:
    """Retorna a modalidade para um nome ou apelido aceito pela CLI."""

    key = value.strip().lower().replace(" ", "")
    try:
        return GAMES[_ALIASES[key]]
    except KeyError as exc:
        choices = ", ".join(sorted(GAMES))
        raise ValueError(f"modalidade desconhecida: {value!r}; use: {choices}") from exc
