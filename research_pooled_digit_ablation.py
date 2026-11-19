"""Ablation of genuinely different pooled DIGIT PROBABILITY formulas.

Tests whether the observed recent Pick-3/Pick-5 pooled top-digit improvement
is explained by using the right Day/Night stream, by recent-vs-long weighting,
or by post-hoc luck. The model registry, smoothing and comparison dates are
fixed in source. Only earlier draws enter forecasts.

Selected after inspecting v3: NO clean confirmatory claims. The one-pick
prospective paper trial is the actual independent verification.
"""
from __future__ import annotations
import json
import math
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path

from research_10k import load_official_history
from research_pooled_digit_followup import probabilities
from val import ET,GAMES

VERSION="val_pooled_digit_ablation_v1"
GAMES_TEST=("pick3","pick4","pick5")
MODELS=("global_5000","stream_5000","recent_500","hier_stream","multiscale")
JSON_OUT=Path("reports/research_pooled_digit_ablation.json")
MD_OUT=Path("reports/research_pooled_digit_ablation.md")

def _normalize(xs):
    s=sum(xs)
    out=[v/s for v in xs]
    assert abs(sum(out)-1)<1e-10
    return out

def formulas(game,global_counts,by_stream,recent_global,recent_stream,stream):
    """Use learned counts, never the target result."""
    width=GAMES[game]["size"]
    global_p=probabilities(global_counts,width)
    stream_p=probabilities(by_stream[stream],width)
    recent_p=probabilities(recent_global,width)
    # Global learned historical distribution as a smooth hierarchical prior.
    stream_count=sum(by_stream[stream])
    hierarchical=_normalize([
        (by_stream[stream][d]+1200*global_p[d])/(stream_count+1200)
        for d in range(10)])
    recent_stream_p=probabilities(recent_stream[stream],width)
    return {
        "global_5000":global_p,
        "stream_5000":stream_p,
        "recent_500":recent_p,
        "hier_stream":hierarchical,
        "multiscale":_normalize([
            .35*global_p[d]+.35*stream_p[d]+.20*recent_p[d]+
            .10*recent_stream_p[d] for d in range(10)
        ])
    }

def examine(game,history):
    width=GAMES[game]["size"]
    all_counts=[0]*10
    short_counts=[0]*10
    stream_counts={s:[0]*10 for s in ("Day","Night")}
    short_stream={s:[0]*10 for s in ("Day","Night")}
    # Include all >500 earlier draws, but evaluate same 2025/2026 calendar
    # target for both sessions, never selecting a favorable subset afterward.
    counts=defaultdict(lambda:{"draws":0,"positions":0,"top1":0,
                               "top3":0,"exact":0,"log_gain":0.})
    for i,row in enumerate(history):
        if i>=500:
            candidates=formulas(game,all_counts,stream_counts,
                                short_counts,short_stream,row["stream"])
            local=datetime.fromisoformat(row["at"]).astimezone(ET)
            period=f"{local.year}_{row['stream']}"
            for name,p in candidates.items():
                top=sorted(range(10),key=lambda d:(-p[d],d))
                true=row["numbers"]
                h1=sum(d==top[0] for d in true)
                h3=sum(d in top[:3] for d in true)
                ex=int(all(d==top[0] for d in true))
                ll=sum(math.log(10*p[d]) for d in true)
                for k in ("all",period):
                    a=counts[game,name,k]
                    a["draws"]+=1
                    a["positions"]+=width
                    a["top1"]+=h1
                    a["top3"]+=h3
                    a["exact"]+=ex
                    a["log_gain"]+=ll
        for d in row["numbers"]:
            all_counts[d]+=1
            short_counts[d]+=1
            stream_counts[row["stream"]][d]+=1
            short_stream[row["stream"]][d]+=1
        if i>=5000:
            for d in history[i-5000]["numbers"]:
                all_counts[d]-=1
                stream_counts[history[i-5000]["stream"]][d]-=1
        if i>=500:
            for d in history[i-500]["numbers"]:
                short_counts[d]-=1
                short_stream[history[i-500]["stream"]][d]-=1
    results={}
    for (game,name,period),c in counts.items():
        results.setdefault(name,{})[period]={
            "draws":c["draws"],
            "position_hits":c["top1"],
            "position_hit_rate":c["top1"]/c["positions"],
            "top3_coverage":c["top3"]/c["positions"],
            "full_straight_winners":c["exact"],
            "mean_log_gain_vs_fair":c["log_gain"]/c["draws"]
        }
    return dict(game=game,history_draws=len(history),models=results,
                experimental=True)

def render(data):
    lines=[
        "# VAL: pooled-digit forecast ablation, by Day/Night",
        "",
        "The prior accuracy lead was identified after looking at 2026.",
        "**All comparisons here remain retrospective and exploratory.**",
        "Four additional pooled-digit formula architectures are compared",
        "with the original 5,000-draw pooled model.",
        "",
        "The reported *top-1* hit rate checks one selected digit at each",
        "position, where 10% is fair expectation. The 30% top-3",
        "benchmark is also shown. Neither is the rate of winning",
        "complete ordered tickets.",
        "",
        "| Game | Session/year | Formula | Draws | Top-digit accuracy | Top-3 coverage | Proper log gain |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: |"
    ]
    for game,info in data["games"].items():
        for period in ("2024_Day","2024_Night","2025_Day","2025_Night",
                       "2026_Day","2026_Night"):
            for name in MODELS:
                x=info["models"].get(name,{}).get(period)
                if x is None:continue
                lines.append("| "+game+" | "+period+" | "+name+" | "+
                             str(x["draws"])+" | "+
                             f'{100*x["position_hit_rate"]:.2f}%'+
                             " | "+f'{100*x["top3_coverage"]:.2f}%'+
                             " | "+f'{x["mean_log_gain_vs_fair"]:+.6f}'+" |")
    lines+=["","## Research constraint","",
            "No new contender can be called a winning system based on",
            "this historical selection. A truly new pre-draw",
            "paper prediction study is required before any promotion.",
            "[Machine-readable results](research_pooled_digit_ablation.json).",""]
    return "\n".join(lines)

def main():
    data={"version":VERSION,"created_utc":datetime.now(timezone.utc).isoformat(),
          "methods":MODELS,"historical_exploratory":True,"games":{}}
    for game in GAMES_TEST:
        x=examine(game,load_official_history(game))
        data["games"][game]=x
        for period in ("2025_Day","2025_Night","2026_Day","2026_Night"):
            ranked=sorted(((m,v[period]) for m,v in x["models"].items()
                           if period in v),
                          key=lambda z:z[1]["mean_log_gain_vs_fair"],reverse=True)
            print(game,period,[(m,round(v["position_hit_rate"],4),
                                     round(v["mean_log_gain_vs_fair"],5))
                               for m,v in ranked],flush=True)
    JSON_OUT.parent.mkdir(parents=True,exist_ok=True)
    JSON_OUT.write_text(json.dumps(data,indent=2)+"\n")
    MD_OUT.write_text(render(data)+"\n")

if __name__=="__main__":main()
