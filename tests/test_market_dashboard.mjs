import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import vm from 'node:vm';

const root=path.resolve(import.meta.dirname,'..');
const source=await fs.readFile(path.join(root,'assets/js/market-dashboard.js'),'utf8');

function element(){
  return{textContent:'',hidden:true,className:'',dateTime:'',dataset:{}};
}

function card(){
  const fields={
    '[data-market-price]':element(),
    '[data-market-change]':element(),
    '[data-market-time]':element(),
    '[data-market-status]':element()
  };
  fields['[data-market-status]'].hidden=false;
  fields['[data-market-status]'].textContent='資料暫時無法取得';
  return{fields,querySelector:selector=>fields[selector]};
}

async function tick(){
  await new Promise(resolve=>setTimeout(resolve,0));
}

async function run(responseSets){
  const cards=Object.fromEntries(['bitcoin','ethereum','gold','brent'].map(id=>[id,card()]));
  let ready,intervalCallback,intervalDelay;
  const calls=[];
  class LocalDate extends Date{
    constructor(...args){super(...(args.length?args:[2026,6,25,16,32,0]))}
  }
  const context={
    document:{
      addEventListener:(name,callback)=>{if(name==='DOMContentLoaded')ready=callback},
      querySelector:selector=>{
        const match=selector.match(/data-market-asset="([^"]+)"/);
        return match?cards[match[1]]:null;
      }
    },
    window:{setInterval:(callback,delay)=>{intervalCallback=callback;intervalDelay=delay;return 1}},
    fetch:async url=>{
      const sourceName=String(url).startsWith('https://api.coingecko.com')?'crypto':'commodities';
      const sourceCalls=calls.filter(call=>call===sourceName).length;
      calls.push(sourceName);
      const responses=responseSets[sourceName];
      const response=responses[Math.min(sourceCalls,responses.length-1)];
      if(response instanceof Error)throw response;
      return{ok:true,status:200,json:async()=>response};
    },
    console:{error:()=>{}},
    Intl,Number,Math,String,Date:LocalDate,Map,Promise
  };
  vm.runInNewContext(source,context);
  ready();
  await tick();
  return{cards,calls,intervalCallback,intervalDelay};
}

const cryptoSuccess={
  bitcoin:{usd:118420.35,usd_24h_change:1.284},
  ethereum:{usd:3740.62,usd_24h_change:-0.544}
};
const commoditySuccess={
  gold:{price:4053.7,changePercent:null,timestamp:'2026-07-25T08:32:00Z'},
  brent:{price:86.99,change:1.98,changePercent:2.3291377485,marketDate:'2026-07-20'}
};
const dashboard=await run({
  crypto:[cryptoSuccess,new Error('offline'),{
    bitcoin:{usd:118420.35,usd_24h_change:0.004},
    ethereum:{usd:3740.62,usd_24h_change:0}
  }],
  commodities:[commoditySuccess,new Error('offline'),commoditySuccess]
});

assert.deepEqual(dashboard.calls.sort(),['commodities','crypto'],'initial load fetches both sources once');
assert.equal(dashboard.intervalDelay,60000,'only one shared 60-second timer is created');
assert.equal(dashboard.cards.bitcoin.fields['[data-market-price]'].textContent,'$ 118,420.35');
assert.equal(dashboard.cards.bitcoin.fields['[data-market-price]'].dataset.marketSuffix,'   USD');
assert.equal(dashboard.cards.gold.fields['[data-market-price]'].textContent,'$ 4,053.70');
assert.equal(dashboard.cards.gold.fields['[data-market-price]'].dataset.marketSuffix,'   USD (XAU)');
assert.equal(dashboard.cards.brent.fields['[data-market-price]'].textContent,'$ 86.99');
assert.equal(dashboard.cards.brent.fields['[data-market-price]'].dataset.marketSuffix,'   USD (Brent)');
assert.equal(dashboard.cards.gold.fields['[data-market-change]'].textContent,'—');
assert.equal(dashboard.cards.gold.fields['[data-market-change]'].className,'market-change neutral');
assert.equal(dashboard.cards.brent.fields['[data-market-change]'].textContent,'+2.33%');
assert.equal(dashboard.cards.brent.fields['[data-market-change]'].className,'market-change up');
assert.equal(dashboard.cards.brent.fields['[data-market-time]'].textContent,'07-20');
assert.equal(dashboard.cards.bitcoin.fields['[data-market-time]'].textContent,'16:32');

const retained=dashboard.cards.gold.fields['[data-market-price]'].textContent;
const retainedTime=dashboard.cards.gold.fields['[data-market-time]'].textContent;
await dashboard.intervalCallback();
assert.equal(dashboard.cards.gold.fields['[data-market-price]'].textContent,retained,'a later failure retains the last successful commodity price');
assert.equal(dashboard.cards.gold.fields['[data-market-time]'].textContent,retainedTime,'a later failure retains the last successful Gold timestamp');
assert.equal(dashboard.cards.gold.fields['[data-market-status]'].hidden,true,'a later failure does not replace successful content');

await dashboard.intervalCallback();
assert.equal(dashboard.cards.bitcoin.fields['[data-market-change]'].textContent,'0.00%');
assert.equal(dashboard.cards.bitcoin.fields['[data-market-change]'].className,'market-change neutral');

const invalid=await run({
  crypto:[{bitcoin:{usd:null,usd_24h_change:null},ethereum:{}}],
  commodities:[{gold:{price:null,changePercent:null},brent:{price:0,changePercent:null}}]
});
for(const asset of ['bitcoin','ethereum','gold','brent']){
  assert.equal(invalid.cards[asset].fields['[data-market-status]'].textContent,'資料暫時無法取得');
  assert.equal(invalid.cards[asset].fields['[data-market-price]'].hidden,true);
}

const partialCommodity=await run({
  crypto:[cryptoSuccess],
  commodities:[{brent:commoditySuccess.brent,unavailable:['gold']}]
});
assert.equal(partialCommodity.cards.gold.fields['[data-market-status]'].hidden,false);
assert.equal(partialCommodity.cards.brent.fields['[data-market-status]'].hidden,true);
assert.equal(partialCommodity.cards.brent.fields['[data-market-price]'].textContent,'$ 86.99');

for(const missingChange of [null,undefined,NaN]){
  const goldWithoutChange=await run({
    crypto:[cryptoSuccess],
    commodities:[{
      gold:{price:4053.699951,changePercent:missingChange,timestamp:'2026-07-26T13:45:57.000Z'},
      brent:commoditySuccess.brent
    }]
  });
  assert.equal(goldWithoutChange.cards.gold.fields['[data-market-price]'].textContent,'$ 4,053.70');
  assert.equal(goldWithoutChange.cards.gold.fields['[data-market-price]'].dataset.marketSuffix,'   USD (XAU)');
  assert.equal(goldWithoutChange.cards.gold.fields['[data-market-change]'].textContent,'—');
  assert.equal(goldWithoutChange.cards.gold.fields['[data-market-change]'].className,'market-change neutral');
  assert.equal(goldWithoutChange.cards.gold.fields['[data-market-status]'].hidden,true);
}

for(const [change,className,text] of [[1.25,'up','+1.25%'],[-0.5,'down','-0.50%'],[0,'neutral','0.00%']]){
  const goldWithChange=await run({
    crypto:[cryptoSuccess],
    commodities:[{
      gold:{price:4053.7,changePercent:change,timestamp:'2026-07-26T13:45:57.000Z'},
      brent:commoditySuccess.brent
    }]
  });
  assert.equal(goldWithChange.cards.gold.fields['[data-market-change]'].textContent,text);
  assert.equal(goldWithChange.cards.gold.fields['[data-market-change]'].className,`market-change ${className}`);
}

for(const badGold of [
  {price:null,changePercent:null,timestamp:'2026-07-26T13:45:57.000Z'},
  {price:4053.7,changePercent:null,timestamp:'not-a-date'}
]){
  const invalidGold=await run({
    crypto:[cryptoSuccess],
    commodities:[{gold:badGold,brent:commoditySuccess.brent}]
  });
  assert.equal(invalidGold.cards.gold.fields['[data-market-status]'].hidden,false);
  assert.equal(invalidGold.cards.gold.fields['[data-market-price]'].hidden,true);
}

console.log('Market Dashboard behavior tests passed');
