"use strict";
function benchmark(rows,seeds=2000){
  const methods=["independent_chambers","extra_mixing","distinct_ball_pool"];
  function rng(seed){let state=seed>>>0;return ()=>{state=(state+0x6D2B79F5)>>>0;let t=state;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return (t^(t>>>14))>>>0;};}
  function index(n,r){let x;const limit=Math.floor(0x100000000/n)*n;do{x=r()}while(x>=limit);return x%n;}
  function shuffle(a,r){for(let i=a.length-1;i>0;i--){let k=index(i+1,r);[a[i],a[k]]=[a[k],a[i]];}return a;}
  function pick(width,method,r){const fresh=()=>[0,1,2,3,4,5,6,7,8,9];if(method==="distinct_ball_pool")return shuffle(fresh(),r).slice(0,width);return Array.from({length:width},()=>{const a=shuffle(fresh(),r);if(method==="extra_mixing"){shuffle(a,r);shuffle(a,r);}return a[0];});}
  function key(a){return [...a].sort((a,b)=>a-b).join("");}
  function ways(a){let p=1;for(let i=2;i<=a.length;i++)p*=i;for(let d=0;d<10;d++){let c=a.filter(x=>x===d).length;for(let j=2;j<=c;j++)p/=j;}return p;}
  function fact(n){let x=1;for(let i=2;i<=n;i++)x*=i;return x;}
  const output={version:"basic_machine_comparison_v1",source:"VAL ledger official result records, retrospective, deduplicated by game and target timestamp/session",seeds,notes:"Each seed defines a separate one-selection-per-target replay, not a portfolio. No winning seed is selected. First seed fixed before execution of this comparison. Distinct pool is a different selection rule, not a replica of official digit chambers. Expected matches conditional on actual outcomes integrate all random seeds exactly. Equal mix methods have identical probabilities. All-identical full matches count for research, not Box prize eligibility.",games:{}};
  for(const width of [3,4,5]){
    const game="pick"+width,targets=rows.filter(x=>x.game===game);
    if(!targets.length)continue;
    if(targets.some(x=>x.numbers.length!==width||x.numbers.some(d=>!Number.isInteger(d)||d<0||d>9)))throw Error("Invalid actual digits");
    const actualKeys=targets.map(x=>key(x.numbers)),unique=targets.filter(x=>new Set(x.numbers).size===width).length;
    const allDistinctOdds=fact(width)/10**width;
    const possible=Array.from({length:width},(_,i)=>10-i).reduce((a,b)=>a*b,1)/fact(width);
    const expectedIndependent=targets.reduce((s,x)=>s+ways(x.numbers)/10**width,0);
    const expectedDistinct=unique/possible;
    const results={};
    for(let m=0;m<methods.length;m++){
      const method=methods[m],isDistinct=method==="distinct_ball_pool";
      let total=0,first=0,straight=0,firstStraight=0,sumFair=0;
      const sampleMatches=[];
      for(let seed=0;seed<seeds;seed++){
        const r=rng((20261123+width+Math.imul(seed,0x9e3779b9))>>>0);
        for(let i=0;i<targets.length;i++){
          const p=pick(width,method,r),hit=Number(key(p)===actualKeys[i]),exact=Number(p.join("")===targets[i].numbers.join(""));
          total+=hit;straight+=exact;sumFair+=ways(p)/10**width;
          if(seed===0){first+=hit;firstStraight+=exact;if(hit)sampleMatches.push({at:targets[i].at,stream:targets[i].stream,pick:p,actual:targets[i].numbers});}
        }
      }
      results[method]={first_seed_matches:first,first_seed_straight:firstStraight,first_seed_match_details:sampleMatches,mean_matches_per_replay:total/seeds,mean_straight_matches_per_replay:straight/seeds,exact_expected_matches_against_actual_targets:isDistinct?expectedDistinct:expectedIndependent,mean_fair_expected_matches_per_replay:sumFair/seeds,expected_matches_per_1000_fair_draws:isDistinct?1000*allDistinctOdds:1000*Array.from({length:10**width},(_,i)=>ways(String(i).padStart(width,"0").split("").map(Number))/10**width).reduce((a,b)=>a+b,0)/10**width};
    }
    if(results.independent_chambers.exact_expected_matches_against_actual_targets!==results.extra_mixing.exact_expected_matches_against_actual_targets)throw Error("Mix invariance failed");
    output.games[game]={draws:targets.length,all_distinct_actual_draws:unique,earliest:targets[0].at,latest:targets[targets.length-1].at,results};
  }
  return output;
}
if(require.main===module){const fs=require("node:fs");const rows=JSON.parse(fs.readFileSync(process.argv[2]||"research/basic_machine_real_targets.json","utf8"));console.log(JSON.stringify(benchmark(rows,Number(process.argv[3]||2000)),null,2));}
module.exports={benchmark};
