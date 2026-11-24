"use strict";
function evaluate(rows){
  const games=["pick3","pick4","pick5"],by=new Map();
  for(const row of rows){
    const k=row.date+"|"+row.session+"|"+row.game;
    if(by.has(k)&&by.get(k).join("")!==row.numbers.join(""))throw Error("Conflicting results");
    if(!games.includes(row.game)||!["Day","Night"].includes(row.session)||row.numbers.length!==Number(row.game.at(-1))||row.numbers.some(x=>!Number.isInteger(x)||x<0||x>9))throw Error("Bad input");
    by.set(k,row.numbers);
  }
  const dates=[...new Set(rows.map(r=>r.date))].sort();
  const methods=["fair","cross_repeat","cross_avoid","same_game_repeat","same_game_avoid"];
  const init=()=>({draws:0,hits:0,log_gain_sum:0,source_overlap_count:0,expected_overlap_count:0});
  const out=Object.fromEntries(games.map(g=>[g,Object.fromEntries(methods.map(m=>[m,init()]))]));
  function prev(date,session){
    if(session==="Night")return date+"|Day|";
    return new Date(Date.parse(date+"T00:00:00Z")-86400000).toISOString().slice(0,10)+"|Night|";
  }
  function key(a){return [...a].sort((a,b)=>a-b).join("");}
  function tie(date,session,game,d){let s=2166136261;for(const c of date+session+game+d)s=Math.imul(s^c.charCodeAt(0),16777619);s^=s>>>16;s=Math.imul(s,0x7feb352d);s^=s>>>15;s=Math.imul(s,0x846ca68b);return (s^(s>>>16))>>>0;}
  for(const date of dates)for(const session of ["Day","Night"])for(const game of games){
    const actual=by.get(date+"|"+session+"|"+game);
    const prefix=prev(date,session),same=by.get(prefix+game),others=games.filter(g=>g!==game).map(g=>by.get(prefix+g));
    if(!actual||!same||others.some(x=>!x))continue;
    const cross=others.flat(),w=actual.length;
    for(const m of methods){
      const source=m.startsWith("same")?same:cross;
      const freq=Array.from({length:10},(_,d)=>source.filter(x=>x===d).length/source.length);
      // 10% shrink toward or away from source frequencies. This is fixed,
      // does not learn on target outcomes, and guarantees positive probabilities.
      const alpha=m==="fair"?0:m.endsWith("repeat")?.1:-.1;
      const p=freq.map(f=>.1+alpha*(f-.1));
      if(Math.min(...p)<=0||Math.abs(p.reduce((a,b)=>a+b,0)-1)>1e-12)throw Error("Bad distribution");
      const pick=Array.from({length:10},(_,i)=>i).sort((a,b)=>p[b]-p[a]||tie(date,session,game,a)-tie(date,session,game,b)).slice(0,w);
      const x=out[game][m];x.draws++;x.hits+=Number(key(pick)===key(actual));
      // For iid digits, the unordered multiplicity cancels in model/fair log ratio.
      x.log_gain_sum+=actual.reduce((s,d)=>s+Math.log(p[d]/.1),0);
      const unique=new Set(source);x.source_overlap_count+=actual.filter(d=>unique.has(d)).length;
      x.expected_overlap_count+=w*unique.size/10;
    }
  }
  for(const [g,metrics] of Object.entries(out))for(const x of Object.values(metrics)){
    const w=Number(g.at(-1));let fac=1;for(let i=2;i<=w;i++)fac*=i;
    x.expected_fair_any_order_hits=x.draws*fac/10**w;
    x.mean_box_log_gain=x.draws?x.log_gain_sum/x.draws:null;
    x.actual_source_overlap_rate=x.draws?x.source_overlap_count/(x.draws*w):null;
    x.expected_source_overlap_rate=x.draws?x.expected_overlap_count/(x.draws*w):null;
  }
  return {version:"cross_game_previous_session_v1",notes:"Retrospective exploratory test. Each method makes one distinct-digit selection per target. All have identical fair Any Order coverage. Only prior session used, never contemporaneous or later outcomes. Fixed 10% tilt and stable date/game/session tie break. Positive log gain and excess hits require independent replication. Same-game methods are comparators; not a new claim of historical discovery.",dates:dates.length,first:dates[0],last:dates.at(-1),games:out};
}
if(require.main===module){const fs=require("node:fs");let rows=JSON.parse(fs.readFileSync(process.argv[2]||"research/cross_game_official_sample.json","utf8"));console.log(JSON.stringify(evaluate(rows),null,2));}
module.exports={evaluate};
