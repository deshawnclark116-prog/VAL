"""Official VA Keno long-history five-spot research; read-only paper backtest.

Uses /api/v1/drawnumbers gameId 30. Keeps live VAL untouched.
"""
import argparse,gzip,hashlib,json,math,time,urllib.parse,urllib.request
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
from val import METHODS,sample_weights
from research_keno import PRIZE_FIVE_SPOT,exact_fair_match_probabilities,match_count,stable_rng

API="https://www.valottery.com/api/v1/drawnumbers"
WARMUP=500
N_PICKS=3


def api_page(page,size):
    data=urllib.parse.urlencode(dict(gameId=30,page=page,pageSize=size)).encode()
    req=urllib.request.Request(API,data=data,method="POST",headers={
      "User-Agent":"Mozilla/5.0","Content-Type":"application/x-www-form-urlencoded",
      "Referer":"https://www.valottery.com/data/draw-games/keno","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=90) as resp:raw=resp.read(8000000)
    val=json.loads(raw)
    if val.get("errors") or not isinstance(val.get("data"),list):raise ValueError("Invalid official response")
    return val,hashlib.sha256(raw).hexdigest()


def normalize(item):
    if item["DrawGameId"]!=30:raise ValueError("Non-Keno game")
    records=item["DailyDraws"]
    if len(records)!=1:raise ValueError("Unexpected daily draw")
    nums=records[0]["SelectedNumbers"]["Value"]
    if len(nums)!=20 or len(set(nums))!=20 or any(type(x)!=int or not 1<=x<=80 for x in nums):
        raise ValueError("Invalid official Keno result")
    bonus=records[0].get("InlineBonusValue")
    if bonus is not None and bonus not in nums:raise ValueError("Bad BULLS-EYE value")
    return dict(draw_id=item["DrawNumber"],date=item["DrawDate"][:10],
                timestamp=item["DrawDate"],numbers=sorted(nums),bullseye=bonus)


def load_archive(size=350,max_pages=70):
    first,h=api_page(1,size)
    total=int(first["totalPages"])
    if total>max_pages:raise ValueError("Official page count exceeded limit")
    seen={};hashes=[]
    for p in range(1,total+1):
        data,ph=(first,h) if p==1 else api_page(p,size)
        if data["currentPage"]!=p or data["totalPages"]!=total:
            raise ValueError("Official Keno pagination drift")
        for raw in data["data"]:
            row=normalize(raw)
            if row["draw_id"] in seen and seen[row["draw_id"]]!=row:
                raise ValueError("Official Keno conflicting draw IDs")
            seen[row["draw_id"]]=row
        hashes.append(ph)
        if p%5==0 or p==total:
            print(json.dumps(dict(pages=p,total=total,draws=len(seen))),flush=True)
        if p<total:time.sleep(.2)
    rows=sorted(seen.values(),key=lambda r:r["draw_id"])
    if len(rows)<2000:raise ValueError("Official archive unexpectedly short")
    if any(a["timestamp"]>b["timestamp"] for a,b in zip(rows,rows[1:])):
        raise ValueError("Draw chronology invalid")
    meta=dict(draws=len(rows),first=rows[0]["timestamp"],last=rows[-1]["timestamp"],
              missing_ids=sum(max(0,b["draw_id"]-a["draw_id"]-1) for a,b in zip(rows,rows[1:])),
              pages=total,page_sha256=hashes)
    return rows,meta


class Counters:
    def __init__(self,rows,i):
        self.total=Counter();self.recent=Counter()
        for r in rows[max(0,i-500):i]:self.total.update(r["numbers"])
        for r in rows[max(0,i-50):i]:self.recent.update(r["numbers"])
    def step(self,rows,i):
        self.total.update(rows[i]["numbers"])
        if i>=500:self.total.subtract(rows[i-500]["numbers"])
        self.recent.update(rows[i]["numbers"])
        if i>=50:self.recent.subtract(rows[i-50]["numbers"])
    def weights(self,method):
        if method=="random":return [1.0]*80
        hot=[self.total[d]+2 for d in range(1,81)]
        recent=[self.recent[d]+2 for d in range(1,81)]
        cold=[1/math.sqrt(x) for x in hot]
        if method=="frequency":return hot
        if method=="recent":return recent
        if method=="cold":return cold
        if method=="ensemble":
            sh,sr,sc=sum(hot),sum(recent),sum(cold)
            return [.4*a/sh+.4*b/sr+.2*c/sc for a,b,c in zip(hot,recent,cold)]
        raise ValueError(method)


def predict(weights,rng):
    found=set();picks=[]
    for _ in range(3000):
        if len(picks)==N_PICKS:break
        number=tuple(sorted(sample_weights(range(1,81),weights,5,rng)))
        if number not in found:found.add(number);picks.append(list(number))
    if len(picks)!=N_PICKS:raise ValueError("Unique picks exhausted")
    return picks


def backtest(rows):
    method_names=("control",)+METHODS
    out={name:dict(dist=Counter(),gross=0,days=defaultdict(lambda: [0,0]),
                   halves=[Counter(),Counter()]) for name in method_names}
    five_match=[]
    mid=WARMUP+(len(rows)-WARMUP)//2
    counter=Counters(rows,WARMUP)
    for i in range(WARMUP,len(rows)):
        draw=rows[i]
        for name in method_names:
            method="random" if name=="control" else name
            picks=predict(counter.weights(method),stable_rng(20261117,name,draw["draw_id"]))
            stats=out[name]
            for ticket in picks:
                n=match_count(ticket,draw["numbers"])
                prize=PRIZE_FIVE_SPOT[n]
                stats["dist"][n]+=1;stats["gross"]+=prize
                stats["days"][draw["date"]][0]+=1;stats["days"][draw["date"]][1]+=prize
                half=stats["halves"][int(i>=mid)]
                half["n"]+=1;half["gross"]+=prize;half["five"]+=n==5
                if n==5:
                    five_match.append(dict(method=name,draw_id=draw["draw_id"],
                                           date=draw["date"],ticket=ticket,
                                           actual=draw["numbers"]))
        counter.step(rows,i)
        if (i-WARMUP+1)%2000==0:
            print("Scored "+str(i-WARMUP+1)+" official drawings",flush=True)
    result={}
    for name,s in out.items():
        n=sum(s["dist"].values())
        result[name]=dict(tickets=n,distribution={str(k):s["dist"][k] for k in range(6)},
            avg_matches=round(sum(k*v for k,v in s["dist"].items())/n,6),
            three_plus=sum(s["dist"][i] for i in (3,4,5)),
            four_plus=s["dist"][4]+s["dist"][5],five=s["dist"][5],
            gross=s["gross"],net=s["gross"]-n,roi=round(s["gross"]/n,6),
            early=dict(s["halves"][0]),late=dict(s["halves"][1]),
            by_day=dict(s["days"]))
    return dict(warmup=WARMUP,draws=len(rows)-WARMUP,picks_per_draw=N_PICKS,
                fair_avg_matches=1.25,
                fair_roi=round(sum(PRIZE_FIVE_SPOT[k]*p for k,p in exact_fair_match_probabilities().items()),6),
                methods=result,five_of_five_records=five_match)


def report(meta,test):
    lines=["# VAL official Keno expanded historical test","",
           f"Official Keno drawings downloaded: **{meta['draws']:,}**.",
           f"Range: {meta['first']} to {meta['last']}.",
           f"Number gaps in official source: {meta['missing_ids']}.","",
           f"Strictly chronological paper backtest: **{test['draws']:,}** real",
           f"drawings, three five-number tickets per method per draw.",
           "First 500 used only for warmup. Independent random control.","",
           "Official Director's Order No. 134 (2026), Section H, page 8:",
           "five-spot $1 prizes: 3 hits $2, 4 hits $20, 5 hits $450.",
           "**Zero, one, or two hits pay $0.** The current marketing website",
           "incorrectly lists a zero-match five-spot prize.","",
           "| Method | Tickets | 3+ hits | 4+ hits | 5/5 | Avg matches | Return/$1 | Net $ |",
           "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for m,r in test["methods"].items():
        lines.append(f"| {m} | {r['tickets']:,} | {r['three_plus']:,} | "
                     f"{r['four_plus']:,} | {r['five']} | {r['avg_matches']:.4f} | "
                     f"{r['roi']:.4f} | {r['net']:+,} |")
    lines+=["","## Early vs late historical periods","",
            "| Method | Early return per $ | Later return per $ | Early 5/5 | Later 5/5 |",
            "| --- | ---: | ---: | ---: | ---: |"]
    for m,r in test["methods"].items():
        a,b=r["early"],r["late"]
        lines.append(f"| {m} | {a['gross']/a['n']:.4f} | {b['gross']/b['n']:.4f} | "
                     f"{a['five']} | {b['five']} |")
    lines+=["",f"Fair random expected payout: {test['fair_roi']:.4f} per $1.",
            "All tickets and prizes are hypothetical. No money wagered.",
            "Multiple-method selection and rare big prizes prevent declaring",
            "a genuine predictive edge on this history alone. No promotion",
            "of any historical winner until a separately frozen future test.",
            "",
            "Raw official result sample: [keno_official_history.json.gz](keno_official_history.json.gz).",
            "Detailed audit [research_keno_official.json](research_keno_official.json).",""]
    return "\n".join(lines)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--page-size",type=int,default=350)
    a=p.parse_args()
    rows,meta=load_archive(a.page_size)
    Path("reports").mkdir(exist_ok=True)
    with open("reports/keno_official_history.json.gz","wb") as f:
        with gzip.GzipFile(fileobj=f,filename="",mode="wb",mtime=0) as g:
            g.write(json.dumps(rows,separators=(",",":")).encode())
    res=backtest(rows)
    result=dict(created_at=datetime.now(timezone.utc).isoformat(),
                version="val_keno_official_v1",
                source=API,coverage=meta,results=res)
    Path("reports/research_keno_official.json").write_text(json.dumps(result,indent=2)+"\n")
    Path("reports/research_keno_official.md").write_text(report(meta,res)+"\n")
    print(json.dumps(dict(draws=res["draws"],results={
        m:dict(roi=r["roi"],five=r["five"],avg_matches=r["avg_matches"])
        for m,r in res["methods"].items()}),indent=2),flush=True)

if __name__=="__main__":main()
