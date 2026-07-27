import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import vm from 'node:vm';

const root=path.resolve(import.meta.dirname,'..');
const source=await fs.readFile(path.join(root,'assets/js/market-dashboard.js'),'utf8');

function element(){
  return{textContent:'',hidden:true,className:'',dateTime:''};
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

async function run(responses){
  const cards={bitcoin:card(),ethereum:card()};
  let ready,intervalCallback,intervalDelay,fetchCalls=0;
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
    fetch:async()=>{
      const response=responses[Math.min(fetchCalls,responses.length-1)];
      fetchCalls+=1;
      if(response instanceof Error)throw response;
      return{ok:true,status:200,json:async()=>response};
    },
    console:{error:()=>{}},
    Intl,Number,Math,String,Date:LocalDate,Map
  };
  vm.runInNewContext(source,context);
  ready();
  await tick();
  return{cards,get fetchCalls(){return fetchCalls},intervalCallback,intervalDelay};
}

const success={
  bitcoin:{usd:118420.35,usd_24h_change:1.284},
  ethereum:{usd:3740.62,usd_24h_change:-0.544}
};
const dashboard=await run([success,new Error('offline'),{
  bitcoin:{usd:118420.35,usd_24h_change:0.004},
  ethereum:{usd:3740.62,usd_24h_change:0}
}]);

assert.equal(dashboard.fetchCalls,1,'頁面初始化應立即抓取一次');
assert.equal(dashboard.intervalDelay,60000,'應只建立 60 秒更新週期');
assert.equal(dashboard.cards.bitcoin.fields['[data-market-price]'].textContent,'$ 118,420.35');
assert.equal(dashboard.cards.ethereum.fields['[data-market-price]'].textContent,'$ 3,740.62');
assert.equal(dashboard.cards.bitcoin.fields['[data-market-change]'].textContent,'+1.28%');
assert.equal(dashboard.cards.bitcoin.fields['[data-market-change]'].className,'market-change up');
assert.equal(dashboard.cards.ethereum.fields['[data-market-change]'].textContent,'-0.54%');
assert.equal(dashboard.cards.ethereum.fields['[data-market-change]'].className,'market-change down');
assert.equal(dashboard.cards.bitcoin.fields['[data-market-time]'].textContent,'16:32');

const retained=dashboard.cards.bitcoin.fields['[data-market-price]'].textContent;
await dashboard.intervalCallback();
assert.equal(dashboard.cards.bitcoin.fields['[data-market-price]'].textContent,retained,'更新失敗應保留最後成功價格');
assert.equal(dashboard.cards.bitcoin.fields['[data-market-status]'].hidden,true,'更新失敗不應覆蓋成功內容');

await dashboard.intervalCallback();
assert.equal(dashboard.cards.bitcoin.fields['[data-market-change]'].textContent,'0.00%');
assert.equal(dashboard.cards.bitcoin.fields['[data-market-change]'].className,'market-change neutral');

const invalid=await run([{bitcoin:{usd:null,usd_24h_change:null},ethereum:{}}]);
for(const asset of ['bitcoin','ethereum']){
  assert.equal(invalid.cards[asset].fields['[data-market-status]'].textContent,'資料暫時無法取得');
  assert.equal(invalid.cards[asset].fields['[data-market-price]'].hidden,true);
}

console.log('Market Dashboard behavior tests passed');
