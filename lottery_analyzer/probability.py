"""Probabilidades combinatorias de um bilhete."""

from __future__ import annotations

from math import comb


def exact_match_probability(
    population: int, ticket_size: int, matches: int
) -> tuple[int, float]:
    """Retorna (casos favoraveis, probabilidade) para exatamente ``matches``."""

    if not 0 <= matches <= ticket_size <= population:
        raise ValueError("parametros de combinacao invalidos")
    favorable = comb(ticket_size, matches) * comb(
        population - ticket_size, ticket_size - matches
    )
    total = comb(population, ticket_size)
    return favorable, favorable / total


def full_hit_probability(population: int, ticket_size: int) -> tuple[int, float]:
    """Retorna (total de combinacoes, probabilidade de acertar todas)."""

    total = comb(population, ticket_size)
    return total, 1 / total


def format_probability(probability: float) -> str:
    """Formata uma probabilidade sem esconder numeros muito pequenos."""

    return f"{probability * 100:.12g}%"
