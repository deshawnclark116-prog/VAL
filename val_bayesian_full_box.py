"""Research-only Bayesian predictors of COMPLETE unordered Pick 3/4/5 outcomes.

These models address structure the pooled-digit model cannot express:
1) exact_bag: posterior mass on whole previously observed digit multisets,
   with a prior equal to the probability of each complete Box under fair draws.
2) pair_shape: posterior digit-PAIR co-occurrence, including identical pairs,
   transformed into a normalized distribution of full digit multisets.
3) pooled: retained v2 iid-digit challenger for a fair comparison.

All probabilities include repeats and all-identical outcomes and sum to 1.
Winning-ticket ranking excludes all-identical Straight-only outcomes. All
features are updated only AFTER the target has been forecast and evaluated.

NO demonstrated real-lottery prediction advantage. Do not import these
research models into production without prospective independent validation.
"""
from __future__ import annotations

from collections import Counter,deque
from functools import lru_cache
from itertools import combinations,combinations_with_replacement
from math import comb,exp,log,prod
from val_box import any_order_prize,box_ways,digits_key
from research_pooled_digit_followup import probabilities as pooled_digit_probs

VERSION="bayesian_full_box_structural_v1"
GAMES=("pick3","pick4","pick5")
WINDOW=5000
EXACT_PRIOR_DRAWS=3000
PAIR_PRIOR_DRAWS=3000
METHODS=("fair","pooled","exact_bag","pair_shape")


@lru_cache(None)
def combos(game):
    if game not in GAMES:
        raise ValueError(game)
    width=int(game[-1])
    items=[]
    for digits in combinations_with_replacement(range(10),width):
        pairs=tuple(tuple(sorted((digits[i],digits[j])))
                    for i,j in combinations(range(width),2))
        fair=box_ways(digits)/(10**width)
        items.append((digits,fair,pairs,any_order_prize(game,digits)>0))
    if abs(sum(row[1] for row in items)-1.)>1e-12:
        raise AssertionError("Fair multiset distribution must total one")
    return tuple(items)


def pair_fair(pair):
    if len(pair)!=2:
        raise ValueError("Invalid unordered digit pair")
    return .01 if pair[0]==pair[1] else .02


class BayesianBox:
    def __init__(self,game,window=WINDOW):
        if game not in GAMES or window<50:
            raise ValueError("Invalid game/window")
        self.game=game
        self.width=int(game[-1])
        self.window=window
        self.queue=deque()
        self.counts=Counter()
        self.digits=Counter()
        self.pairs=Counter()
        self.pairs_per_draw=comb(self.width,2)

    def _change(self,draw,sign):
        key=digits_key(draw)
        self.counts[key]+=sign
        if not self.counts[key]:
            del self.counts[key]
        for d in draw:
            self.digits[d]+=sign
            if not self.digits[d]:
                del self.digits[d]
        for a,b in combinations(range(self.width),2):
            key2=tuple(sorted((draw[a],draw[b])))
            self.pairs[key2]+=sign
            if not self.pairs[key2]:
                del self.pairs[key2]

    def observe(self,row):
        draw=tuple(row["numbers"])
        if len(draw)!=self.width or any(type(d) is not int or
                not 0<=d<=9 for d in draw):
            raise ValueError("Invalid result")
        self._change(draw,1)
        self.queue.append(draw)
        if len(self.queue)>self.window:
            self._change(self.queue.popleft(),-1)

    def distributions(self):
        """Return four complete, normalized multiset distributions.

        The pair potential is a log-linear normalized *joint* distribution,
        not a collection of independent digit guesses.
        """
        n=len(self.queue)
        items=combos(self.game)
        pooled=pooled_digit_probs([self.digits[d] for d in range(10)],
                                  self.width)
        p_exact={}
        p_pooled={}
        weights_pair={}
        pairs_in_draw=self.pairs_per_draw
        pair_den=(n+PAIR_PRIOR_DRAWS)*pairs_in_draw
        log_enrichment={}
        for a in range(10):
            for b in range(a,10):
                pair=(a,b)
                empirical=(self.pairs[pair]+
                            PAIR_PRIOR_DRAWS*pairs_in_draw*pair_fair(pair)
                           )/pair_den
                log_enrichment[pair]=log(empirical/pair_fair(pair))
        for key,q,pairs,_eligible in items:
            p_exact[key]=(self.counts[key]+EXACT_PRIOR_DRAWS*q)/(
                n+EXACT_PRIOR_DRAWS)
            p_pooled[key]=box_ways(key)*prod(pooled[d] for d in key)
            # Averaging enrichment across the draw's pairs protects
            # larger Pick5 sets from an uncalibrated exponent explosion.
            score=sum(log_enrichment[p] for p in pairs)/len(pairs)
            weights_pair[key]=q*exp(score)
        z=sum(weights_pair.values())
        models={
            "fair":{key:q for key,q,_,_ in items},
            "pooled":p_pooled,
            "exact_bag":p_exact,
            "pair_shape":{key:v/z for key,v in weights_pair.items()},
        }
        for name,p in models.items():
            if abs(sum(p.values())-1.)>1e-9 or any(v<=0 for v in p.values()):
                raise AssertionError("Model not a joint probability: "+name)
        return models

    def top_box(self,dist,count=3):
        """Optimal distinct complete multiset outcomes for a fixed budget."""
        if not 1<=count<=5:
            raise ValueError(count)
        ranked=sorted(
            ((p,key) for key,p in dist.items()
             if any_order_prize(self.game,key)),
            key=lambda x:(-x[0],x[1]))
        return [list(key) for p,key in ranked[:count]]

    def predict(self,count=3):
        distributions=self.distributions()
        return {
            name:dict(picks=self.top_box(dist,count),
                      distribution=dist)
            for name,dist in distributions.items()
        }
