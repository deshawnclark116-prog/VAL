"""VAL Night Conditional Box candidate: observable Day -> next Night information.

Every forecast is computed BEFORE observing that Night result. Training pairs
consist only of completed earlier Day/Night draws sharing an Eastern-local date.
Hidden equipment labels, simulator truth, and pretests are never exposed.

Two fully normalized joint distributions for Night's ordered digits:
- presence: shrink the empirical Night probability of each digit conditional
  on whether the same digit appeared in that day's Day combination.
- tokens: shrink the full Night distribution conditional on each digit that
  appeared in the Day combination; average across Day digit observations.

Each distribution induces an exact complete-Box probability by summing all
distinct permutations. For these exchangeable product distributions, this is
exactly box_ways(combo) * product(prob[d] for d in combo).

Evidence is a predictable likelihood-ratio e-process against the independent
fair-null Night drawing, with fixed nonoverlapping 1600-pair epochs and
summable alpha allocation. Recent positive validation and a strict family
threshold are required. Failure to detect a signal means random Box
coverage, NOT a forced conditional forecast.

This is a separate RESEARCH challenger, not evidence that an actual draw
machine is shared between Day and Night.
"""
from __future__ import annotations

from collections import deque
from datetime import datetime
from itertools import combinations_with_replacement
import math
import random

from val import ET
from val_box import any_order_prize, box_ways, random_box_picks

VERSION = "day_night_conditional_box_v1"
EXPERTS = ("presence", "tokens")
WINDOW = 1800
WARMUP = 180
ANCHOR = "2024-01-01"
EPOCH = 1600
PREWARM = 450
RECENT = 320
RECENT_MIN = 200
MIN_MEAN_LOG_GAIN = .002
# 0.005 fair-null family budget across 2 experts * 3 digit games * all
# predefined future epochs. Sum 1/((k+1)(k+2)) across k>=0 equals 1.
GATE_0 = math.log(6 / .005)
PRIOR_BASE = 100.
PRIOR_CONDITIONAL = 140.
GAMES = ("pick3", "pick4", "pick5")


def _date(row):
    if "date" in row:
        return row["date"]
    return datetime.fromisoformat(row["at"]).astimezone(ET).date().isoformat()


def _smooth(counts, base, prior):
    total = sum(counts) + prior
    return tuple((counts[d] + prior * base[d]) / total for d in range(10))


def _normalized(values):
    total = sum(values)
    if total <= 0:
        raise ValueError("Empty probabilities")
    distribution = tuple(v / total for v in values)
    if abs(sum(distribution)-1.) > 1e-12 or min(distribution) <= 0:
        raise AssertionError("Unnormalized conditional forecast")
    return distribution


def full_box_probability(game, probability, combo):
    """Exact unordered outcome probability; multiplicity is preserved."""
    if game not in GAMES or len(combo) != int(game[-1]):
        raise ValueError("Invalid Box candidate")
    return box_ways(combo) * math.prod(prob[d] for d in combo)


def optimal_boxes(game, probability, count=3):
    """Find the highest complete-Box probabilities; no beam approximation."""
    width = int(game[-1])
    if len(probability) != 10 or not 1 <= count <= 5:
        raise ValueError("Invalid candidate parameters")
    ranked = (
        (full_box_probability(game, probability, combo), combo)
        for combo in combinations_with_replacement(range(10), width)
        if any_order_prize(game, combo) > 0
    )
    ranked = sorted(ranked, key=lambda x: (-x[0], x[1]))
    return [dict(numbers=list(combo), box_probability=p, play_type="any_order",
                 formula_version=VERSION)
            for p,combo in ranked[:count]]


class _NightCounts:
    def __init__(self, width, window=WINDOW):
        self.width = width
        self.window = window
        self.queue = deque()
        self.night = [0]*10
        self.presence_success = [[0]*2 for _ in range(10)]
        self.presence_exposure = [[0]*2 for _ in range(10)]
        self.token_success = [[0]*10 for _ in range(10)]
        self.token_exposure = [0]*10

    def _apply(self, day, night, sign):
        if len(day) != self.width or len(night) != self.width:
            raise ValueError("Wrong Day/Night width")
        if any(type(d) is not int or not 0 <= d < 10 for d in day+night):
            raise ValueError("Digit outside 0-9")
        present = set(day)
        for d in night:
            self.night[d] += sign
        for digit in range(10):
            state = int(digit in present)
            self.presence_exposure[digit][state] += sign * self.width
            self.presence_success[digit][state] += sign * night.count(digit)
        for d in day:
            self.token_exposure[d] += sign * self.width
            for n in night:
                self.token_success[d][n] += sign

    def add(self, day, night):
        a, b = tuple(day), tuple(night)
        self._apply(a,b,+1)
        self.queue.append((a,b))
        if len(self.queue) > self.window:
            x,y = self.queue.popleft()
            self._apply(x,y,-1)

    def base(self):
        return _smooth(self.night, (.1,)*10, PRIOR_BASE * 10)

    def distributions(self, day):
        if len(day)!=self.width:
            raise ValueError("Day digits must match target game width")
        base=self.base()
        pres=[]
        for d in range(10):
            state=int(d in day)
            n=self.presence_exposure[d][state]
            yes=self.presence_success[d][state]
            pres.append((yes+PRIOR_CONDITIONAL*base[d]) /
                        (n+PRIOR_CONDITIONAL))
        token=[]
        for d in range(10):
            token.append(_smooth(self.token_success[d], base,
                                 PRIOR_CONDITIONAL))
        mixture=[sum(token[d][k] for d in day)/len(day)
                 for k in range(10)]
        return {"presence":_normalized(pres),
                "tokens":_normalized(mixture)}


class NightConditionalEvidence:
    def __init__(self, game, window=WINDOW):
        if game not in GAMES:
            raise ValueError(game)
        self.game = game
        self.width=int(game[-1])
        self.window=window
        self.paired=0
        self.accumulator=_NightCounts(self.width, window)
        self.log_e={m:0. for m in EXPERTS}
        self.recent={m:deque(maxlen=RECENT) for m in EXPERTS}

    def predict(self, day_numbers, epoch_index=0):
        p=self.accumulator.distributions(day_numbers)
        threshold=GATE_0 + math.log((epoch_index+1)*(epoch_index+2))
        valid=[]
        details={}
        for name in EXPERTS:
            gains=list(self.recent[name])
            n=len(gains)
            half=n//2
            first=sum(gains[:half])/half if half else 0.
            second=sum(gains[half:])/(n-half) if n>half else 0.
            avg=sum(gains)/n if n else 0.
            selected=(self.log_e[name]>=threshold and
                      n>=RECENT_MIN and first>0 and second>0 and
                      avg>MIN_MEAN_LOG_GAIN)
            details[name]=dict(log_e=self.log_e[name],avg=avg,
                               first=first,second=second,passed=selected)
            if selected:
                valid.append(name)
        expert=max(valid,key=lambda x:self.log_e[x]) if valid else None
        return expert, p[expert] if expert else None, dict(
            epoch=epoch_index,threshold=threshold,paired=self.paired,
            experts=details)

    def observe(self, day_numbers, night_numbers, include_evidence=True):
        # Called only AFTER the forecast for this Night has been frozen/scored.
        if include_evidence and self.paired >= WARMUP:
            forecasts=self.accumulator.distributions(day_numbers)
            fair=self.width * math.log(.1)
            for name in EXPERTS:
                inc=sum(math.log(forecasts[name][d]) for d in night_numbers)-fair
                self.log_e[name]+=inc
                self.recent[name].append(inc)
        self.accumulator.add(day_numbers,night_numbers)
        self.paired+=1


def fit_before(game,history,stream):
    """Train using only chronological completed pairs. Nothing from target."""
    if game not in GAMES or stream not in ("Day","Night"):
        raise ValueError("Unsupported digit game or session")
    if stream=="Day" or not history or history[-1]["stream"]!="Day":
        return None, None, {"reason":"no completed same-day Day drawing"}
    now_day=history[-1]
    date=_date(now_day)
    if date < ANCHOR:
        return None,None,{"reason":"before fixed study origin"}
    pairs=[]
    pending={}
    for row in history[:-1]:
        day=_date(row)
        if day < ANCHOR:
            continue
        if row["stream"]=="Day":
            pending[day]=tuple(row["numbers"])
        elif row["stream"]=="Night" and day in pending:
            pairs.append((pending.pop(day),tuple(row["numbers"])))
    if not pairs:
        return None,None,{"reason":"no complete earlier Day/Night pairs"}
    epoch=len(pairs)//EPOCH
    boundary=epoch*EPOCH
    previous=pairs[max(0,boundary-PREWARM):boundary]
    current=pairs[boundary:]
    model=NightConditionalEvidence(game)
    for d,n in previous:
        model.observe(d,n,include_evidence=False)
    # These warmup pairs fit parameters; their observed Night outcomes
    # must never enter this epoch's log evidence.
    model.log_e={name:0. for name in EXPERTS}
    model.recent={name:deque(maxlen=RECENT) for name in EXPERTS}
    for d,n in current:
        model.observe(d,n)
    selected, probs, data=model.predict(tuple(now_day["numbers"]),epoch)
    data.update(
        last_day=date,
        warmup_pairs=len(previous),
        current_epoch_pairs=len(current),
        selected_expert=selected,
        revision=VERSION,
    )
    return selected,probs,data


def candidate_picks(game, history, stream, count=3, rng=None):
    selected, probabilities, diagnostics=fit_before(game,history,stream)
    if probabilities is None:
        return selected,random_box_picks(game,count,rng),diagnostics
    return selected,optimal_boxes(game,probabilities,count),diagnostics
