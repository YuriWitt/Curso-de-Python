"""Persistencia SQLite sem dependencias externas."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

from .games import GameSpec
from .models import Draw


class DrawStore:
    """Armazena concursos e permite retomar importacoes interrompidas."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS draws (
                game TEXT NOT NULL,
                contest INTEGER NOT NULL,
                draw_date TEXT,
                numbers TEXT NOT NULL,
                PRIMARY KEY (game, contest)
            )
            """
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "DrawStore":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def upsert(self, spec: GameSpec, draw: Draw) -> None:
        self.connection.execute(
            """
            INSERT INTO draws(game, contest, draw_date, numbers)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(game, contest) DO UPDATE SET
                draw_date = excluded.draw_date,
                numbers = excluded.numbers
            """,
            (
                spec.key,
                draw.contest,
                draw.draw_date.isoformat() if draw.draw_date else None,
                json.dumps(draw.numbers),
            ),
        )

    def upsert_many(self, spec: GameSpec, draws: Iterable[Draw]) -> int:
        count = 0
        try:
            for draw in draws:
                self.upsert(spec, draw)
                count += 1
        finally:
            self.connection.commit()
        return count

    def list_draws(self, spec: GameSpec) -> list[Draw]:
        rows = self.connection.execute(
            "SELECT contest, draw_date, numbers FROM draws WHERE game = ? ORDER BY contest",
            (spec.key,),
        ).fetchall()
        from datetime import date

        result: list[Draw] = []
        for row in rows:
            parsed_date = date.fromisoformat(row["draw_date"]) if row["draw_date"] else None
            result.append(Draw(row["contest"], tuple(json.loads(row["numbers"])), parsed_date))
        return result
