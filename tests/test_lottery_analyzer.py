import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lottery_analyzer.analyzer import analyze
from lottery_analyzer.games import GAMES
from lottery_analyzer.models import Draw
from lottery_analyzer.probability import exact_match_probability, full_hit_probability
from lottery_analyzer.sources import load_file, sync_api
from lottery_analyzer.storage import DrawStore


class AnalyzerTests(unittest.TestCase):
    def setUp(self):
        self.spec = GAMES["mega-sena"]
        self.draws = [
            Draw.create(1, [1, 2, 3, 4, 5, 6], spec=self.spec),
            Draw.create(2, [1, 2, 3, 7, 8, 9], spec=self.spec),
            Draw.create(3, [1, 2, 3, 10, 11, 12], spec=self.spec),
        ]

    def test_validation_and_analysis(self):
        result = analyze(self.spec, self.draws, seed=42)
        self.assertEqual(result.draw_count, 3)
        self.assertEqual(len(result.suggested_numbers), 6)
        self.assertEqual(len(set(result.suggested_numbers)), 6)
        self.assertEqual(result.full_hit_cases, 50063860)
        self.assertAlmostEqual(result.full_hit_probability, 1 / 50063860)

    def test_probabilities_are_combinatorial(self):
        cases, probability = full_hit_probability(25, 15)
        self.assertEqual(cases, 3268760)
        self.assertAlmostEqual(probability, 1 / 3268760)
        favorable, probability = exact_match_probability(60, 6, 5)
        self.assertEqual(favorable, 324)
        self.assertAlmostEqual(probability, 324 / 50063860)

    def test_store_and_json_import(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "draws.json"
            path.write_text(json.dumps([{"numero": 1, "listaDezenas": ["01", "02", "03", "04", "05", "06"]}]))
            draws = load_file(path, self.spec)
            with DrawStore(Path(directory) / "db.sqlite") as store:
                self.assertEqual(store.upsert_many(self.spec, draws), 1)
                self.assertEqual(store.list_draws(self.spec), draws)

    def test_cli_import_and_json_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(__file__).resolve().parents[1]
            input_path = Path(directory) / "draws.json"
            db_path = Path(directory) / "db.sqlite"
            input_path.write_text(json.dumps([{"numero": 1, "dataApuracao": "30/10/2025", "listaDezenas": ["01", "02", "03", "04", "05", "06"]}]))
            imported = subprocess.run([sys.executable, "-m", "lottery_analyzer", "--db", str(db_path), "import", "--game", "mega-sena", "--file", str(input_path)], cwd=root, check=False, capture_output=True, text=True)
            self.assertEqual(imported.returncode, 0, imported.stderr)
            report = subprocess.run([sys.executable, "-m", "lottery_analyzer", "--db", str(db_path), "analyze", "--game", "mega-sena", "--json"], cwd=root, check=False, capture_output=True, text=True)
            self.assertEqual(report.returncode, 0, report.stderr)
            payload = json.loads(report.stdout)
            self.assertEqual(payload[0]["draw_count"], 1)
            self.assertEqual(payload[0]["latest_contest"], 1)

    def test_sync_fetches_only_latest_without_end_and_history_with_end(self):
        def fake_fetch(spec, contest=None, **_):
            return Draw.create(contest or 3, range(1, 7), spec=spec)

        with patch("lottery_analyzer.sources.fetch_draw", side_effect=fake_fetch):
            latest = list(sync_api(self.spec, start=0))
            history = list(sync_api(self.spec, start=0, end=1))
        self.assertEqual([draw.contest for draw in latest], [3])
        self.assertEqual([draw.contest for draw in history], [3, 2, 1])


if __name__ == "__main__":
    unittest.main()
