# VAL — Virginia Lottery Lab

A local research bot for Virginia drawing games. It downloads official draw history, generates small batches of picks, runs chronological backtests and Monte Carlo frequency checks, and records prospective picks alongside equal-sized uniform random controls.

**No method here has an established predictive edge.** More calculations do not make a fair independent draw predictable. Backtest hits and partial matches are not evidence of profit. Start with paper picks.

## Run

Requires **Python 3.11+** with IANA timezone data (normally included on Linux/macOS). No Python packages, API keys, or paid services are required. Windows systems missing timezone data can install `tzdata` using `python -m pip install tzdata`.

```sh
git clone https://github.com/deshawnclark116-prog/VAL.git
cd VAL
python3 val.py sync --game all
python3 val.py serve
```

Open **http://localhost:8765**. The dashboard includes game/session selection, official history updates, frequency counts, combination generation, rolling tests, simulation, CSV imports, and the prediction ledger.

For optional periodic updates while the bot is running:

```sh
python3 val.py serve --interval 360
```

This refreshes the nine supported official downloads at startup and every six hours. Closing the process stops updates. It is a local app, not an unattended hosted service. The server binds to loopback only; no gambling accounts are connected and no tickets are purchased.

## Coverage

| Game | Current base selection | Data |
| --- | --- | --- |
| Pick 3 | 3 ordered digits, 0–9; repeats allowed | Official download, Day/Night filters |
| Pick 4 | 4 ordered digits, 0–9; repeats allowed | Official download, Day/Night filters |
| Pick 5 | 5 ordered digits, 0–9; repeats allowed | Official download, Day/Night filters |
| Cash 5 | 5 distinct numbers, 1–45 | Official download |
| Powerball | 5 distinct numbers, 1–69 + 1–26 | Official download |
| Mega Millions | 5 distinct numbers, 1–70 + 1–24 | Official download |
| Millionaire for Life | 5 distinct numbers, 1–58 + 1–5 | Official download |
| Bank a Million | 6 distinct numbers, 1–40 | Official download; drawn bonus retained as metadata |
| Cash Pop | 1 number, 1–15 | Official download; five session filters |
| Keno | Bot produces five-spot tickets from 1–80; 20 numbers drawn | CSV import; no automatic bulk feed in this version |
| New Year's Millionaire Raffle | Assigned ticket numbers | Official reference only; no generated selections |

FIREBALL, EZ Match, multipliers, alternative Keno spot sizes, box wagers, prize-tier evaluation, and return-on-investment calculations are not implemented. Leading zeros and repeated Pick digits are preserved. Bank a Million's drawn bonus is not a separate player selection. Cash4Life is retired and is not mixed with Millionaire for Life.

All automatic history is restricted to **April 8, 2025 onward**, a conservative common current-format cutoff, rather than combining incompatible historical matrices. Newer games naturally have shorter histories. The application displays data timestamps and update failures; a failed request retains previously imported data. Source downloads are external services and may change format or become unavailable. Scheduled times are used to timestamp date-only records; these are not verified actual drawing-event timestamps.

## The methods

Methods sample combinations with these **experimental selection weights**, not estimated winning probabilities:

- **Uniform random:** equal per-number weights; distinct main balls are sampled without replacement. Digit positions sample independently with replacement.
- **Frequency:** `count + 2` smoothing over the previous 500 draws.
- **Recent:** `count + 2` smoothing over the previous 50 draws.
- **Cold:** `1 / sqrt(count + 2)` over the previous 500 draws. An underrepresented number is not "due."
- **Ensemble:** fixed `0.4 × normalized frequency + 0.4 × normalized recent + 0.2 × normalized cold`.

Pick games model each digit position separately; separately selected special balls use their own pool and history. Each batch contains unique combinations. Cash Pop has only 15 single-number combinations, so batches cap at 15. Methods use the selected draw session; history methods need at least 30 draws. No automatic method tuning or retrospective winner selection takes place.

### Rolling evaluation

Backtests use up to the last 500 test draws, at least 30 earlier training draws, and a 500-draw rolling training window. At least 80 total draws are required. Each tested draw is withheld when its picks are produced. Five methods run with the same requested ticket count and a fixed seed for repeatable comparisons. A random baseline, exact-hit counts, special-ball matches, average main matches per ticket, and approximate 95% intervals are shown.

The expected main matches for an ordered `k`-digit ticket are `k/10`. For a ticket selecting `k` distinct numbers from `N` with `d` winning main numbers, the expectation is `k*d/N`. These are match expectations, **not prize probabilities**. Exact hits require every selected main number and the selected special ball when applicable; for Keno they mean all five selected spots are among the 20 drawn. Intervals use per-draw average matches and a normal approximation; they are descriptive, do not adjust for multiple comparisons, and do not establish an edge. Special-ball results are reported separately from main-match averages. No payout inference is made.

### Monte Carlo

The randomness check compares aggregate frequency dispersion `sum((observed - expected)^2 / expected)` over the last 200 selected draws with 1,000–100,000 simulated fair histories. It simulates the game's replacement rules, including 20-of-80 Keno. The tail estimate uses `(exceedances + 1)/(trials + 1)`. This test does not test special balls, all possible dependencies, or next-draw prediction. Repeatedly trying tests or game/session choices can yield apparently unusual results by chance.

### Prospective ledger

Each generated batch saves its creation time, method, session, selections, and the same number of uniform random controls in local SQLite. It settles against the first loaded draw in that session **on a later Eastern calendar date**. Same-day draws are deliberately excluded because source histories often have dates rather than actual event timestamps. Refresh history after the target drawing to settle it. Batches retain both wins and losses; generating more batches does not erase earlier ones. The ledger shows all sessions for the selected game. Multiple batches targeting the same draw are correlated and are not independent trials.

The database is local and user-editable; this is a research log, not a tamper-proof audit service. Imported records carry a user-import source label. Preserve your database to preserve your ledger.

## CSV format

```csv
game,at,stream,numbers,bonus
pick3,2026-11-10T13:59:00-05:00,Day,"0 7 7",
powerball,2026-11-09T22:59:00-05:00,Main,"13 34 41 45 48",25
```

Use the internal game IDs in the table's corresponding source (`pick3`, `pick4`, `pick5`, `cash5`, `powerball`, `megamillions`, `millionaireforlife`, `bankamillion`, `cashpop`, `keno`). Timestamps need an explicit timezone. Future timestamps and records before the current-format cutoff are rejected. Keno needs all 20 distinct winning numbers. Digit games need `Day` or `Night` as the session. Missing or duplicate main numbers, invalid ranges, and missing special balls are rejected. An invalid row prevents the whole import. Existing `(game, timestamp, session)` records are not overwritten. Import trustworthy records with timestamps matching the official draw schedule to avoid duplicate identifiers.

## CLI analysis

```sh
python3 val.py backtest --game pick3 --stream Night
python3 val.py simulate --game cash5 --trials 10000
python3 -m unittest discover -s tests -v
```

`--db PATH` selects a separate database; `serve --port 8766` changes the port. Local data is ignored by Git. Copy `data/val.sqlite3` with the server stopped to back it up.

## Sources

- [Virginia's current drawing games](https://www.valottery.com/alldrawgames)
- Official plain-text history endpoint linked from each game page: `https://www.valottery.com/api/v1/downloadall?gameId=1050` (example: Pick 3). Game IDs are discovered from official download links, not an unofficial results service.
- [Millionaire for Life rules and number fields](https://www.valottery.com/data/draw-games/millionaireforlife)
- [Mega Millions current format](https://www.valottery.com/data/draw-games/megamillions)
- [Keno format](https://www.valottery.com/data/draw-games/keno)
- [Seasonal raffle](https://www.valottery.com/data/draw-games/raffle)

Rules and feeds checked November 12, 2026. Independent tool; not affiliated with Virginia Lottery. The UI optionally loads Google Fonts and falls back to system fonts offline. All analysis and stored records remain local.
