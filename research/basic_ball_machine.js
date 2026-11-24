"use strict";
// Fair virtual ball machine. A seed is for reproducible experiments only.
function seededRandom(seed) {
  if (!Number.isInteger(seed) || seed<0 || seed>0xffffffff) throw new Error("Seed must be a uint32");
  let state=seed>>>0;
  return function uint32(){
    state=(state+0x6D2B79F5)>>>0;
    let t=state;
    t=Math.imul(t^(t>>>15),t|1);
    t^=t+Math.imul(t^(t>>>7),t|61);
    return (t^(t>>>14))>>>0;
  };
}

function uniformIndex(n, uint32) {
  if (!Number.isInteger(n)||n<1||n>0x100000000) throw new Error("Invalid index bound");
  const limit=Math.floor(0x100000000/n)*n;
  let x;
  do {x=uint32();if(!Number.isInteger(x)||x<0||x>0xffffffff)throw new Error("Invalid random value");} while(x>=limit);
  return x%n;
}

function draw(game,uint32) {
  const width={pick3:3,pick4:4,pick5:5}[game];
  if(!width)throw new Error("Use pick3, pick4 or pick5");
  const chambers=[],numbers=[];
  for(let j=0;j<width;j++){
    const balls=Array.from({length:10},(_,i)=>i);
    for(let i=9;i>0;i--){const k=uniformIndex(i+1,uint32);[balls[i],balls[k]]=[balls[k],balls[i]];}
    numbers.push(balls[0]);
    chambers.push(balls);
  }
  return {game,numbers,chambers};
}

function boxKey(digits){return [...digits].sort((a,b)=>a-b).join("");}

function test(){
  function ok(x,msg){if(!x)throw new Error(msg);}
  const a=seededRandom(11),b=seededRandom(11);
  for(let i=0;i<100;i++)ok(JSON.stringify(draw("pick5",a))===JSON.stringify(draw("pick5",b)),"reproducibility");
  let rejected=0;ok(uniformIndex(10,()=>++rejected===1?0xffffffff:9)===9&&rejected===2,"rejection sample");
  const results=[];
  for(const w of [3,4,5]){
    const game="pick"+w,n=100000,r=seededRandom(20261123+w),other=seededRandom(7800123+w);
    const counts=Array.from({length:w},()=>Array(10).fill(0)),pair=Array.from({length:100},()=>0);
    let repeats=0,boxHits=0,exact=0;
    for(let i=0;i<n;i++){
      const x=draw(game,r),y=draw(game,other);
      ok(x.numbers.length===w&&x.chambers.length===w,"width");
      for(let j=0;j<w;j++){
        ok(boxKey(x.chambers[j])==="0123456789","each chamber contains all ten balls");
        ok(x.numbers[j]===x.chambers[j][0],"selected ball");
        counts[j][x.numbers[j]]++;
      }
      pair[x.numbers[0]*10+x.numbers[1]]++;
      repeats+=Number(new Set(x.numbers).size<w);
      boxHits+=Number(boxKey(x.numbers)===boxKey(y.numbers));
      exact+=Number(x.numbers.join("")===y.numbers.join(""));
    }
    const noRepeat=Array.from({length:w},(_,i)=>(10-i)/10).reduce((a,b)=>a*b,1);
    const chi=counts.map(c=>c.reduce((s,x)=>s+(x-n/10)**2/(n/10),0));
    const pairChi=pair.reduce((s,x)=>s+(x-n/100)**2/(n/100),0);
    ok(chi.every(x=>x<35),"gross marginal discrepancy");
    ok(pairChi<165,"gross chamber-pair discrepancy");
    ok(Math.abs(repeats-n*(1-noRepeat))<5*Math.sqrt(n*noRepeat*(1-noRepeat)),"repeat sanity");
    // Exact probability that two independent draws have identical digit multisets.
    const hist={};for(let i=0;i<10**w;i++){const key=String(i).padStart(w,"0").split("").sort().join("");hist[key]=(hist[key]||0)+1;}
    const expectedBox=n*Object.values(hist).reduce((s,c)=>s+(c/10**w)**2,0);
    results.push({game,draws:n,position_chi_square:chi,pair_chi_square:pairChi,observed_repeat_fraction:repeats/n,expected_repeat_fraction:1-noRepeat,independent_machine_box_hits:boxHits,expected_box_hits:expectedBox,independent_machine_straight_hits:exact,expected_straight_hits:n/10**w,example:draw(game,r).numbers});
  }
  return {version:"virtual_ball_machine_v1",scope:"Independent fair virtual chambers; synthetic validation only, no predictive advantage claimed.",tests:"pass",results};
}
if(require.main===module){const args=process.argv.slice(2);if(args[0]==="--test") console.log(JSON.stringify(test(),null,2));else{const game=args[0]||"pick3";const rng=args[1]===undefined?()=>require("node:crypto").randomBytes(4).readUInt32LE():seededRandom(Number(args[1]));console.log(JSON.stringify(draw(game,rng),null,2));}}
module.exports={draw,seededRandom,boxKey,test};
