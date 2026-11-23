"""Preview the next drawing's picks from the new generators, using real results.

Prints picks only; nothing is saved to the ledger (the live bot does that once
these generators are merged).
"""
from __future__ import annotations

import tempfile
from datetime import datetime, timezone
from pathlib import Path

from val import ET, GAMES, Store, next_draw, sync_game
from val_player_methods import METHODS, player_pick
from val_ultimate import load_tuned_weights, ultimate_pick, weighted_digit_pick


def show(nums):
    return " ".join(map(str, nums["numbers"])) + (f" + {nums['bonus']}" if nums.get("bonus") else "")


def main():
    now = datetime.now(timezone.utc)
    lines = ["# Picks preview — new generators", "", f"Made: {now.astimezone(ET):%a %b %d, %I:%M %p} ET, from real official results.", "",
             "| Game | Drawing (ET) | Ultimate pick | Tuned Pick 4 | Latest result used |", "| --- | --- | --- | --- | --- |"]
    methods = ["", "## Each method's pick", "", "| Game | " + " | ".join(METHODS.values()) + " |",
               "| --- |" + " --- |" * len(METHODS)]
    tuned = load_tuned_weights()
    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "val.sqlite3")
        for game, g in GAMES.items():
            if "id" not in g:
                continue
            sync_game(store, game)
            history = [r for r in store.history(game) if datetime.fromisoformat(r["at"]) <= now]
            target = next_draw(game, now)
            when = datetime.fromisoformat(target["at"]).astimezone(ET).strftime("%a %b %d, %I:%M %p")
            pick, _ = ultimate_pick(game, history)
            t = show(weighted_digit_pick(history, 4, tuned["weights"])) if game == "pick4" and tuned else "—"
            last = history[-1]
            lines.append(f"| {g['name']} | {when} {target['stream']} | **{show(pick)}** | **{t}** | {show(last)} ({last['stream']}) |")
            if g.get("digits"):
                methods.append(f"| {g['name']} | " + " | ".join(show(player_pick(m, history, g['size'])) for m in METHODS) + " |")
    text = "\n".join(lines + methods) + "\n\nPreview only: not saved to the ledger.\n"
    Path("reports").mkdir(exist_ok=True)
    Path("reports/preview_picks.md").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
