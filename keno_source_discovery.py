"""Keno public-source diagnostics: find pagination/results API without guessing.

Records machine-readable source evidence for later expansion; makes no bets
and runs no unvalidated predictive evaluations.
"""
from __future__ import annotations

import json
import re
import urllib.request
from html.parser import HTMLParser
from datetime import datetime,timezone
from pathlib import Path

PAGES=[
  "https://www.comparethelotto.com/us/results-virginia-keno",
  "https://www.theroanokestar.com/arts-events-etc/most-common-keno-numbers/",
  "https://www.valottery.com/data/draw-games/keno",
]
class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[];self.scripts=[]
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if tag=="a" and d.get("href"):
            self.links.append({"href":d["href"],"text":""})
        if tag=="script" and d.get("src"): self.scripts.append(d["src"])
    def handle_data(self,t):
        if self.links and len(self.links[-1]["text"])<100:
            self.links[-1]["text"]+=t.strip()[:120]

def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; VAL-research/1.0)"})
    with urllib.request.urlopen(req,timeout=30) as resp:
        b=resp.read(2_500_000)
        return b.decode("utf-8-sig","replace"),resp.status,resp.geturl()

def run():
    results={"generated_utc":datetime.now(timezone.utc).isoformat(),"pages":{}}
    for url in PAGES:
        d={"url":url}
        try:
            body,status,final=fetch(url)
            p=Links();p.feed(body)
            d["http"]=status;d["final_url"]=final;d["bytes"]=len(body)
            d["older_links"]=[l for l in p.links if "older" in l["text"].lower() or "older" in l["href"].lower()]
            d["keno_links"]=[l for l in p.links if any(a in l["href"].lower() for a in ("keno","download","past","history"))][:50]
            d["scripts_of_interest"]=[s for s in p.scripts if any(a in s.lower() for a in ("keno","game","draw","result","bundle","app"))][:60]
            d["scripts_total"]=len(p.scripts)
            d["page_api_strings"]=sorted(set(
                re.findall(r"(?:https?://[^\s\"'<>]{1,130}|/[a-zA-Z0-9/_-]{4,120})",body)
            ))
            d["page_api_strings"]=[x for x in d["page_api_strings"] if any(t in x.lower() for t in ("api","keno","history","result","draw"))][:90]
            d["mentions_html"]=[{"term":term,"excerpt":body[max(0,(i:=body.lower().find(term))-120):i+260]}
                                  for term in ("pastnumbers","drawnumber","keno","getpast","api/v1")
                                  if term in body.lower()]
        except Exception as exc:
            d["error"]=str(exc)
        results["pages"][url]=d
    dest=Path("reports/keno_source_discovery.json")
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(json.dumps(results,indent=2)+"\n")
    print(json.dumps(results)[:18000],flush=True)
if __name__=="__main__":run()
