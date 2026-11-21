"""Regression: a missing official result must not mutate frozen prospective records."""
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import research_prospective_pooled_box_v2 as trial


class AtomicProspectiveSourceGuardTests(unittest.TestCase):
    def test_missing_result_does_not_change_existing_ledger_or_report(self):
        now = datetime(2026, 11, 21, 4, 6, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / "frozen.json"
            report = Path(directory) / "frozen.md"
            original = {
                "created_utc": "2026-11-20T12:00:00+00:00",
                "version": trial.VERSION,
                "signal_model": "pooled_5000_pr200_complete_box_v2",
                "games": {game: [] for game in trial.GAMES_TEST},
            }
            ledger.write_text(json.dumps(original, indent=2) + "\n")
            report.write_text("Previous immutable report\n")
            before_ledger = ledger.read_bytes()
            before_report = report.read_bytes()
            with patch.object(
                trial, "load_fresh_official_history",
                side_effect=ValueError(
                    "Latest completed official result is missing; withhold picks"
                ),
            ):
                with self.assertRaisesRegex(ValueError, "withhold picks"):
                    trial.cycle(now, ledger=ledger, report=report)
            self.assertEqual(ledger.read_bytes(), before_ledger)
            self.assertEqual(report.read_bytes(), before_report)


if __name__ == "__main__":
    unittest.main()
