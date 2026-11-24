"use strict";
function raceCheck(){
  let state=293718;
  function u(){state=(Math.imul(state,1664525)+1013904223)>>>0;return (state+.5)/4294967296}
  const mobility=[.72,.81,.9,.96,1,1.04,1.09,1.18,1.24,1.36],total=mobility.reduce((a,b)=>a+b,0),n=500000,counts=Array(10).fill(0);
  for(let i=0;i<n;i++){let winner=0,min=Infinity;for(let d=0;d<10;d++){const distance=-Math.log(u());const time=Math.sqrt(2*distance/mobility[d]);if(time<min){min=time;winner=d}}counts[winner]++}
  const entries=counts.map((v,i)=>({digit:i,expected:mobility[i]/total,observed:v/n,z:(v-n*mobility[i]/total)/Math.sqrt(n*mobility[i]/total*(1-mobility[i]/total))}));
  const max_z=Math.max(...entries.map(x=>Math.abs(x.z)));if(max_z>5)throw Error("first-passage law check failed");
  return {n,max_z,entries};
}
if(require.main===module)console.log(JSON.stringify(raceCheck(),null,2));
module.exports={raceCheck};
