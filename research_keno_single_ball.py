"""Single-ball (1-spot) Keno walk-forward audit on official frozen result archive.

Each strategy predicts exactly ONE number 1..80 before each 20-ball draw.
A fair prediction has a 25% chance of appearing. Earlier 60% trains
conditional models, later 40% is historical chronological validation.
20 independent uniform controls are scored for sampling variability.
This is research, not a claim of an untouched prospective holdout.
"""
from __future__ import annotations
import gzip
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from research_keno import stable_rng
from research_keno_official import Counters

SOURCE=Path("reports/keno_official_history.json.gz")
OUTPUT_JSON=Path("reports/research_keno_single_ball.json")
OUTPUT_MD=Path("reports/research_keno_single_ball.md")
SEED=20261117
SPLIT=0.60
CONTROL_COUNT=20
MODEL_NAMES=("global_hot","recent_50_hot","recent_500_hot","recent_500_cold",
             "last_draw_ball","time_bucket_hot","lag_transition",
             "original_ensemble_weighted")
TEST_NAMES=MODEL_NAMES+("random_control",)


def get_rows(path=SOURCE):
    with gzip.open(path,"rt",encoding="utf-8") as fh:
        rows=json.load(fh)
    ids=[x["draw_id"] for x in rows]
    if ids!=sorted(set(ids)) or len(rows)<5000:
        raise ValueError("Frozen source must contain at least 5000 unique chronological draws")
    for row in rows:
        nums=row["numbers"]
        if len(nums)!=20 or len(set(nums))!=20 or any(not isinstance(x,int) or not 1<=x<=80 for x in nums):
            raise ValueError("Official draw malformed")
    return rows


def hour_bucket(row):
    return int(row["timestamp"][11:13])//6


def train_models(rows):
    freq=Counter()
    time_counts=[Counter() for _ in range(4)]
    time_n=[0]*4
    lag_den=[0]*81
    lag_counts=[[0]*81 for _ in range(81)]
    for row in rows:
        freq.update(row["numbers"])
        b=hour_bucket(row)
        time_counts[b].update(row["numbers"])
        time_n[b]+=1
    for before,after in zip(rows,rows[1:]):
        if after["draw_id"]!=before["draw_id"]+1:continue
        for a in before["numbers"]:
            lag_den[a]+=1
            for b in after["numbers"]:
                lag_counts[a][b]+=1
    # Regularized conditional probabilities; training selection only.
    lag_prob=[[.25]*81 for _ in range(81)]
    for a in range(1,81):
        denom=lag_den[a]+1500
        for b in range(1,81):
            lag_prob[a][b]=(lag_counts[a][b]+1500*.25)/denom
    # Uniform prior equal to 250 previous draws for 6-hour buckets.
    hour_weights=[]
    for k in range(4):
        hour_weights.append({b:(time_counts[k][b]+250*.25)/(time_n[k]+250)
                             for b in range(1,81)})
    return {"frequency":freq,"time":hour_weights,"lag":lag_prob,
            "train_draws":len(rows)}


def choose_max(vals, method, draw_id, reverse=False):
    # Stable unbiased tie-breaking; ties are resolved before target observed.
    keys=[(b,vals[b]) for b in range(1,81)]
    value=min(v for _,v in keys) if reverse else max(v for _,v in keys)
    choices=[b for b,v in keys if abs(v-value)<1e-13]
    return stable_rng(SEED,method,draw_id).choice(choices)


def pick_one(method, draw, prev, rolling, trained, seen_draws):
    ident=draw["draw_id"]
    is_next=prev is not None and ident==prev["draw_id"]+1
    if method=="global_hot":
        return choose_max(trained["frequency"],method,ident)
    if method=="recent_50_hot":
        freq=Counter(n for row in seen_draws[-50:] for n in row["numbers"])
        return choose_max(freq,method,ident)
    if method=="recent_500_hot":
        return choose_max(rolling.total,method,ident)
    if method=="recent_500_cold":
        return choose_max(rolling.total,method,ident,reverse=True)
    if method=="last_draw_ball":
        return stable_rng(SEED,method,ident).choice(prev["numbers"]) if is_next else stable_rng(SEED,method,ident).randint(1,80)
    if method=="time_bucket_hot":
        return choose_max(trained["time"][hour_bucket(draw)],method,ident)
    if method=="lag_transition":
        if not is_next:
            return stable_rng(SEED,method,ident).randint(1,80)
        on=prev["numbers"]
        vals={j:sum(trained["lag"][i][j] for i in on)/20 for j in range(1,81)}
        return choose_max(vals,method,ident)
    if method=="original_ensemble_weighted":
        weights=rolling.weights("ensemble")
        return stable_rng(SEED,method,ident).choices(range(1,81),weights=weights,k=1)[0]
    if method=="random_control":
        return stable_rng(SEED,method,ident).randint(1,80)
    raise ValueError(method)


def wilson(hits,n,z=1.96):
    p=hits/n
    den=1+z*z/n
    center=(p+z*z/(2*n))/den
    rad=z*math.sqrt((p*(1-p)+z*z/(4*n))/n)/den
    return [max(0,center-rad),min(1,center+rad)]


def binomial_approx_p(hits,n,baseline=.25):
    z=(abs(hits-n*baseline)-.5)/math.sqrt(n*baseline*(1-baseline))
    return min(1.0,math.erfc(max(0,z)/math.sqrt(2)))


def paired_p(x,y,n):
    # Paired discordance counts: x correct only, y correct only.
    b=sum(a and not c for a,c in zip(x,y))
    c=sum(c and not a for a,c in zip(x,y))
    disc=b+c
    p=1 if not disc else math.erfc(max(0,abs(b-c)-1)/math.sqrt(2*disc))
    return dict(model_only=b,control_only=c,discordants=disc,p_approx=p)


def evaluate(rows,split_fraction=SPLIT,controls=CONTROL_COUNT):
    split=int(len(rows)*split_fraction)
    train=rows[:split]
    later=rows[split:]
    if len(train)<2000 or len(later)<1000:raise ValueError("Split too small")
    trained=train_models(train)
    rolling=Counters(rows,split)
    hits={m:[] for m in TEST_NAMES}
    ctrl_sets=[[] for _ in range(controls)]
    picks_audit={m:[] for m in TEST_NAMES}
    for i in range(split,len(rows)):
        draw=rows[i]
        prev=rows[i-1]
        actual=set(draw["numbers"])
        seen=rows[:i] # Past only, target excluded.
        for m in TEST_NAMES:
            n=pick_one(m,draw,prev,rolling,trained,seen)
            if not isinstance(n,int) or not 1<=n<=80:raise AssertionError("Not exactly one legal ball")
            win=n in actual
            hits[m].append(win)
            if len(picks_audit[m])<4:
                picks_audit[m].append(dict(draw_id=draw["draw_id"],
                                           number=n,hit=win))
        for ctrl_num in range(controls):
            ball=stable_rng(SEED,"independent_control",ctrl_num,draw["draw_id"]).randint(1,80)
            ctrl_sets[ctrl_num].append(ball in actual)
        rolling.step(rows,i)
        if (i-split+1)%2000==0:
            print("Scored "+str(i-split+1)+" ONE-ball draws",flush=True)
    results={}
    n=len(later)
    for m in TEST_NAMES:
        values=hits[m]
        successes=sum(values)
        half=n//2
        p=binomial_approx_p(successes,n)
        paired=paired_p(values,hits["random_control"],n) if m!="random_control" else None
        results[m]=dict(
            draws=n,hits=successes,misses=n-successes,
            hit_rate=successes/n,
            wilson_95=wilson(successes,n),
            expected_random_hits=n*.25,
            approximate_p_vs_25_percent=p,
            bonferroni_9=min(1,p*len(TEST_NAMES)),
            first_half=dict(draws=half,hits=sum(values[:half]),rate=sum(values[:half])/half),
            second_half=dict(draws=n-half,hits=sum(values[half:]),
                             rate=sum(values[half:])/(n-half)),
            paired_vs_one_random=paired,
            sample_predeclared_picks=picks_audit[m]
        )
    control_rates=[sum(x)/n for x in ctrl_sets]
    return dict(version="val_keno_single_ball_chronological_v1",
                source="frozen official Virginia Keno API data",
                archive_draws=len(rows),
                training_draws=len(train),testing_draws=n,
                train_range=[train[0]["timestamp"],train[-1]["timestamp"]],
                test_range=[later[0]["timestamp"],later[-1]["timestamp"]],
                chance_per_ball=.25,
                model_specification="Single selected number from 1..80 per method per draw",
                candidate_names=list(MODEL_NAMES),
                research_caveat="Archive already explored; this is not an independent prospective holdout.",
                results=results,
                independent_random_controls=dict(count=controls,
                                                 rates=control_rates,
                                                 mean_rate=sum(control_rates)/controls,
                                                 min_rate=min(control_rates),max_rate=max(control_rates)))


def markdown(r):
    lines=[
        "# VAL Keno — ONE BALL predicted per drawing",
        "",
        "A real 1-spot prediction: one number 1 through 80, and 20 winning",
        "numbers in each official drawing. Fair hit probability: **25%**.",
        "No five-number combinations and no three tickets.",
        "",
        "Frozen official archive: "+format(r["archive_draws"],",")+" draws.",
        "Training: "+format(r["training_draws"],",")+" draws ("+r["train_range"][0]+
        " to "+r["train_range"][1]+").",
        "Later chronological test: "+format(r["testing_draws"],",")+" draws ("+
        r["test_range"][0]+" to "+r["test_range"][1]+").",
        "",
        "| One-ball method | Correct / draws | Hit rate | 95% Wilson interval | Adjusted p vs 25% | Earlier validation half | Later validation half |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"
    ]
    for m,v in r["results"].items():
        ci=v["wilson_95"]
        lines.append("| "+m+" | "+str(v["hits"])+"/"+str(v["draws"])+" | "+
                     format(v["hit_rate"]*100,".2f")+"% | "+
                     format(ci[0]*100,".2f")+"–"+format(ci[1]*100,".2f")+"% | "+
                     format(v["bonferroni_9"],".4g")+" | "+
                     format(v["first_half"]["rate"]*100,".2f")+"% | "+
                     format(v["second_half"]["rate"]*100,".2f")+"% |")
    c=r["independent_random_controls"]
    lines.extend([
        "",
        str(c["count"])+" extra independent random controls each predicted one",
        "ball per draw. Average correct rate "+
        format(c["mean_rate"]*100,".2f")+
        "%; range "+format(c["min_rate"]*100,".2f")+"–"+
        format(c["max_rate"]*100,".2f")+"%.",
        "",
        "Approximate binomial p-values use a continuity correction and",
        "Bonferroni adjustment for nine strategies. Because test variants",
        "were considered after earlier exploration of this archive, these",
        "are descriptive historical checks rather than independent proof.",
        "Winning numbers do NOT enter models until after their draw is scored.",
        "Only true 1-ball hits counted. Not a five-spot prize calculation.",
        "No live betting, no original VAL changes, no purchased tickets.",
        "",
        "Detailed paired comparisons and pick audit:",
        "[research_keno_single_ball.json](research_keno_single_ball.json).",
        ""
    ])
    return "\n".join(lines)


def main():
    rows=get_rows()
    result=evaluate(rows)
    result["generated_utc"]=datetime.now(timezone.utc).isoformat()
    OUTPUT_JSON.write_text(json.dumps(result,indent=2)+"\n")
    OUTPUT_MD.write_text(markdown(result)+"\n")
    print(json.dumps({
        "train":result["training_draws"],"test":result["testing_draws"],
        "control_mean":result["independent_random_controls"]["mean_rate"],
        "results":{name:{"hit_rate":v["hit_rate"],"hits":v["hits"],
                          "adjusted_p":v["bonferroni_9"]}
                   for name,v in result["results"].items()}
        },indent=2),flush=True)

if __name__=="__main__":main()
