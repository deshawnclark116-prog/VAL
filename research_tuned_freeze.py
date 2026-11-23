"""Freeze the tuned Pick 4 weights: tune once on ALL real Pick 4 history to date.

The saved weights never change afterwards, so every later live pick is a fair
out-of-sample test tracked by the bot's luck check.
"""
from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from research_tuned_ultimate import SOURCES, features, tune
from val import Store, sync_game
from val_ultimate import SOURCE_ORDER, TUNED_WEIGHTS_FILE


def main():
    assert SOURCES == SOURCE_ORDER
    out = Path(TUNED_WEIGHTS_FILE)
    if out.exists():
        raise SystemExit(f"{out} already exists; frozen weights are never re-tuned")
    with tempfile.TemporaryDirectory(prefix="val-freeze-") as directory:
        store = Store(Path(directory) / "val.sqlite3")
        sync_game(store, "pick4")
        now = datetime.now(timezone.utc)
        history = [r for r in store.history("pick4") if datetime.fromisoformat(r["at"]) <= now]
    votes, tiebreak, target = features(history, 4)
    best, hits, tried = tune(votes, tiebreak, target, 4)
    data = dict(game="pick4", frozen_at=now.isoformat(), sources=SOURCE_ORDER,
                weights=[int(w) for w in best], tuned_on_draws=len(votes),
                tuned_from=history[0]["at"], tuned_to=history[-1]["at"], tuned_hits=hits,
                weightings_tried=tried)
    out.write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
