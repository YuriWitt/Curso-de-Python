"""Interface de linha de comando do analisador."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .analyzer import analyze
from .games import GAMES, normalize_game
from .probability import format_probability
from .sources import load_file, sync_api
from .storage import DrawStore


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lottery-analyzer",
        description="Importa e analisa resultados da Mega-Sena e da Lotofacil.",
    )
    parser.add_argument("--db", default="data/lottery.db", help="arquivo SQLite (padrao: data/lottery.db)")
    sub = parser.add_subparsers(dest="command", required=True)

    import_parser = sub.add_parser("import", help="importa JSON ou CSV local")
    import_parser.add_argument("--game", required=True, choices=sorted(GAMES))
    import_parser.add_argument("--file", required=True, type=Path)

    sync_parser = sub.add_parser("sync", help="consulta a API da Caixa")
    sync_parser.add_argument("--game", required=True, choices=sorted(GAMES))
    sync_parser.add_argument("--start", type=int, default=0, help="concurso inicial; 0 usa o ultimo")
    sync_parser.add_argument("--end", type=int, help="concurso final para sincronizacao retroativa")
    sync_parser.add_argument("--api-url", default=None, help="URL base alternativa da API")

    analyze_parser = sub.add_parser("analyze", help="calcula estatisticas e sugestao")
    analyze_parser.add_argument("--game", required=True, choices=[*sorted(GAMES), "todos"])
    analyze_parser.add_argument("--seed", type=int, default=42, help="semente para desempates reproduciveis")
    analyze_parser.add_argument("--json", action="store_true", dest="as_json")
    return parser


def _print_analysis(result: object) -> None:
    data = result.as_dict()  # type: ignore[union-attr]
    probability = data["probability"]  # type: ignore[index]
    print(f"{data['game']}: {data['draw_count']} concursos analisados (ultimo {data['latest_contest']})")
    frequencies = data["frequencies"]  # type: ignore[index]
    overdue = data["overdue_draws"]  # type: ignore[index]
    frequent = sorted(frequencies.items(), key=lambda item: (-item[1], item[0]))[:10]
    delayed = sorted(overdue.items(), key=lambda item: (-item[1], item[0]))[:10]
    print("Mais frequentes:", ", ".join(f"{number:02d} ({count})" for number, count in frequent))
    print("Mais atrasadas:", ", ".join(f"{number:02d} ({gap} concursos)" for number, gap in delayed))
    print("Sugestao heuristica:", " ".join(f"{number:02d}" for number in data["suggested_numbers"]))  # type: ignore[index]
    print(
        "Acerto de todos os numeros:",
        f"1 em {probability['one_in']}",  # type: ignore[index]
        f"({format_probability(probability['exact_full_hit'])})",  # type: ignore[index]
    )
    print("Probabilidades exatas por quantidade de acertos:")
    for matches, value in probability["matches"].items():  # type: ignore[index]
        print(f"  {matches} acertos: {format_probability(value)}")
    print("Aviso:", data["warning"])


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "import":
            spec = normalize_game(args.game)
            draws = load_file(args.file, spec)
            with DrawStore(args.db) as store:
                count = store.upsert_many(spec, draws)
            print(f"{count} concursos importados para {spec.display_name}.")
            return 0
        if args.command == "sync":
            spec = normalize_game(args.game)
            kwargs = {} if args.api_url is None else {"base_url": args.api_url}
            with DrawStore(args.db) as store:
                count = store.upsert_many(spec, sync_api(spec, start=args.start, end=args.end, **kwargs))
            print(f"{count} concursos sincronizados para {spec.display_name}.")
            return 0
        selected = list(GAMES.values()) if args.game == "todos" else [normalize_game(args.game)]
        with DrawStore(args.db) as store:
            analyses = [analyze(spec, store.list_draws(spec), seed=args.seed) for spec in selected]
        if args.as_json:
            print(json.dumps([item.as_dict() for item in analyses], ensure_ascii=False, indent=2))
        else:
            for index, item in enumerate(analyses):
                if index:
                    print()
                _print_analysis(item)
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
