"""VAL contextual adaptive full-Box prediction engine — research challenger.

New architecture: online Bayesian mixture of CONTEXT-conditioned generative
models. Unlike a digit-frequency-only model, it can ingest timestamp-verified
pre-cutoff equipment IDs and pretests, and it learns weekday/session context.
A continuously discounted likelihood optimizer reweights complete-draw
experts without fitting to the target result.

Experts:
  fair: independent uniform digits (always an eligible safety anchor)
  regime: position-specific, recent-window shrinkage to long-run background
  calendar: session + weekday hierarchical posterior per digit position
  equipment: equipment-specific position priors, IF and only IF a source was
             published AND retrieved strictly before the target wager cutoff
  pretest: actual pre-cutoff equipment pretest outcomes, if verified, updating
           the physical-device posterior before the official drawing

All expert probabilities are full ordered-outcome distributions. A predicted
complete ANY ORDER combination has mass equal to the sum of likelihoods over
its distinct permutations. No partial digit or position matches count.

This is a RESEARCH challenger only. No proof of equipment effects in the
real Virginia Lottery, and no hypothetical simulator metadata may flow to
the real production engine. A model that does not beat fair data must not
be deployed merely for passing tests.
"""
from __future__ import annotations

from collections import Counter, defaultdict, deque
from datetime import datetime, date
from functools import lru_cache
from itertools import combinations_with_replacement, permutations
import math
import random

from val_box import any_order_prize, box_ways, digits_key, random_box_picks

VERSION = "contextual_regime_box_v1"
GAMES = ("pick3", "pick4", "pick5")
ALL_EXPERTS = ("fair", "regime", "calendar", "equipment", "pretest")
LONG_WINDOW = 1800
SHORT_WINDOW = 160
BASE_PRIOR_DRAWS = 500.
REGIME_PRIOR_DRAWS = 180.
CONTEXT_PRIOR_DRAWS = 140.
EQUIPMENT_PRIOR_DRAWS = 55.
PRETEST_PRIOR_DRAWS = 20.
WEIGHT_DISCOUNT = .992
WEIGHT_TEMPERATURE = .5
PRIOR_WEIGHTS = {
    "fair":.65, "regime":.15, "calendar":.13,
    "equipment":.05, "pretest":.02,
}
TOP_PROPOSALS = 90


def _date(target):
    value=target.get("date")
    if value is None:
        value=datetime.fromisoformat(target["at"]).date().isoformat()
    return date.fromisoformat(value)


def _features(target):
    """No result values, simulator machine truth, or private pretests inferred.

    The ONLY eligible external evidence is an explicitly supplied source
    with a first-public timestamp and retrieval timestamp, BOTH before
    actual game wager cutoff. This validates temporal eligibility, not
    the source's factual authenticity: independent verification is still
    required before any real-world promotion.
    """
    result={}
    evidence=target.get("observables")
    if not isinstance(evidence,dict):
        return result
    close=target.get("wagers_close_utc")
    if not close:
        return result
    try:
        deadline=datetime.fromisoformat(close)
        if deadline.tzinfo is None:
            return result
    except (ValueError,TypeError):
        return result
    for name in ("equipment_id","pretests"):
        meta=evidence.get(name)
        if not isinstance(meta,dict):
            continue
        if not meta.get("source_url"):
            continue
        try:
            published=datetime.fromisoformat(meta["published_at_utc"])
            observed=datetime.fromisoformat(meta["observed_at_utc"])
            if published.tzinfo is None or observed.tzinfo is None:
                continue
        except (ValueError,KeyError,TypeError):
            continue
        if published>=deadline or observed>=deadline or observed<published:
            continue
        v=meta.get("value")
        if name=="equipment_id" and isinstance(v,(str,int)) and str(v).strip():
            result[name]=str(v)
        if name=="pretests" and isinstance(v,list) and 1<=len(v)<=30:
            result[name]=v
    return result


def _zero(width):
    return [[0]*10 for _ in range(width)]


def _change(store,draw,sign):
    for j,d in enumerate(draw):
        store[j][d]+=sign
        if store[j][d]<0:
            raise AssertionError("Negative rolling count")


def _posterior(counts,base,prior):
    n=sum(counts)
    denominator=n+prior
    return [(counts[d]+prior*base[d])/denominator for d in range(10)]


def _fair(width):
    return [[.1]*10 for _ in range(width)]


@lru_cache(maxsize=3000)
def _distinct_orders(combo):
    return tuple(set(permutations(combo)))


def full_box_mass(game,positions,combo):
    """Exact complete unordered outcome probability, repetitions included."""
    if game not in GAMES or len(combo)!=int(game[-1]):
        raise ValueError("Mismatched full Box candidate")
    return sum(math.prod(positions[j][d] for j,d in enumerate(order))
               for order in _distinct_orders(tuple(combo)))


def _joint_density(positions,digits):
    return math.prod(positions[j][d] for j,d in enumerate(digits))


class ContextualBox:
    def __init__(self,game,long_window=LONG_WINDOW,short_window=SHORT_WINDOW):
        if game not in GAMES or long_window<50 or not 10<=short_window<=long_window:
            raise ValueError("Bad contextual engine configuration")
        self.game=game
        self.width=int(game[-1])
        self.long_window=long_window
        self.short_window=short_window
        self.long=deque()
        self.short=deque()
        self.long_counts=_zero(self.width)
        self.short_counts=_zero(self.width)
        self.context_counts=defaultdict(lambda:_zero(self.width))
        self.equipment_counts=defaultdict(lambda:_zero(self.width))
        self.context_total=Counter()
        self.equipment_total=Counter()
        self.log_skill={expert:0. for expert in ALL_EXPERTS}
        self.observed=0

    def _context(self,target):
        if target["stream"] not in ("Day","Night"):
            raise ValueError("Invalid drawing session")
        return (target["stream"],_date(target).weekday())

    def _valid_pretests(self,raw):
        width=self.width
        if not isinstance(raw,list):
            return []
        if any(not isinstance(x,(list,tuple)) or len(x)!=width or
               any(type(d)!=int or not 0<=d<=9 for d in x)
               for x in raw):
            return []
        return raw

    def forecast(self,target):
        ctx=self._context(target)
        evidence=_features(target)
        background=[
            _posterior(self.long_counts[j],[.1]*10,BASE_PRIOR_DRAWS)
            for j in range(self.width)
        ]
        regime=[
            _posterior(self.short_counts[j],background[j],
                       REGIME_PRIOR_DRAWS)
            for j in range(self.width)
        ]
        calendar=[
            _posterior(self.context_counts[ctx][j],background[j],
                       CONTEXT_PRIOR_DRAWS)
            for j in range(self.width)
        ]
        experts={"fair":_fair(self.width),
                 "regime":regime,"calendar":calendar}
        eid=evidence.get("equipment_id")
        if eid is not None:
            equipment=[
                _posterior(self.equipment_counts[eid][j],background[j],
                           EQUIPMENT_PRIOR_DRAWS)
                for j in range(self.width)]
            experts["equipment"]=equipment
        raw_tests=self._valid_pretests(evidence.get("pretests"))
        if raw_tests:
            parent=experts.get("equipment",background)
            pretest_counts=_zero(self.width)
            for draw in raw_tests:
                _change(pretest_counts,draw,1)
            experts["pretest"]=[
                _posterior(pretest_counts[j],parent[j],
                           PRETEST_PRIOR_DRAWS)
                for j in range(self.width)]
        # Predictable exponentiated likelihood, with decayed prior evidence.
        # The uniform expert competes directly and can dominate fair draws.
        raw={}
        for name in experts:
            raw[name]=math.log(PRIOR_WEIGHTS[name]) + (
                WEIGHT_TEMPERATURE*self.log_skill[name])
        vmax=max(raw.values())
        weights={key:math.exp(value-vmax) for key,value in raw.items()}
        total=sum(weights.values())
        weights={key:value/total for key,value in weights.items()}
        return dict(version=VERSION,game=self.game,
                    target_date=_date(target).isoformat(),
                    stream=target["stream"],weights=weights,
                    models=experts,
                    eligible_features=tuple(sorted(evidence)),
                    observed_before=self.observed)

    def score(self,frozen,digits):
        if len(digits)!=self.width:
            raise ValueError("Wrong outcome width")
        likelihoods={name:_joint_density(positions,digits)
                     for name,positions in frozen["models"].items()}
        mixture=sum(frozen["weights"][name]*p
                    for name,p in likelihoods.items())
        fair=.1**self.width
        if not mixture>0:
            raise AssertionError("Nonpositive predictive density")
        return dict(log_gain=math.log(mixture/fair),
                    model_joint_probability=mixture,
                    expert_log_gains={name:math.log(p/fair)
                                      for name,p in likelihoods.items()})

    def choose(self,frozen,count=3,proposals=TOP_PROPOSALS):
        """Rank exact whole Box masses from an all-combination proposal pool.

        Proposal ranking uses position-averaged expert distributions;
        top candidates are then reranked by the exact sum of their
        distinct full permutations under the actual joint mixture.
        """
        if not 1<=count<=5 or proposals<count:
            raise ValueError("Invalid selection parameters")
        avg={}
        for name,positions in frozen["models"].items():
            avg[name]=[
                sum(positions[j][digit] for j in range(self.width)) /
                self.width for digit in range(10)]
        candidates=[]
        for combo in combinations_with_replacement(range(10),self.width):
            if not any_order_prize(self.game,combo):
                continue
            ways=box_ways(combo)
            approximate=ways*sum(
                frozen["weights"][name] *
                math.prod(p[d] for d in combo)
                for name,p in avg.items())
            candidates.append((approximate,combo))
        candidates.sort(key=lambda x:(-x[0],x[1]))
        # Include high-priority all-distinct alternatives for fair
        # coverage. This is a deterministic proposal beam, not an
        # unproven claim of global exact search optimality.
        proposed={combo for _,combo in candidates[:proposals]}
        distinct_added=0
        for _,combo in candidates:
            if len(set(combo))==self.width:
                proposed.add(combo)
                distinct_added+=1
            if distinct_added>=max(35,proposals//2):
                break
        exact=[]
        for combo in proposed:
            p=sum(weight*full_box_mass(self.game,
                                      frozen["models"][name],combo)
                  for name,weight in frozen["weights"].items())
            exact.append((p,combo))
        exact.sort(key=lambda x:(-x[0],x[1]))
        picks=[list(combo) for _,combo in exact[:count]]
        return dict(picks=picks,
                    predicted_full_box_probability=sum(
                        p for p,_ in exact[:count]),
                    fair_full_box_probability=sum(
                        box_ways(t) for t in picks)/10**self.width)

    def observe(self,target,result,frozen=None):
        """Update all parameters AFTER scoring this target; no lookahead."""
        digits=tuple(result)
        if len(digits)!=self.width or any(
                type(d)!=int or not 0<=d<=9 for d in digits):
            raise ValueError("Invalid completed digits")
        context=self._context(target)
        evidence=_features(target)
        if frozen is None:
            frozen=self.forecast(target)
        if frozen["observed_before"]!=self.observed:
            raise ValueError("Forecast was not frozen at this information time")
        measured=self.score(frozen,digits)
        for name in ALL_EXPERTS:
            self.log_skill[name]*=WEIGHT_DISCOUNT
        for name,gain in measured["expert_log_gains"].items():
            if name!="fair":
                self.log_skill[name]+=gain
        outgoing=(self.long.popleft() if len(self.long)>=self.long_window
                  else None)
        if outgoing is not None:
            _,old_digits,old_context,old_eid=outgoing
            _change(self.long_counts,old_digits,-1)
            _change(self.context_counts[old_context],old_digits,-1)
            self.context_total[old_context]-=1
            if old_eid is not None:
                _change(self.equipment_counts[old_eid],old_digits,-1)
                self.equipment_total[old_eid]-=1
        if len(self.short)>=self.short_window:
            _change(self.short_counts,self.short.popleft(),-1)
        self.short.append(digits)
        _change(self.short_counts,digits,+1)
        self.long.append((self.observed,digits,context,
                          evidence.get("equipment_id")))
        _change(self.long_counts,digits,+1)
        _change(self.context_counts[context],digits,+1)
        self.context_total[context]+=1
        eid=evidence.get("equipment_id")
        if eid is not None:
            _change(self.equipment_counts[eid],digits,+1)
            self.equipment_total[eid]+=1
        self.observed+=1
        return measured


def forecast_full_box(game,history,target,count=3,rng=None):
    """Simple research integration for a single future drawing."""
    machine=ContextualBox(game)
    for row in history:
        past_context=dict(date=_date(row).isoformat(),
                          stream=row["stream"])
        # Earlier observations may legitimately have authenticated
        # metadata, but never synthesize it from undocumented fields.
        if row.get("observables") is not None:
            past_context["observables"]=row["observables"]
            past_context["wagers_close_utc"]=row.get("wagers_close_utc")
        frozen=machine.forecast(past_context)
        machine.observe(past_context,row["numbers"],frozen)
    ready=machine.forecast(target)
    candidate=machine.choose(ready,count)
    control=random_box_picks(game,count,rng)
    return dict(frozen=ready,picks=candidate,
                fair_control=[x["numbers"] for x in control],
                formula_version=VERSION)
