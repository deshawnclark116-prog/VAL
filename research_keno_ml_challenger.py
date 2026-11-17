"""Research-grade VA Keno challenger: leak-safe supervised learning vs fair null.

The question is NOT whether high-capacity AI can find patterns in the
same history; it is whether those patterns predict later draws.

Four chronologically separated roles:
 - all earlier 60%: model fitting
 - next 20%: ONE-TIME model family / shrinkage selection on Brier
 - final 20%: frozen evaluation, without refitting after selection
 - independent future drawings: needed before any real-world promotion.

Each input row is one candidate ball among the 80 for a future draw.
Includes multi-scale frequency, lag signatures, recency and calendar
conditions, and regularized linear and nonlinear predictive architectures.
Scores calibrated per-ball Brier/log-loss and one-ball hit probability.
No future draw numbers are used as target features. No live predictions
or betting automation changes. Historical archive was previously examined.
"""
from __future__ import annotations

import gzip
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from research_keno import stable_rng

ARCHIVE=Path("reports/keno_official_history.json.gz")
JSON_OUT=Path("reports/research_keno_ml_challenger.json")
MD_OUT=Path("reports/research_keno_ml_challenger.md")
SEED=20261117
WINDOWS=(10,50,250,1000,3000)
LAGS=(1,2,3,5,10,20)
ALPHAS=(0.0,0.25,0.5,0.75,1.0)
FEATURE_NAMES=(
    "p_last_10","p_last_50","p_last_250","p_last_1000","p_last_3000",
    "p_all_previous",
    "present_lag_1","present_lag_2","present_lag_3",
    "present_lag_5","present_lag_10","present_lag_20",
    "draws_since_number_last_seen",
    "number_scaled",
    "draw_time_sin","draw_time_cos",
    "weekday_sin","weekday_cos",
    "draw_id_mod_2","draw_id_mod_8",
)
M=len(FEATURE_NAMES)


def load_archive(path=ARCHIVE):
    with gzip.open(path,"rt",encoding="utf-8") as f:
        rows=json.load(f)
    ids=[r["draw_id"] for r in rows]
    if len(rows)<6000 or ids!=sorted(set(ids)):
        raise ValueError("Need unique, chronological, adequately sized official archive")
    for r in rows:
        nums=r["numbers"]
        if len(nums)!=20 or len(set(nums))!=20 or any(type(x)!=int or x<1 or x>80 for x in nums):
            raise ValueError("Invalid official 20-ball result")
    return rows


def build_dataset(rows):
    """X for drawing i depends only on draws [0, i), plus scheduled time."""
    n=len(rows)
    y=np.zeros((n,80),dtype=np.uint8)
    draw_ids=np.array([r["draw_id"] for r in rows],dtype=np.int64)
    for i,r in enumerate(rows):
        y[i,np.asarray(r["numbers"])-1]=1
    cumulative=np.concatenate([
        np.zeros((1,80),dtype=np.int32),
        np.cumsum(y.astype(np.int32),axis=0)
    ],axis=0)
    x=np.empty((n,80,M),dtype=np.float32)
    seen=np.full(80,-1,dtype=np.int32)
    num_scaled=(np.arange(1,81,dtype=np.float32)-40.5)/40.0
    for i,r in enumerate(rows):
        for idx,w in enumerate(WINDOWS):
            j=max(0,i-w)
            denom=max(1,i-j)
            x[i,:,idx]=(cumulative[i]-cumulative[j])/denom
        x[i,:,5]=cumulative[i]/max(1,i)
        for idx,lag in enumerate(LAGS):
            if i>=lag and draw_ids[i]-draw_ids[i-lag]==lag:
                x[i,:,6+idx]=y[i-lag]
            else:
                x[i,:,6+idx]=0.0
        # This is completed BEFORE recording the current draw.
        x[i,:,12]=np.minimum(i-seen,200)/200.0
        x[i,:,13]=num_scaled
        stamp=datetime.fromisoformat(r["timestamp"])
        hh=stamp.hour+stamp.minute/60+stamp.second/3600
        x[i,:,14]=math.sin(2*math.pi*hh/24)
        x[i,:,15]=math.cos(2*math.pi*hh/24)
        x[i,:,16]=math.sin(2*math.pi*stamp.weekday()/7)
        x[i,:,17]=math.cos(2*math.pi*stamp.weekday()/7)
        x[i,:,18]=draw_ids[i]%2
        x[i,:,19]=(draw_ids[i]%8)/8.0
        seen[np.flatnonzero(y[i])]=i
        if (i+1)%3000==0:
            print("Built leak-safe features through draw "+str(i+1),flush=True)
    return x,y


def normalized_prob(raw):
    """Each official draw has exactly 20 of 80 balls; enforce the sum."""
    raw=np.clip(np.asarray(raw,dtype=np.float64),1e-5,1-1e-5)
    raw=raw*(20.0/raw.sum(axis=1,keepdims=True))
    if np.any(raw>=1) or np.any(raw<=0):
        raise ValueError("Calibrated p outside bounds; invalid model")
    if not np.allclose(raw.sum(axis=1),20,atol=1e-8):
        raise AssertionError("Probabilities do not sum to 20")
    return raw


def calibrate(raw,alpha):
    return normalized_prob(.25+alpha*(raw-.25))


def brier(prob,y):
    return float(np.mean((prob-y)**2))


def logloss(prob,y):
    prob=np.clip(prob,1e-10,1-1e-10)
    return float(-np.mean(y*np.log(prob)+(1-y)*np.log1p(-prob)))


def pick_one(prob,draw_ids,name):
    picks=[]
    for i,draw_id in enumerate(draw_ids):
        # Use exactly ONE ball. Random tie-breaks, selected before outcomes.
        arr=prob[i]
        maximal=arr.max()
        eligible=np.flatnonzero(np.abs(arr-maximal)<1e-13)
        candidate=int(stable_rng(SEED,name,int(draw_id)).choice(eligible))+1
        picks.append(candidate)
    return np.asarray(picks,dtype=np.int16)


def wilson(hits,n):
    z=1.96
    p=hits/n
    denom=1+z*z/n
    mid=(p+z*z/(2*n))/denom
    delta=z*math.sqrt((p*(1-p)+z*z/(4*n))/n)/denom
    return [mid-delta,mid+delta]


def success_p(hits,n):
    z=(abs(hits-.25*n)-.5)/math.sqrt(.25*.75*n)
    return min(1.0,math.erfc(max(0,z)/math.sqrt(2)))


def day_cluster_interval(values,day_keys,n_iter=1000):
    """Resample whole calendar days to allow within-day correlations."""
    bucket={}
    for key,x in zip(day_keys,values):
        bucket.setdefault(key,[]).append(float(x))
    groups=list(bucket.values())
    g=len(groups)
    if g<3:return [None,None]
    sums=np.array([sum(group) for group in groups])
    sizes=np.array([len(group) for group in groups])
    rng=np.random.default_rng(SEED)
    idx=rng.integers(0,g,size=(n_iter,g))
    means=sums[idx].sum(axis=1)/sizes[idx].sum(axis=1)
    return [float(x) for x in np.quantile(means,[.025,.975])]


def score(name,p,y,rows,draw_ids):
    p=normalized_prob(p)
    n=len(rows)
    correct_perball=(y==1)
    chosen=pick_one(p,draw_ids,name)
    hit=np.array([int(y[k,ball-1]) for k,ball in enumerate(chosen)])
    successes=int(hit.sum())
    # For each ticket, score all 80 probabilities + the chosen ball.
    brier_by_draw=((p-y)**2).mean(axis=1)
    delta_brier=.1875-brier_by_draw
    dates=[row["date"] for row in rows]
    half=n//2
    return {
        "draws":n,
        "one_ball_hit_count":successes,
        "one_ball_hit_rate":successes/n,
        "fair_expected_hit_rate":.25,
        "wilson_95":wilson(successes,n),
        "day_cluster_bootstrap_hit_rate_95":day_cluster_interval(hit,dates),
        "p_vs_25pct":success_p(successes,n),
        "average_brier":brier(p,y),
        "brier_advantage_vs_fair":float(delta_brier.mean()),
        "day_cluster_bootstrap_brier_advantage_95":
            day_cluster_interval(delta_brier,dates),
        "log_loss":logloss(p,y),
        "sum_to_20_probability_invariant":bool(np.allclose(p.sum(axis=1),20)),
        "first_half_rate":float(hit[:half].mean()),
        "second_half_rate":float(hit[half:].mean()),
        "first_five_audit":[dict(draw_id=int(draw_ids[i]),predicted_ball=int(chosen[i]),
                                 hit=bool(hit[i])) for i in range(min(5,n))]
    }


def fit_models(xtrain,ytrain):
    xx=xtrain.reshape((-1,M))
    yy=ytrain.reshape(-1)
    print("Training regularized linear model on "+str(len(yy))+" candidate-ball observations",flush=True)
    linear=make_pipeline(
        StandardScaler(),
        LogisticRegression(C=.025,solver="lbfgs",max_iter=220,tol=1e-5))
    linear.fit(xx,yy)
    print("Training gradient-boosted nonlinear model",flush=True)
    boosted=HistGradientBoostingClassifier(
        loss="log_loss",learning_rate=.055,max_iter=125,
        max_leaf_nodes=15,max_depth=4,min_samples_leaf=900,
        l2_regularization=35,random_state=42,
        early_stopping=False)
    boosted.fit(xx,yy)
    return {"regularized_linear":linear,"nonlinear_boosted":boosted}


def forecast_models(models,x,static_frequency):
    n=x.shape[0]
    xx=x.reshape(-1,M)
    outputs={}
    for name,model in models.items():
        prob=model.predict_proba(xx)[:,1].reshape((n,80))
        outputs[name]=normalized_prob(prob)
    outputs["static_frequency"]=normalized_prob(
        np.broadcast_to(static_frequency,(n,80)))
    return outputs


def evaluate(rows):
    n=len(rows)
    train_end=int(.60*n)
    cal_end=int(.80*n)
    if train_end<3000 or cal_end-train_end<1000 or n-cal_end<1000:
        raise ValueError("Not enough observations in each chronological interval")
    x,y=build_dataset(rows)
    training_y=y[:train_end]
    static_frequency=(training_y.sum(axis=0)+250*.25)/(len(training_y)+250)
    model=fit_models(x[:train_end],y[:train_end])
    del training_y
    print("Selecting model and shrinkage using calibration period ONLY",flush=True)
    cal_outputs=forecast_models(model,x[train_end:cal_end],static_frequency)
    cal_y=y[train_end:cal_end]
    trials=[]
    best={"name":"uniform_null","alpha":0.0,"validation_brier":.1875}
    for name,raw in cal_outputs.items():
        for alpha in ALPHAS:
            prob=calibrate(raw,alpha)
            value=brier(prob,cal_y)
            trials.append(dict(name=name,alpha=alpha,validation_brier=value))
            if value<best["validation_brier"]-1e-9:
                best=dict(name=name,alpha=alpha,validation_brier=value)
    print("Pre-final selection: "+json.dumps(best),flush=True)
    # Entire final period is evaluated once, no refitting or selection here.
    final_x=x[cal_end:]
    final_y=y[cal_end:]
    final_rows=rows[cal_end:]
    final_ids=[r["draw_id"] for r in final_rows]
    final_raw=forecast_models(model,final_x,static_frequency)
    final_scores={
        "fair_uniform":score("fair_uniform",np.full((len(final_rows),80),.25),
                             final_y,final_rows,final_ids),
    }
    for name,raw in final_raw.items():
        final_scores[name+"_unshrunk"]=score(
            name+"_unshrunk",raw,final_y,final_rows,final_ids)
    if best["name"]=="uniform_null":
        selected=np.full((len(final_rows),80),.25)
    else:
        selected=calibrate(final_raw[best["name"]],best["alpha"])
    final_scores["calibration_selected_champion"]=score(
        "calibration_selected_champion",selected,final_y,final_rows,final_ids)
    # Independent one-ball random placebo controls, same final draw set.
    placebo_hits=[]
    for k in range(25):
        guesses=[stable_rng(SEED,"control",k,int(id)).randint(1,80) for id in final_ids]
        placebo_hits.append(sum(final_y[i,guess-1] for i,guess in enumerate(guesses))/len(final_rows))
    # Log only chosen models: final-period alternatives are diagnostic, not eligible for promotion.
    return {
        "version":"val_keno_ml_adversarial_v1",
        "official_draws":n,
        "train":dict(n=train_end,dates=[rows[0]["timestamp"],rows[train_end-1]["timestamp"]]),
        "calibration":dict(n=cal_end-train_end,dates=[rows[train_end]["timestamp"],rows[cal_end-1]["timestamp"]]),
        "final":dict(n=n-cal_end,dates=[rows[cal_end]["timestamp"],rows[-1]["timestamp"]]),
        "features":list(FEATURE_NAMES),
        "architectures":["regularized_linear","nonlinear_boosted","static_frequency","uniform_null"],
        "calibration_grid":trials,
        "frozen_selected_model":best,
        "final_scores":final_scores,
        "placebo_random_controls":dict(n=25,average=float(np.mean(placebo_hits)),
                minimum=float(min(placebo_hits)),maximum=float(max(placebo_hits))),
        "research_limitations":[
            "Historical archive was already inspected in earlier research, so even final chronology is not independently untouched.",
            "About one month of drawings; subtle stable biases may not be identifiable.",
            "Only observed draw outcomes are available. Internal RNG implementation and seed are unknown.",
            "Five experimental architectures / calibration comparisons should not be repurposed as guaranteed lottery predictions.",
            "No promotion unless a locked candidate later beats fair uniform on genuinely future draws."
        ]
    }


def markdown(r):
    lines=[
        "# VAL Keno — machine-learning challenger under falsification controls",
        "",
        "Frozen source: **"+format(r["official_draws"],",")+" official draws**.",
        "Training "+str(r["train"]["n"])+" draws; model/calibration selection "+
        str(r["calibration"]["n"])+" draws; **final chronological evaluation "+
        str(r["final"]["n"])+" draws**.",
        "",
        "Model features: multi-scale frequency, six lag indicators, number recency,",
        "scheduled draw-time and weekday cycles, and draw index conditions.",
        "Architectures: regularized logistic regression, gradient boosted trees,",
        "static frequency control and exact fair null.",
        "",
        "**Frozen before final test:** "+r["frozen_selected_model"]["name"]+
        " with shrinkage "+str(r["frozen_selected_model"]["alpha"])+
        " (selected using Brier score only on middle period).",
        "",
        "| Final period model | Single-ball hits | Hit rate | Brier gain vs fair | 95% day-bootstrap Brier gain |",
        "| --- | ---: | ---: | ---: | --- |"
    ]
    for name,v in r["final_scores"].items():
        ci=v["day_cluster_bootstrap_brier_advantage_95"]
        lines.append("| "+name+" | "+str(v["one_ball_hit_count"])+"/"+str(v["draws"])+
                     " | "+format(100*v["one_ball_hit_rate"],".2f")+"% | "+
                     format(v["brier_advantage_vs_fair"],"+.8f")+" | ["+
                     format(ci[0],"+.8f")+", "+format(ci[1],"+.8f")+"] |")
    x=r["placebo_random_controls"]
    lines+=["",
        str(x["n"])+" independent random ticket controls, one ball per draw:",
        "mean "+format(100*x["average"],".2f")+"%, range "+
        format(100*x["minimum"],".2f")+"% to "+
        format(100*x["maximum"],".2f")+"%.",
        "",
        "The 25% chance baseline is the expected hit rate under fair selection.",
        "Brier score assesses ALL 80 probabilities per drawing and cannot",
        "be rescued by occasional unusually lucky five-number jackpots.",
        "Day-level bootstrap accounts for within-day related outcomes.",
        "We never choose a final-period winner after seeing final results.",
        "",
        "**Caution:** all these draws are historical and had previously been",
        "examined in other experiments. This is a stronger chronological",
        "falsification study, not a genuinely unseen prospective test.",
        "A physically perfect generator and an exploitable one may be hard",
        "to distinguish with only a month of outputs.",
        "",
        "No live VAL change, real gambling, or claims of guaranteed winnings.",
        "Full audit: [research_keno_ml_challenger.json](research_keno_ml_challenger.json).",
        ""
    ]
    return "\n".join(lines)


def main():
    rows=load_archive()
    result=evaluate(rows)
    result["generated_utc"]=datetime.now(timezone.utc).isoformat()
    JSON_OUT.write_text(json.dumps(result,indent=2)+"\n")
    MD_OUT.write_text(markdown(result)+"\n")
    print(json.dumps({
        "frozen_selected_model":result["frozen_selected_model"],
        "final_draws":result["final"]["n"],
        "results":{k:{"one_ball_hit_rate":v["one_ball_hit_rate"],
                      "brier_advantage":v["brier_advantage_vs_fair"]}
                   for k,v in result["final_scores"].items()}
    },indent=2),flush=True)


if __name__=="__main__":main()
