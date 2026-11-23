"""Ferramentas para importar e analisar resultados de loterias."""

from .games import GAMES, GameSpec, normalize_game
from .models import Draw

__all__ = ["Draw", "GAMES", "GameSpec", "normalize_game"]
