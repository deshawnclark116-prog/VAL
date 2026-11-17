"""Research-only Keno structural/randomness audit on frozen official VAL history.

PRE-REGISTERED candidate tests:
  * Marginal number-frequency drift (80 tests).
  * Within-drawing co-occurring pairs (3,160 tests).
  * Lagged drawing intersections (1,2,3,5,10,20 draws).
  * Per-number next-draw reappearance (80 tests).
  * Local draw-time frequency departures (4x80 tests).
  * Actual 1-ticket prediction: fair control, static frequency, lagged repeat,
    lagged transition matrix, and the previous VAL ensemble first ticket.

The earliest 60% of 10,665 official records estimates models/flags anomalies;
the last 40% measures conditional predictions and checks flagged anomalies.
The history has already been analyzed in prior experiments, so this is
CHRONOLOGICAL internal validation, not independently prospective evidence.
All draws and tickets are scored once; no source files or live picks changed.
"""
from __future__ import annotations

import json
import math
from collections import Counter
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

from research_keno_one_ticket import read_archive
from research_keno_official import Counters, predict
from research_keno import PRIZE_FIVE_SPOT, exact_fair_match_probabilities, match_count, stable_rng

DEST_JSON=Path("reports/research_keno_dependencies.json")
DEST_MD=Path("reports/research_keno_dependencies.md")
PAIR_NULL=20*19/(80*79)
PROB=.25
LAGS=(1,2,3,5,10,20)
SMOOTH_STATIC=2000
SMOOTH_TRANSITION=2000
SMOOTH_REPEAT=1000
SPLIT_FRAC=.60
SEED=20261117


def two_sided_z(z):
    return math.erfc(abs(z)/math.sqrt(2))


def corrected(p,n):
    return min(1.0,p*n)


def z_binomial(count,n,p):
    return (count-n*p)/math.sqrt(n*p*(1-p)) if n else 0.0


def pair_counts(rows):
    c=Counter()
    for r in rows:
        for a,b in combinations(sorted(r["numbers"]),2):
            c[(a,b)]+=1
    return c


def pair_discovery(train,valid):
    first=pair_counts(train)
    later=pair_counts(valid)
    n1,n2=len(train),len(valid)
    findings=[]
    for a in range(1,81):
        for b in range(a+1,81):
            pair=(a,b)
            z=z_binomial(first[pair],n1,PAIR_NULL)
            raw=two_sided_z(z)
            findings.append((raw,z,pair))
    findings.sort(key=lambda a:a[0])
    selected=[]
    for raw,z,pair in findings[:20]:
        k2=later[pair]
        z2=z_binomial(k2,n2,PAIR_NULL)
        selected.append({
            "pair":list(pair),"discovery_count":first[pair],
            "discovery_expected":round(n1*PAIR_NULL,2),
            "discovery_z":round(z,4),"discovery_p":raw,
            "discovery_bonferroni_3160":corrected(raw,3160),
            "validation_count":k2,"validation_expected":round(n2*PAIR_NULL,2),
            "validation_z":round(z2,4),"validation_p":two_sided_z(z2),
            "validation_bonferroni_20":corrected(two_sided_z(z2),20),
            "same_effect_direction":(z*z2>0)
        })
    return {
        "tests":3160,
        "expected_probability_per_pair":PAIR_NULL,
        "discovery_bonferroni_significant":sum(corrected(x[0],3160)<.05 for x in findings),
        "selected_20_validation_bonferroni_significant":sum(
            r["validation_bonferroni_20"]<.05 for r in selected),
        "top_discovery_20_with_validation":selected
    }


def frequency_anomalies(train,valid):
    c1=Counter(x for r in train for x in r["numbers"])
    c2=Counter(x for r in valid for x in r["numbers"])
    rows=[]
    for n in range(1,81):
        z1=z_binomial(c1[n],len(train),PROB)
        z2=z_binomial(c2[n],len(valid),PROB)
        delta=c1[n]/len(train)-c2[n]/len(valid)
        zdelta=delta/math.sqrt(PROB*(1-PROB)*(1/len(train)+1/len(valid)))
        rows.append({"number":n,"train_count":c1[n],"train_z":round(z1,4),
                     "train_p_corrected_80":corrected(two_sided_z(z1),80),
                     "validation_count":c2[n],"validation_z":round(z2,4),
                     "validation_p_corrected_80":corrected(two_sided_z(z2),80),
                     "between_periods_z":round(zdelta,4),
                     "between_periods_p_corrected_80":corrected(two_sided_z(zdelta),80)})
    ranked=sorted(rows,key=lambda x:x["train_p_corrected_80"])
    return {
       "tests":80,
       "discovery_significant":sum(x["train_p_corrected_80"]<.05 for x in rows),
       "validation_significant":sum(x["validation_p_corrected_80"]<.05 for x in rows),
       "early_vs_late_significant":sum(x["between_periods_p_corrected_80"]<.05 for x in rows),
       "top_train_anomalies_checked_on_validation":ranked[:12],
    }


def contiguous_pairs(rows,lag=1):
    for idx in range(lag,len(rows)):
        a,b=rows[idx-lag],rows[idx]
        if b["draw_id"]-a["draw_id"]==lag:
            yield a,b


def lag_analysis(rows):
    out=[]
    var=20*PROB*(1-PROB)*(80-20)/(80-1)
    for lag in LAGS:
        n=0; overlap=0
        for a,b in contiguous_pairs(rows,lag):
            n+=1
            overlap+=len(set(a["numbers"])&set(b["numbers"]))
        if n<50:raise ValueError("Not enough contiguous lag pairs")
        mean=overlap/n
        z=(overlap-5*n)/math.sqrt(n*var)
        out.append({"lag":lag,"complete_pairs":n,
                    "mean_overlapping_numbers":round(mean,6),
                    "null_mean_overlap":5,"z":round(z,4),
                    "p_approx":two_sided_z(z),
                    "bonferroni_6":corrected(two_sided_z(z),len(LAGS))})
    return {"tests":len(LAGS),
            "significant":sum(x["bonferroni_6"]<.05 for x in out),
            "lags":out}


def transition_anomalies(train,valid):
    def collect(rows):
        prev=Counter();reappear=Counter()
        for a,b in contiguous_pairs(rows,1):
            bset=set(b["numbers"])
            for n in a["numbers"]:
                prev[n]+=1
                if n in bset:reappear[n]+=1
        return prev,reappear
    pa,ra=collect(train)
    pb,rb=collect(valid)
    flags=[]
    for n in range(1,81):
        if pa[n]<20 or pb[n]<20:continue
        za=z_binomial(ra[n],pa[n],.25)
        zb=z_binomial(rb[n],pb[n],.25)
        flags.append({
            "number":n,
            "discovery_prev_seen":pa[n],"discovery_reappear":ra[n],
            "discovery_z":round(za,4),
            "discovery_p_corrected_80":corrected(two_sided_z(za),80),
            "validation_prev_seen":pb[n],"validation_reappear":rb[n],
            "validation_z":round(zb,4),
            "validation_p_corrected_80":corrected(two_sided_z(zb),80),
        })
    flags.sort(key=lambda x:x["discovery_p_corrected_80"])
    return {"tests":len(flags),
            "discovery_significant":sum(x["discovery_p_corrected_80"]<.05 for x in flags),
            "validation_significant":sum(x["validation_p_corrected_80"]<.05 for x in flags),
            "top_10":flags[:10]}


def time_bucket(timestamp):
    return int(timestamp[11:13])//6


def time_effects(rows):
    groups=[Counter() for _ in range(4)]
    counts=[0]*4
    for r in rows:
        b=time_bucket(r["timestamp"])
        if b not in range(4):raise ValueError("Invalid official Keno timestamp")
        counts[b]+=1
        groups[b].update(r["numbers"])
    tests=[]
    for b in range(4):
        for n in range(1,81):
            z=z_binomial(groups[b][n],counts[b],PROB)
            tests.append({"hour_block":b,"number":n,"count":groups[b][n],
                          "z":round(z,4),
                          "p_adjusted_320":corrected(two_sided_z(z),320)})
    tests.sort(key=lambda a:a["p_adjusted_320"])
    return {"tests":320,"draws_per_6hour_block":counts,
            "significant":sum(x["p_adjusted_320"]<.05 for x in tests),
            "top_10":tests[:10]}


def fit_models(train):
    n=len(train)
    frequency=Counter(i for r in train for i in r["numbers"])
    static=[(frequency[x]+SMOOTH_STATIC*PROB)/(n+SMOOTH_STATIC)
            for x in range(1,81)]
    prev_counts=[0]*81
    observed=[[0]*81 for _ in range(81)]
    overlap_sum=0;num_edges=0
    for a,b in contiguous_pairs(train,1):
        num_edges+=1
        aset=a["numbers"]
        bset=set(b["numbers"])
        overlap_sum+=len(bset.intersection(aset))
        for i in aset:
            prev_counts[i]+=1
            for j in bset:
                observed[i][j]+=1
    if num_edges<1000:raise ValueError("Insufficient training transitions")
    cond=[[.25]*81]
    for i in range(1,81):
        denom=prev_counts[i]+SMOOTH_TRANSITION
        cond.append([0.0]+[(observed[i][j]+SMOOTH_TRANSITION*PROB)/denom
                          for j in range(1,81)])
    p_repeat=(overlap_sum+5*SMOOTH_REPEAT)/(20*(num_edges+SMOOTH_REPEAT))
    return {"static":static,"transition":cond,"p_repeat":p_repeat,
            "train_transitions":num_edges,"overlap_train_mean":overlap_sum/num_edges}


def forecasts(fit,prev,consecutive):
    if not consecutive:
        return {"frequency":[.25]*80,"lag_repeat":[.25]*80,
                "transition":[.25]*80}
    on=set(prev["numbers"])
    q=fit["p_repeat"]
    out={}
    out["frequency"]=fit["static"]
    out["lag_repeat"]=[q if n in on else (1-q)/3 for n in range(1,81)]
    transition=fit["transition"]
    out["transition"]=[
        sum(transition[i][j] for i in on)/20 for j in range(1,81)]
    for name,p in out.items():
        if abs(sum(p)-20)>1e-8 or any(v<=0 or v>=1 for v in p):
            raise AssertionError("Probabilities not positive or sum != 20: "+name)
    return out


def top_five(prob,draw_id,name):
    # Ties broken independently from lottery outcome; deterministic hash
    rand=stable_rng(SEED,name,draw_id)
    ties=[rand.random() for _ in range(80)]
    return sorted(sorted(range(1,81),
                         key=lambda x:(-prob[x-1],ties[x-1]))[:5])


def mean_and_se(vals):
    n=len(vals)
    avg=sum(vals)/n
    if n<2:return avg,0.0
    sd2=sum((v-avg)**2 for v in vals)/(n-1)
    return avg,math.sqrt(sd2/n)


def validate_forecasts(train,validation):
    fit=fit_models(train)
    names=("uniform_random","original_ensemble","frequency","lag_repeat","transition")
    res={name:{"counts":Counter(),"gross":0,"brier_gain":[],"first_half":Counter(),
               "second_half":Counter()} for name in names}
    # Accurate parity with existing VAL: rolling 500-draw counts update only
    # after each actual target result is observed.
    joined=train+validation
    start=len(train)
    roll=Counters(joined,start)
    ntest=len(validation)
    test_mid=start+ntest//2
    for idx in range(start,len(joined)):
        current=joined[idx]
        previous=joined[idx-1]
        consecutive=(current["draw_id"]-previous["draw_id"]==1)
        p=forecasts(fit,previous,consecutive)
        choices={
            "uniform_random":sorted(
                stable_rng(SEED,"uniform_random",current["draw_id"]).sample(range(1,81),5)),
            "original_ensemble":predict(
                roll.weights("ensemble"),
                stable_rng(SEED,"ensemble",current["draw_id"]))[0],
        }
        for name,arr in p.items():
            choices[name]=top_five(arr,current["draw_id"],name)
        actual=set(current["numbers"])
        half="first_half" if idx<test_mid else "second_half"
        for name,pick in choices.items():
            hits=len(actual.intersection(pick))
            payout=PRIZE_FIVE_SPOT[hits]
            entry=res[name]
            entry["counts"][hits]+=1
            entry["gross"]+=payout
            entry[half]["tickets"]+=1
            entry[half]["gross"]+=payout
            entry[half]["five"]+=hits==5
            if name in p:
                # Brier score benchmark uniform = 0.1875 on every draw.
                bs=sum((float(j in actual)-p[name][j-1])**2
                       for j in range(1,81))/80
                entry["brier_gain"].append(.1875-bs)
        roll.step(joined,idx)
    var_hits=5*.25*.75*(80-5)/(80-1)
    results={}
    for name,v in res.items():
        n=sum(v["counts"].values())
        avg_hits=sum(k*c for k,c in v["counts"].items())/n
        z=(avg_hits-1.25)/math.sqrt(var_hits/n)
        brier_delta,brier_se=mean_and_se(v["brier_gain"]) if v["brier_gain"] else (None,None)
        results[name]={
            "draws":n,
            "exactly_one_ticket_each_draw":True,
            "hit_distribution":{str(k):v["counts"][k] for k in range(6)},
            "average_matches":round(avg_hits,6),
            "hits_z_vs_random":round(z,5),
            "hits_p_two_sided":two_sided_z(z),
            "hits_p_bonferroni_5":corrected(two_sided_z(z),len(names)),
            "perfect_five_hits":v["counts"][5],
            "expected_five_hits_fair":round(n*exact_fair_match_probabilities()[5],3),
            "gross_dollars":v["gross"],"ticket_cost_dollars":n,
            "net_dollars":v["gross"]-n,
            "gross_per_dollar":round(v["gross"]/n,6),
            "mean_brier_advantage_over_fair":None if brier_delta is None else round(brier_delta,9),
            "brier_advantage_95pct_interval":None if brier_delta is None else [
                round(brier_delta-1.96*brier_se,9),round(brier_delta+1.96*brier_se,9)],
            "first_half":dict(v["first_half"]),
            "second_half":dict(v["second_half"]),
        }
    return {
        "discovery_transition_pairs":fit["train_transitions"],
        "discovery_mean_consecutive_overlap":round(fit["overlap_train_mean"],6),
        "discovery_p_next_draw_repeat":round(fit["p_repeat"],8),
        "prediction_models":results,
    }


def analyze(rows):
    sep=int(SPLIT_FRAC*len(rows))
    discovery=rows[:sep]
    validation=rows[sep:]
    if len(discovery)<2000 or len(validation)<1000:
        raise ValueError("Insufficient chronology")
    result={
        "version":"val_keno_structure_v1",
        "source":"previously archived Virginia Lottery public gameId=30 drawnumbers",
        "archive_draws":len(rows),
        "discovery_draws":len(discovery),
        "chronological_validation_draws":len(validation),
        "discovery_period":[discovery[0]["timestamp"],discovery[-1]["timestamp"]],
        "validation_period":[validation[0]["timestamp"],validation[-1]["timestamp"]],
        "draw_id_gaps":sum(max(0,b["draw_id"]-a["draw_id"]-1)
                           for a,b in zip(rows,rows[1:])),
        "frequency_test":frequency_anomalies(discovery,validation),
        "cooccurrence_test":pair_discovery(discovery,validation),
        "serial_overlap_discovery":lag_analysis(discovery),
        "serial_overlap_validation":lag_analysis(validation),
        "number_transition_test":transition_anomalies(discovery,validation),
        "time_of_day_discovery":time_effects(discovery),
        "time_of_day_validation":time_effects(validation),
        "out_of_sample_one_ticket":validate_forecasts(discovery,validation),
        "note":"Chronological validation is NOT a truly untouched prospective holdout; earlier experiments viewed same archive."
    }
    return result


def md_report(r):
    p=r["out_of_sample_one_ticket"]["prediction_models"]
    lines=[
        "# VAL Keno — structural randomness investigation",
        "",
        "Official archived records: **"+format(r["archive_draws"],",")+"**.",
        "Exploratory discovery: "+format(r["discovery_draws"],",")+" draws;",
        "later chronological evaluation: "+format(r["chronological_validation_draws"],",")+" draws.",
        "Period under validation: "+str(r["validation_period"]),
        "",
        "## Are there unusual patterns?",
        "",
        "| Hypothesis | Tests | Discovery findings after correction | Validation findings after correction |",
        "| --- | ---: | ---: | ---: |",
        "| Unusual individual frequencies | 80 | "+
          str(r["frequency_test"]["discovery_significant"])+" | "+
          str(r["frequency_test"]["validation_significant"])+" |",
        "| Within-draw number pairs | 3,160 | "+
          str(r["cooccurrence_test"]["discovery_bonferroni_significant"])+" | "+
          str(r["cooccurrence_test"]["selected_20_validation_bonferroni_significant"])+" of 20 flagged pairs |",
        "| Consecutive-draw number overlap | 6 lag distances | "+
          str(r["serial_overlap_discovery"]["significant"])+" | "+
          str(r["serial_overlap_validation"]["significant"])+" |",
        "| Individual reappearance next draw | 80 | "+
          str(r["number_transition_test"]["discovery_significant"])+" | "+
          str(r["number_transition_test"]["validation_significant"])+" |",
        "| Time-of-day number bias | 320 | "+
          str(r["time_of_day_discovery"]["significant"])+" | "+
          str(r["time_of_day_validation"]["significant"])+" |",
        "",
        "All family-wise corrections use Bonferroni at 5%. Pair-validation",
        "correction is across the 20 previously flagged pairs.",
        "These are approximate tests; same-draw number dependence",
        "and overlapping serial comparisons make caution important.",
        "",
        "## Can any signal improve ONE five-number ticket per drawing?",
        "",
        "| Method | Tickets | Average matching balls | Perfect 5/5 | Gross/$1 | Net hypothetical $ | Adjusted hit-count p |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name,v in p.items():
        lines.append("| "+name+" | "+format(v["draws"],",")+" | "+
                     format(v["average_matches"],".4f")+" | "+
                     str(v["perfect_five_hits"])+" | "+
                     format(v["gross_per_dollar"],".4f")+" | "+
                     format(v["net_dollars"],"+,")+" | "+
                     format(v["hits_p_bonferroni_5"],".4g")+" |")
    lines.extend([
        "",
        "Mathematical null: 1.25 matches per five-number ticket,",
        "approximately 0.7 dollars gross returned per dollar wagered.",
        "Each method makes exactly one ticket per actual future historical draw.",
        "Discovery-period statistics are frozen before validation.",
        "The original VAL ensemble's first ticket is also evaluated.",
        "",
        "## Probability calibration",
        "",
        "For static frequency, prior-draw repetition and cross-draw",
        "transition-matrix methods, lower Brier score is better.",
        "A fair uniform model scores 0.1875 per draw.",
        "",
        "| Method | Brier advantage vs fair | Approximate 95% interval |",
        "| --- | ---: | ---: |"
    ])
    for name in ("frequency","lag_repeat","transition"):
        x=p[name]
        ci=x["brier_advantage_95pct_interval"]
        lines.append("| "+name+" | "+format(x["mean_brier_advantage_over_fair"],"+.8f")+
                     " | ["+format(ci[0],"+.8f")+", "+format(ci[1],"+.8f")+"] |")
    lines.extend([
        "",
        "## Interpretation",
        "",
        "A corrected anomaly by itself does not establish prediction:",
        "we require consistent direction in the later time period and",
        "out-of-sample win-rate/probability improvement.",
        "The validation period is historical, and earlier VAL research",
        "already inspected this archive. We cannot call it untouched.",
        "No live picks were modified. No money was wagered.",
        "Archive gaps are explicitly omitted from cross-draw lag tests.",
        "",
        "Full numbered anomalies and per-model diagnostics:",
        "[research_keno_dependencies.json](research_keno_dependencies.json).",
        ""
    ])
    return "\n".join(lines)


def main():
    rows=read_archive()
    result=analyze(rows)
    result["generated_utc"]=datetime.now(timezone.utc).isoformat()
    DEST_JSON.write_text(json.dumps(result,indent=2)+"\n")
    DEST_MD.write_text(md_report(result)+"\n")
    print(json.dumps({
        "archive_draws":result["archive_draws"],
        "validation_draws":result["chronological_validation_draws"],
        "significant_counts":{
            "frequency":result["frequency_test"]["validation_significant"],
            "pair_validation":result["cooccurrence_test"]["selected_20_validation_bonferroni_significant"],
            "serial_overlap":result["serial_overlap_validation"]["significant"],
            "transitions":result["number_transition_test"]["validation_significant"],
            "time":result["time_of_day_validation"]["significant"],
        },
        "one_ticket_methods":{
            name:{"avg_matches":p["average_matches"],
                  "gross_per_dollar":p["gross_per_dollar"],
                  "hits_p_corrected":p["hits_p_bonferroni_5"]}
            for name,p in result["out_of_sample_one_ticket"]["prediction_models"].items()
        }
    },indent=2),flush=True)


if __name__=="__main__":main()
