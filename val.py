"""VAL: Virginia draw analysis. Python 3.11+, standard library only."""
from __future__ import annotations
import argparse
import csv
import io
import json
import math
import random
import re
import sqlite3
import statistics
import threading
import urllib.request
import warnings
from collections import Counter
from datetime import datetime, timezone, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
ET = ZoneInfo("America/New_York")
METHODS = ("random", "frequency", "recent", "cold", "ensemble")
# A conservative common cutoff avoids mixing obsolete matrices into current games.
CUTOFF = "2025-04-08"
# The 2025-04-08 rule-change floor applies to newer game matrices (e.g.
# Mega Millions); it must not silently erase decades of stable digit results.
# Pick 3/4/5 predate 2025 and the official bulk downloads include them.
DIGIT_HISTORY_START = {
    "pick3": "1989-05-22",
    "pick4": "1991-09-30",
    "pick5": "2023-06-05",
}

def history_cutoff(game):
    return DIGIT_HISTORY_START.get(game, CUTOFF)
GAMES = {
    "pick3": dict(name="Pick 3", size=3, pool=10, digits=True, id=1050),
    "pick4": dict(name="Pick 4", size=4, pool=10, digits=True, id=1040),
    "pick5": dict(name="Pick 5", size=5, pool=10, digits=True, id=1035),
    "cash5": dict(name="Cash 5", size=5, pool=45, id=1030),
    "powerball": dict(name="Powerball", size=5, pool=69, bonus=26, id=20),
    "megamillions": dict(name="Mega Millions", size=5, pool=70, bonus=24, id=15),
    "millionaireforlife": dict(name="Millionaire for Life", size=5, pool=58, bonus=5, id=1075),
    "bankamillion": dict(name="Bank a Million", size=6, pool=40, id=1070),
    "cashpop": dict(name="Cash Pop", size=1, pool=15, id=40),
    "keno": dict(name="Keno", size=5, pool=80, drawn=20),
}

def draw_schedule(game, now, stream="All"):
    """Scheduled Eastern draw times around now, with DST and weekday rules."""
    if game == "keno": raise ValueError("Keno automatic targeting is not available")
    times = [("Main",23,0)]
    weekdays = set(range(7))
    if GAMES[game].get("digits"): times=[("Day",13,59),("Night",23,0)]
    elif game == "cashpop": times=[("Coffee Break",9,0),("Lunch Break",12,0),("Rush Hour",17,0),("Prime Time",21,0),("After Hours",23,59)]
    elif game == "powerball": weekdays={0,2,5};times=[("Main",22,59)]
    elif game == "megamillions": weekdays={1,4}
    elif game == "bankamillion": weekdays={2,5}
    elif game == "millionaireforlife": times=[("Main",23,15)]
    day=now.astimezone(ET).date()
    draws=[]
    for offset in range(-8,9):
        date=day+timedelta(days=offset)
        if date.weekday() not in weekdays: continue
        for session,hour,minute in times:
            if stream != "All" and session != stream: continue
            draws.append(dict(at=datetime(date.year,date.month,date.day,hour,minute,tzinfo=ET).astimezone(timezone.utc).isoformat(),stream=session))
    return sorted(draws,key=lambda x:x["at"])

def next_draw(game,now,stream="All"):
    return next(d for d in draw_schedule(game,now,stream) if datetime.fromisoformat(d["at"])>now)

def parse_latest_digits(game,text):
    """Supplement same-day digit results omitted by the full-day download."""
    from html import unescape
    g=GAMES[game]
    card=re.search(r'<a\b[^>]*\bid="game-'+str(g["id"])+r'"[^>]*>(.*?)</a>',text,re.S)
    if not card: raise ValueError("Latest-result game card was not found")
    date=re.search(r'Latest Drawing:\s*\w+\s+(\d+/\d+/\d+)',card[1])
    if not date: raise ValueError("Latest-result date was not found")
    day=datetime.strptime(date[1],"%m/%d/%Y")
    rows=[]
    for css,stream,hour,minute in [("daytime","Day",13,59),("evening","Night",23,0)]:
        ul=re.search(r'<ul\b[^>]*class="'+css+r'"[^>]*>(.*?)</ul>',card[1],re.S)
        if not ul: continue
        digits=[]
        for li in re.findall(r'<li\b[^>]*>(.*?)</li>',ul[1],re.S):
            value=unescape(re.sub(r'<[^>]+>', '', li)).strip()
            if re.fullmatch(r'\d',value): digits.append(int(value))
        if not digits: continue  # A future session contains dashes, never zeroes.
        if len(digits) != g["size"]+1: raise ValueError("Unexpected latest digit-result format")
        validate(game,digits[:-1])
        rows.append(dict(game=game,at=day.replace(hour=hour,minute=minute,tzinfo=ET).astimezone(timezone.utc).isoformat(),
                         stream=stream,numbers=digits[:-1],bonus=None,extra=digits[-1],source="Virginia Lottery latest-result page"))
    if not rows: raise ValueError("No completed digit results on latest-result page")
    return rows

def validate(game, numbers, bonus=None, draw=True):
    g = GAMES[game]
    n = g.get("drawn", g["size"]) if draw else g["size"]
    low = 0 if g.get("digits") else 1
    if len(numbers) != n or any(type(x) is not int or not low <= x < low + g["pool"] for x in numbers):
        raise ValueError(f"{g['name']}: expected {n} integers from {low} to {low + g['pool'] - 1}")
    if not g.get("digits") and len(set(numbers)) != n:
        raise ValueError("Repeated numbers are invalid for this game")
    if g.get("bonus") and (type(bonus) is not int or not 1 <= bonus <= g["bonus"]):
        raise ValueError("Missing or invalid special ball")
    if not g.get("bonus") and bonus is not None:
        raise ValueError("This game has no player-selected special ball")

def quarantine_conflicted_draws(rows):
    """Exclude *all* incompatible draw records sharing one official timestamp.

    The Lottery bulk files sometimes repeat a date/session with DIFFERENT
    numbers (for example Pick 3 Night 2008-10-30). We cannot determine from
    those records which is authoritative or whether it was a redraw.
    Never silently choose one or feed conflicting rows to models.
    """
    by_key = {}
    conflicting = set()
    identical_duplicates = 0
    for row in rows:
        key = (row["game"], row["at"], row["stream"])
        prior = by_key.get(key)
        if prior is None:
            by_key[key] = row
        elif (prior["numbers"], prior.get("bonus"), prior.get("extra")) != (
              row["numbers"],row.get("bonus"),row.get("extra")):
            conflicting.add(key)
        else:
            identical_duplicates += 1
    if conflicting:
        first = sorted(conflicting)[0]
        warnings.warn("Official archive contains "+str(len(conflicting))+
             " ambiguous draw time(s) (first: "+repr(first)+
             "); quarantining ALL matching records, not guessing an outcome",
             RuntimeWarning, stacklevel=2)
    if identical_duplicates:
        warnings.warn("Removed "+str(identical_duplicates)+
            " identical repeated official draw rows",RuntimeWarning,stacklevel=2)
    return [row for key,row in sorted(by_key.items(),key=lambda x:x[0][1:])
            if key not in conflicting]


def parse_official(game, text):
    """Parse the Lottery's plain-text download; fail closed on unexpected lines."""
    rows = []
    g = GAMES[game]
    for line in text.splitlines():
        line = line.strip()
        if (not line or line.startswith("Results for") or line in (
            "All information is entered manually, and is subject to human error.",
            "Therefore, we can not guarantee the accuracy of this information.")):
            continue
        parts = [p.strip() for p in line.split(";")]
        if game == "cashpop":
            dt = datetime.strptime(parts[0], "%a %m/%d/%Y - %I:%M %p").replace(tzinfo=ET)
            draws = [(parts[2], [int(parts[1])], None, None, dt)]
        else:
            day = datetime.strptime(parts[0], "%m/%d/%Y")
            if day.strftime("%Y-%m-%d") < history_cutoff(game):
                continue
            if g.get("digits"):
                draws = []
                for i, part in enumerate(parts[1:], 1):
                    match = re.fullmatch(r"(Day|Night):\s*([\d,]+)", part)
                    if match:
                        stream = match[1]
                        dt = day.replace(hour=13 if stream == "Day" else 23, minute=59 if stream == "Day" else 0, tzinfo=ET)
                        fire = int(parts[i+1].split(":")[1]) if i+1 < len(parts) and parts[i+1].startswith("Fireball:") else None
                        draws.append((stream, [int(v) for v in match[2].split(",")], None, fire, dt))
                if not draws:
                    raise ValueError("Unrecognized digit draw: " + line[:100])
            else:
                numbers = [int(v) for v in parts[1].split(",")]
                extra = int(parts[2].split(":")[1]) if len(parts) > 2 else None
                hour, minute = (23, 15) if game == "millionaireforlife" else (23, 0)
                if game == "powerball": hour, minute = 22, 59
                dt = day.replace(hour=hour, minute=minute, tzinfo=ET)
                draws = [("Main", numbers, extra if g.get("bonus") else None, extra if game == "bankamillion" else None, dt)]
        for stream, numbers, bonus, extra, dt in draws:
            if dt.date().isoformat() < history_cutoff(game): continue
            validate(game, numbers, bonus)
            rows.append(dict(game=game, at=dt.astimezone(timezone.utc).isoformat(), stream=stream,
                             numbers=numbers, bonus=bonus, extra=extra, source="Virginia Lottery official download"))
    if not rows:
        raise ValueError("No current-format draw records found")
    return quarantine_conflicted_draws(rows)

class Store:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
              CREATE TABLE IF NOT EXISTS draws(game TEXT, at TEXT, stream TEXT, data TEXT,
                PRIMARY KEY(game, at, stream));
              CREATE TABLE IF NOT EXISTS predictions(id INTEGER PRIMARY KEY, game TEXT, created TEXT,
                stream TEXT, method TEXT, data TEXT, result TEXT);
              CREATE TABLE IF NOT EXISTS sync(game TEXT PRIMARY KEY, at TEXT, error TEXT);
            ''')
    def connect(self): return sqlite3.connect(self.path, timeout=30)
    def put(self, rows):
        with self.connect() as db:
            before = db.total_changes
            for r in rows:
                validate(r["game"], r["numbers"], r.get("bonus"))
                cur = db.execute("INSERT OR IGNORE INTO draws VALUES(?,?,?,?)",
                                 (r["game"],r["at"],r["stream"],json.dumps(r)))
                if cur.rowcount == 0:
                    old = db.execute("SELECT data FROM draws WHERE game=? AND at=? AND stream=?",
                                     (r["game"],r["at"],r["stream"])).fetchone()
                    original=json.loads(old[0])
                    if (original["numbers"]!=r["numbers"] or
                        original.get("bonus")!=r.get("bonus")):
                        raise ValueError("Conflicting previously stored official draw: "+
                                         r["game"]+" "+r["at"]+" "+r["stream"])
            return db.total_changes - before
    def history(self, game, stream="All"):
        with self.connect() as db:
            rows = db.execute("SELECT data FROM draws WHERE game=? ORDER BY at,stream", (game,)).fetchall()
        return [r for x in rows if (r := json.loads(x[0])) and (stream == "All" or r["stream"] == stream)]
    def record(self, game, stream, method, picks, baseline, target=None, training_latest=None, created=None, model_meta=None):
        data = dict(picks=picks, baseline=baseline)
        if model_meta is not None: data["model_meta"] = model_meta
        created=created or datetime.now(timezone.utc)
        if target:
            if datetime.fromisoformat(target["at"])<=created: raise ValueError("Target draw has already occurred")
            data.update(target=target,training_latest=training_latest)
        with self.connect() as db:
            cur = db.execute("INSERT INTO predictions(game,created,stream,method,data) VALUES(?,?,?,?,?)",
                (game, created.isoformat(), stream, method, json.dumps(data)))
            return cur.lastrowid
    def ledger(self, game):
        history = self.history(game)
        with self.connect() as db:
            records = db.execute("SELECT id,created,stream,method,data,result FROM predictions WHERE game=? ORDER BY id DESC", (game,)).fetchall()
            out = []
            for pid, created, stream, method, data, result in records:
                data = json.loads(data)
                if result is None:
                    created_day = datetime.fromisoformat(created).astimezone(ET).date()
                    if data.get("target"):
                        future=next((d for d in history if d["at"]==data["target"]["at"] and d["stream"]==data["target"]["stream"]),None)
                    else:
                        # Preserve the original contract for batches created before explicit targets.
                        future = next((d for d in history if datetime.fromisoformat(d["at"]).astimezone(ET).date() > created_day
                                       and (stream == "All" or d["stream"] == stream)), None)
                    if future:
                        result = json.dumps(dict(draw=future, model=score_batch(game,data["picks"],future), random=score_batch(game,data["baseline"],future)))
                        db.execute("UPDATE predictions SET result=? WHERE id=?", (result,pid))
                out.append(dict(id=pid,created=created,stream=stream,method=method,**data,result=json.loads(result) if result else None))
            return out

def model_selection_weights(game, history, method="ensemble", position=None, bonus=False):
    """Experimental selection weights, NOT calibrated winning probabilities."""
    if method not in METHODS: raise ValueError("Unknown method")
    g = GAMES[game]
    low = 0 if g.get("digits") else 1
    values = list(range(low, low + g["pool"]))
    pool = list(range(1, g["bonus"] + 1)) if bonus else values
    if method == "random": return [1] * len(pool)
    history = history[-500:]
    total = Counter(); recent = Counter()
    for i, row in enumerate(history):
        ns = [row["bonus"]] if bonus else ([row["numbers"][position]] if position is not None else row["numbers"])
        total.update(ns)
        if i >= len(history) - 50: recent.update(ns)
    hot = [total[v] + 2 for v in pool]
    rec = [recent[v] + 2 for v in pool]
    cold = [1 / math.sqrt(x) for x in hot]
    if method == "frequency": return hot
    if method == "recent": return rec
    if method == "cold": return cold
    return [0.4*h/sum(hot) + 0.4*r/sum(rec) + 0.2*c/sum(cold) for h,r,c in zip(hot,rec,cold)]


def rank_ensemble_picks(game, history, picks):
    """Rank existing ensemble-sampled picks by model weight, not winning odds."""
    from itertools import permutations
    if len(history) < 30: raise ValueError("At least 30 historical draws are required")
    g = GAMES[game]; low = 0 if g.get("digits") else 1
    main = ([model_selection_weights(game, history, position=i) for i in range(g["size"])]
            if g.get("digits") else model_selection_weights(game, history))
    bonus_weights = model_selection_weights(game, history, bonus=True) if g.get("bonus") else None
    def weight_score(pick):
        if g.get("digits"):
            result = math.prod(main[i][n] for i, n in enumerate(pick["numbers"]))
        else:
            # Generated ball combinations are sorted; sum probabilities of all
            # their underlying weighted-without-replacement draw orders.
            result = 0.0
            for sequence in permutations(pick["numbers"]):
                remaining, probability = 1.0, 1.0
                for number in sequence:
                    weight = main[number - low]
                    probability *= weight / remaining
                    remaining -= weight
                result += probability
        if bonus_weights is not None: result *= bonus_weights[pick["bonus"] - 1]
        return result
    scored = [(weight_score(p), i, p) for i, p in enumerate(picks)]
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [dict(pick, rank=rank, role=("primary" if rank == 1 else f"alternative_{rank-1}"),
                 model_weight_score=score, ranking_version="ensemble_sampling_v1")
            for rank, (score, _, pick) in enumerate(scored, 1)]

def sample_weights(values, weights, size, rng, replace=False):
    values, weights = list(values), list(weights)
    out = []
    for _ in range(size):
        i = rng.choices(range(len(values)), weights=weights, k=1)[0]
        out.append(values[i])
        if not replace: values.pop(i); weights.pop(i)
    return out

def generate(game, history, method="ensemble", count=5, rng=None):
    if method not in METHODS: raise ValueError("Unknown method")
    if not 1 <= count <= 20: raise ValueError("Choose 1–20 combinations")
    if method != "random" and len(history) < 30: raise ValueError("Load at least 30 draws for history-based methods")
    g = GAMES[game]
    rng = rng or random.SystemRandom()
    low = 0 if g.get("digits") else 1
    values = list(range(low, low+g["pool"]))
    history = history[-500:]
    main_weights = ([model_selection_weights(game, history, method, position=i) for i in range(g["size"])]
                    if g.get("digits") else model_selection_weights(game, history, method))
    bonus_weights = model_selection_weights(game, history, method, bonus=True) if g.get("bonus") else None
    picks, seen = [], set()
    # Cash Pop has only 15 possible single-number combinations.
    limit = min(count, g["pool"]) if g["size"] == 1 else count
    for _ in range(limit*1000):
        if len(picks) == limit: break
        nums = [rng.choices(values, weights=w)[0] for w in main_weights] if g.get("digits") else sorted(sample_weights(values,main_weights,g["size"],rng))
        bonus = rng.choices(range(1,g["bonus"]+1),weights=bonus_weights)[0] if g.get("bonus") else None
        key = (tuple(nums),bonus)
        if key not in seen:
            seen.add(key); picks.append(dict(numbers=nums,bonus=bonus))
    return picks

def score(game, pick, draw):
    g = GAMES[game]
    matches = sum(a == b for a,b in zip(pick["numbers"],draw["numbers"])) if g.get("digits") else len(set(pick["numbers"]) & set(draw["numbers"]))
    special = bool(g.get("bonus") and pick.get("bonus") == draw.get("bonus"))
    exact = matches == g["size"] and (not g.get("bonus") or special)
    return dict(matches=matches,bonus=special,exact=exact)

def score_batch(game,picks,draw):
    scores = [score(game,p,draw) for p in picks]
    return dict(best=max(s["matches"] for s in scores), exact=sum(s["exact"] for s in scores),
                total_matches=sum(s["matches"] for s in scores), tickets=len(scores),
                bonus_matches=sum(s["bonus"] for s in scores))

def backtest(game, history, count=5, tests=200, seed=42):
    if len(history) < 80: raise ValueError("At least 80 draws are needed: 30 training draws and 50 test draws")
    if not 1 <= count <= 20 or not 50 <= tests <= 500: raise ValueError("Invalid test size or pick count")
    start = max(30,len(history)-tests)
    results = []
    for method in METHODS:
        rng = random.Random(seed)
        aggregates = Counter(); by_draw = []
        for i in range(start,len(history)):
            picks = generate(game,history[max(0,i-500):i],method,count,rng)
            s = score_batch(game,picks,history[i]); aggregates.update(s); by_draw.append(s["total_matches"]/s["tickets"])
        n = len(by_draw)
        avg = statistics.mean(by_draw)
        se = statistics.stdev(by_draw)/math.sqrt(n)
        results.append(dict(method=method,draws=n,tickets=aggregates["tickets"],exact=aggregates["exact"],
            average_matches=avg,ci95=[max(0,avg-1.96*se),avg+1.96*se],bonus_matches=aggregates["bonus_matches"]))
    g = GAMES[game]
    chance = g["size"]/10 if g.get("digits") else g["size"]*g.get("drawn",g["size"])/g["pool"]
    return dict(results=results,from_draw=history[start]["at"],to_draw=history[-1]["at"],expected_matches=chance,
        note="Chronological rolling test; training uses only earlier draws (last 500). Fixed methods; no automatic winner selection. Confidence intervals are approximate and do not prove predictive ability. Exact means all selected main numbers plus the special ball where applicable; Keno means all five spots. Partial matches are not prize wins. No payout or ROI calculation.")

def frequency(game, history):
    g=GAMES[game]; low=0 if g.get("digits") else 1
    counts=Counter(v for r in history for v in r["numbers"])
    return [dict(number=v,count=counts[v]) for v in range(low,low+g["pool"])]

def simulate(game, history, trials=10000, seed=42):
    """Monte Carlo calibration of one pre-specified frequency dispersion statistic."""
    if len(history)<30: raise ValueError("Load at least 30 draws")
    if not 1000 <= trials <= 100000: raise ValueError("Use 1,000–100,000 simulations")
    g=GAMES[game]; rng=random.Random(seed); low=0 if g.get("digits") else 1
    pool=list(range(low,low+g["pool"])); n=min(len(history),200)
    rows=history[-n:]; drawn=g.get("drawn",g["size"]); expected=n*drawn/g["pool"]
    observed=Counter(v for d in rows for v in d["numbers"])
    statistic=sum((observed[v]-expected)**2/expected for v in pool)
    exceed=0
    for _ in range(trials):
        counts=Counter()
        for _ in range(n): counts.update(rng.choices(pool,k=drawn) if g.get("digits") else rng.sample(pool,drawn))
        exceed += sum((counts[v]-expected)**2/expected for v in pool) >= statistic
    return dict(trials=trials,draws=n,statistic=statistic,p_value=(exceed+1)/(trials+1),
        note="Tests aggregate number-frequency dispersion against fair simulated draws. A small p-value is a reason to investigate data quality, not a prediction or proof of bias. Multiple tests can produce small p-values by chance.")

def sync_game(store,game):
    g=GAMES[game]
    if "id" not in g: raise ValueError("Keno requires CSV import; official bulk download not available")
    try:
        request=urllib.request.Request(f"https://www.valottery.com/api/v1/downloadall?gameId={g['id']}",headers={"User-Agent":"VAL/1.0 (draw history research)"})
        with urllib.request.urlopen(request,timeout=35) as response: text=response.read(12_000_000).decode("utf-8-sig")
        added=store.put(parse_official(game,text))
        if g.get("digits"):
            latest_request=urllib.request.Request(f"https://www.valottery.com/data/draw-games/{game}",headers={"User-Agent":"VAL/1.1 (draw history research)"})
            with urllib.request.urlopen(latest_request,timeout=35) as response: latest=response.read(3_000_000).decode("utf-8-sig")
            added+=store.put(parse_latest_digits(game,latest))
        with store.connect() as db: db.execute("INSERT OR REPLACE INTO sync VALUES(?,?,NULL)",(game,datetime.now(timezone.utc).isoformat()))
        store.ledger(game)
        return dict(game=game,added=added)
    except Exception as exc:
        with store.connect() as db: db.execute("INSERT INTO sync VALUES(?,NULL,?) ON CONFLICT(game) DO UPDATE SET error=excluded.error",(game,str(exc)))
        raise

def import_csv(store,text):
    rows=[]
    for line in csv.DictReader(io.StringIO(text)):
        game=line["game"].strip().lower()
        if game not in GAMES: raise ValueError("Unknown game: "+game)
        dt=datetime.fromisoformat(line["at"].replace("Z","+00:00"))
        if dt.tzinfo is None: raise ValueError("at must include a timezone offset")
        if dt > datetime.now(timezone.utc): raise ValueError("Future draw dates cannot be imported")
        if dt.astimezone(ET).date().isoformat()<history_cutoff(game): raise ValueError("Draw predates supported game cutoff")
        numbers=[int(x) for x in re.split(r"[ ,|]+",line["numbers"].strip())]
        bonus=int(line["bonus"]) if line.get("bonus","").strip() else None
        validate(game,numbers,bonus)
        stream=line.get("stream","").strip() or "Main"
        if GAMES[game].get("digits") and stream not in ("Day","Night"): raise ValueError("Digit games need Day or Night stream")
        rows.append(dict(game=game,at=dt.astimezone(timezone.utc).isoformat(),stream=stream,numbers=numbers,bonus=bonus,extra=None,source="User CSV import"))
    if not rows: raise ValueError("CSV contains no draw rows")
    # All rows are validated before any are written.
    added=store.put(rows)
    for game in {r["game"] for r in rows}: store.ledger(game)
    return dict(added=added,rows=len(rows))

class Handler(BaseHTTPRequestHandler):
    store: Store
    gate = threading.Lock()
    def send(self,status,data,kind="application/json"):
        raw=(json.dumps(data) if kind=="application/json" else data).encode()
        self.send_response(status); self.send_header("Content-Type",kind+"; charset=utf-8")
        self.send_header("Content-Length",str(len(raw))); self.send_header("X-Content-Type-Options","nosniff")
        self.end_headers(); self.wfile.write(raw)
    def do_GET(self):
        from urllib.parse import urlparse,parse_qs
        url=urlparse(self.path); params=parse_qs(url.query)
        try:
            if url.path=="/api/state":
                game=params.get("game",["pick3"])[0]; stream=params.get("stream",["All"])[0]
                history=self.store.history(game,stream)
                with self.store.connect() as db: sync=db.execute("SELECT at,error FROM sync WHERE game=?",(game,)).fetchone()
                return self.send(200,dict(games=GAMES,count=len(history),latest=history[-10:][::-1],
                    frequency=frequency(game,history[-500:]),frequency_draws=min(500,len(history)),
                    streams=sorted({r["stream"] for r in self.store.history(game)}),
                    sync=sync,ledger=self.store.ledger(game)))
            files={"/":"index.html","/app.js":"app.js","/style.css":"style.css"}
            if url.path not in files: return self.send(404,dict(error="Not found"))
            name=files[url.path]; kind={"html":"text/html","js":"text/javascript","css":"text/css"}[name.split(".")[-1]]
            return self.send(200,(ROOT/"web"/name).read_text(),kind)
        except (ValueError,KeyError) as exc: self.send(400,dict(error=str(exc)))
    def do_POST(self):
        # Local app: reject cross-origin browser writes, including DNS-rebinding hosts.
        host=self.headers.get("Host","").split(":")[0]
        origin=self.headers.get("Origin")
        if host not in ("localhost","127.0.0.1") or (origin and origin not in (f"http://{self.headers.get('Host')}",f"https://{self.headers.get('Host')}")):
            return self.send(403,dict(error="Only same-origin localhost requests are accepted"))
        if self.headers.get_content_type() != "application/json": return self.send(415,dict(error="Use application/json"))
        try:
            length=int(self.headers.get("Content-Length","0"))
            if not 0<length<=5_000_000: raise ValueError("Request must be between 1 byte and 5 MB")
            body=json.loads(self.rfile.read(length)); game=body.get("game","pick3")
            if game not in GAMES: raise ValueError("Unknown game")
            stream=body.get("stream","All"); history=self.store.history(game,stream)
            if self.path=="/api/import": return self.send(200,import_csv(self.store,body["csv"]))
            if self.path=="/api/sync": return self.send(200,sync_game(self.store,game))
            if self.path=="/api/picks":
                method=body.get("method","digit_conditional_v2" if GAMES[game].get("digits") else "ensemble")
                count=int(body.get("count",5))
                created=datetime.now(timezone.utc)
                history=[r for r in history if datetime.fromisoformat(r["at"])<=created]
                target=next_draw(game,created,stream) if game!="keno" else None
                model_meta=None
                if method=="digit_conditional_v2":
                    if not GAMES[game].get("digits"):
                        raise ValueError("Conditional v2 supports only Pick 3, Pick 4 and Pick 5")
                    from val_digit_formula_v2 import generate_picks
                    # Sequential transitions need ALL prior sessions.
                    training=[r for r in self.store.history(game)
                              if datetime.fromisoformat(r["at"])<=created]
                    picks,model_meta=generate_picks(game,training,target["stream"],count)
                    history=training
                else:
                    picks=generate(game,history,method,count)
                baseline=generate(game,[],"random",len(picks))
                pid=self.store.record(game,stream,method,picks,baseline,target=target,
                                      training_latest=history[-1] if history else None,
                                      created=created,model_meta=model_meta)
                return self.send(200,dict(id=pid,picks=picks,baseline=baseline,
                                          target=target,model_meta=model_meta))
            if self.path in ("/api/backtest","/api/simulate"):
                if not self.gate.acquire(blocking=False): return self.send(429,dict(error="An analysis is already running"))
                try:
                    data=backtest(game,history,int(body.get("count",5)),int(body.get("tests",200))) if self.path.endswith("backtest") else simulate(game,history,int(body.get("trials",10000)))
                finally: self.gate.release()
                return self.send(200,data)
            self.send(404,dict(error="Not found"))
        except (ValueError,KeyError,TypeError,IndexError) as exc: self.send(400,dict(error=str(exc)))
        except Exception as exc: self.send(502,dict(error="Operation failed: "+str(exc)))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=["serve","sync","backtest","simulate"],nargs="?",default="serve")
    parser.add_argument("--game",choices=[*GAMES,"all"],default="pick3")
    parser.add_argument("--db",default=str(ROOT/"data"/"val.sqlite3"))
    parser.add_argument("--port",type=int,default=8765)
    parser.add_argument("--interval",type=int,default=0,help="Optional official-history refresh interval in minutes while server runs (minimum 60)")
    parser.add_argument("--trials",type=int,default=10000)
    parser.add_argument("--stream",default="All")
    args=parser.parse_args(); store=Store(args.db)
    if args.command=="sync":
        for game in GAMES if args.game=="all" else [args.game]:
            if game=="keno": print("Keno: CSV import required"); continue
            try: print(json.dumps(sync_game(store,game)))
            except Exception as exc: print(json.dumps(dict(game=game,error=str(exc))))
    elif args.command in ("backtest","simulate"):
        if args.game=="all": parser.error("Choose a single game for analysis")
        history=store.history(args.game,args.stream)
        print(json.dumps(backtest(args.game,history) if args.command=="backtest" else simulate(args.game,history,args.trials),indent=2))
    else:
        if args.interval and args.interval<60: parser.error("Refresh interval must be at least 60 minutes")
        if args.interval:
            def updater():
                while True:
                    for game,g in GAMES.items():
                        if "id" in g:
                            try: sync_game(store,game)
                            except Exception as exc: print(f"Refresh {game}: {exc}",flush=True)
                    threading.Event().wait(args.interval*60)
            threading.Thread(target=updater,daemon=True).start()
        Handler.store=store
        server=ThreadingHTTPServer(("127.0.0.1",args.port),Handler)
        print(f"VAL is running at http://localhost:{args.port}",flush=True)
        try: server.serve_forever()
        except KeyboardInterrupt: server.server_close()

if __name__=="__main__": main()
