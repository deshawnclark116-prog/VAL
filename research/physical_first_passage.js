"use strict";
// Reproducible physical first-passage research; no production changes.
function runLab() {
  const configs = [
    {name:"fair", spread:0, noise:.025, exponent:1},
    {name:"small_variation", spread:.012, noise:.025, exponent:1},
    {name:"large_variation_stress", spread:.12, noise:.025, exponent:1},
    {name:"large_variation_wrong_physics", spread:.12, noise:.025, exponent:-1}
  ];
  const rigs=6, trials=20000, devices=4;
  function rng(seed){let s=seed>>>0;return ()=>{s=(s+0x6D2B79F5)>>>0;let t=s;t=Math.imul(t^t>>>15,t|1);t^=t+Math.imul(t^t>>>7,t|61);return ((t^t>>>14)>>>0)/4294967296;};}
  function normal(r){return Math.sqrt(-2*Math.log(Math.max(r(),1e-12)))*Math.cos(2*Math.PI*r());}
  function soft(x){const y=x.map(Math.exp),s=y.reduce((a,b)=>a+b,0);return y.map(z=>z/s);}
  function assert(b,m){if(!b)throw Error(m);}
  function table(width){
    const map=new Map(), labels=[], ids=new Int32Array(10**width);
    for(let i=0;i<ids.length;i++){const s=String(i).padStart(width,"0").split("").sort().join("");if(!map.has(s)){map.set(s,labels.length);labels.push(s);}ids[i]=map.get(s);}
    const multiplicity=new Int32Array(labels.length);for(const k of ids)multiplicity[k]++;
    assert(multiplicity.reduce((a,b)=>a+b,0)===10**width,"box partition");
    function masses(probs){const out=new Float64Array(labels.length);function rec(pos,id,p){if(pos===width){out[ids[id]]+=p;return;}for(let j=0;j<10;j++)rec(pos+1,id*10+j,p*probs[pos][j]);}rec(0,0,1);assert(Math.abs(out.reduce((a,b)=>a+b,0)-1)<1e-9,"normalized box");return out;}
    function best(v){let k=-1;for(let i=0;i<v.length;i++)if(multiplicity[i]>1&&(k===-1||v[i]>v[k]+1e-15))k=i;return k;}
    return {labels,ids,multiplicity,masses,best};
  }
  const report={version:"physical_first_passage_v1",assumptions:"Illustrative drag-to-mass acceleration surrogate; unmeasured actual Virginia equipment. Independent exponential travel distances, device shared by chambers; no winning-history training. Stress scenarios are not claims of real tolerances. Wrong-physics stress reverses the assumed effect.",rigs,trials_per_rig:trials,devices,results:[]};
  for(const w of [3,4,5]){
    const t=table(w),fair=Array.from(t.multiplicity,x=>x/10**w),fairMax=Math.max(...fair);
    assert(Math.abs(fairMax-[0,0,0,.006,.0024,.0012][w])<1e-12,"fair max");
    for(let ci=0;ci<configs.length;ci++){
      const c=configs[ci];const names=["unmeasured_fair","calibrated_pool_hidden_device","measured_selected_device","oracle_selected_device"];
      const metrics=Object.fromEntries(names.map(n=>[n,{hits:0,expected_hits:0,fair_expected_hits:0,box_log_gain:0}]));
      for(let rep=0;rep<rigs;rep++){
        const r=rng(81343+w*100003+ci*4919+rep*401), measurement=rng(9929+w*2029+ci*101+rep*17), draw=rng(51037+w*131071+ci*5923+rep*31);
        const truth=[], predicted=[];
        for(let k=0;k<devices;k++){
          const tv=[],pv=[];
          for(let j=0;j<w;j++){
            const z=[],m=[];
            for(let d=0;d<10;d++){
              // Relative log diameter and mass. For similar air flow, a~diameter^2/mass.
              const logDiameter=c.spread*normal(r)/Math.sqrt(5), logMass=c.spread*normal(r)/Math.sqrt(5);
              const mobility=2*logDiameter-logMass;
              z.push(c.exponent*mobility);
              const observed=mobility+c.noise*normal(measurement);
              // Prespecified Gaussian measurement-error shrinkage; no result fit.
              const shrink=c.spread*c.spread/(c.spread*c.spread+c.noise*c.noise);
              m.push(shrink*observed);
            }
            tv.push(soft(z));pv.push(soft(m));
          }
          truth.push(t.masses(tv));predicted.push(t.masses(pv));
        }
        const pool=Float64Array.from(fair,(_,i)=>predicted.reduce((s,p)=>s+p[i],0)/devices);
        const baselineDigits=Array.from({length:10},(_,i)=>i);
        for(let j=9;j>0;j--){const k=Math.floor(r()*(j+1));[baselineDigits[j],baselineDigits[k]]=[baselineDigits[k],baselineDigits[j]];}
        const baseline=t.labels.indexOf(baselineDigits.slice(0,w).sort((a,b)=>a-b).join(""));
        const picks=[Array(devices).fill(baseline),Array(devices).fill(t.best(pool)),predicted.map(t.best),truth.map(t.best)];
        const dists=[Array(devices).fill(fair),Array(devices).fill(pool),predicted,truth];
        // Expected hit probabilities integrate the unknown random apparatus selection.
        for(let q=0;q<names.length;q++){
          const m=metrics[names[q]];
          for(let k=0;k<devices;k++){
            m.expected_hits+=trials*truth[k][picks[q][k]]/devices;
            m.fair_expected_hits+=trials*fair[picks[q][k]]/devices;
            for(let i=0;i<fair.length;i++)m.box_log_gain+=truth[k][i]*Math.log(dists[q][k][i]/fair[i])/devices*trials;
          }
        }
        // The independent draw stream samples the physical race's exact categorical
        // law (exponential first passage) aggregated into full Box outcomes.
        const cdfs=truth.map(p=>{let sum=0;return Float64Array.from(p,v=>sum+=v);});
        for(let n=0;n<trials;n++){
          const k=Math.floor(draw()*devices),u=draw(),cdf=cdfs[k];let lo=0,hi=cdf.length-1;
          while(lo<hi){const mid=(lo+hi)>>1;if(cdf[mid]<u)lo=mid+1;else hi=mid;}
          for(let q=0;q<names.length;q++)metrics[names[q]].hits+=Number(picks[q][k]===lo);
        }
      }
      for(const m of Object.values(metrics)){
        m.expected_hits=+m.expected_hits.toFixed(4);m.fair_expected_hits=+m.fair_expected_hits.toFixed(4);
        m.box_log_gain=+(m.box_log_gain/(rigs*trials)).toFixed(8);
        m.expected_lift_vs_max_fair=+(m.expected_hits/(rigs*trials*fairMax)).toFixed(6);
      }
      if(ci===0)for(const m of Object.values(metrics))assert(Math.abs(m.expected_lift_vs_max_fair-1)<1e-9,"fair test must stay fair");
      assert(metrics.oracle_selected_device.expected_hits+1e-6>=metrics.measured_selected_device.expected_hits,"oracle bound");
      report.results.push({game:"pick"+w,scenario:c.name,draws:rigs*trials,metrics});
    }
  }
  return report;
}
if (require.main === module) process.stdout.write(JSON.stringify(runLab(), null, 2)+"\n");
module.exports = {runLab};
