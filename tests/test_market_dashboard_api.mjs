import assert from 'node:assert/strict';
import * as XLSX from 'xlsx';
import {internals} from '../functions/api/market-dashboard.js';

function brentWorkbook(rows=[
  [new Date('2026-07-17T00:00:00Z'),85.01],
  [new Date('2026-07-20T00:00:00Z'),86.99]
]){
  const workbook=XLSX.utils.book_new();
  const sheet=XLSX.utils.aoa_to_sheet([
    ['Back to Contents','Data 1: Europe Brent Spot Price FOB (Dollars per Barrel)'],
    ['Sourcekey','RBRTE'],
    ['Date','Europe Brent Spot Price FOB (Dollars per Barrel)'],
    ...rows,
    [null,null]
  ]);
  XLSX.utils.book_append_sheet(workbook,sheet,'Data 1');
  return XLSX.write(workbook,{bookType:'xls',type:'array'});
}

const buffer=brentWorkbook();
const brent=internals.parseBrent(buffer);
assert.equal(brent.price,86.99);
assert.equal(brent.previousClose,85.01);
assert.ok(Math.abs(brent.change-1.98)<1e-10);
assert.equal(brent.marketDate,'2026-07-20');
assert.ok(Math.abs(brent.changePercent-((86.99-85.01)/85.01*100))<1e-10);

const gold=internals.parseGold({
  currency:'USD',
  price:4053.699951,
  symbol:'XAU',
  updatedAt:'2026-07-26T13:45:57.000Z'
});
assert.deepEqual(gold,{
  price:4053.699951,
  changePercent:null,
  timestamp:'2026-07-26T13:45:57.000Z',
  benchmark:'XAU'
});
console.log('PASS Gold Success Test');

for(const badGold of [
  {currency:'USD',price:null,symbol:'XAU',updatedAt:'2026-07-26T13:45:57.000Z'},
  {currency:'USD',price:4053.7,symbol:'XAU',updatedAt:'not-a-date'},
  {currency:'EUR',price:4053.7,symbol:'XAU',updatedAt:'2026-07-26T13:45:57.000Z'},
  {currency:'USD',price:4053.7,symbol:null,updatedAt:'2026-07-26T13:45:57.000Z'}
]){
  assert.throws(()=>internals.parseGold(badGold),/invalid_gold_data/);
}
console.log('PASS Gold Error Test');

assert.throws(()=>internals.parseBrent(brentWorkbook([
  [new Date('2026-07-20T00:00:00Z'),86.99],
  [new Date('2026-07-17T00:00:00Z'),null]
])),/insufficient_brent_data/);
console.log('PASS Oil Parser Test');

const goldPayload={
  currency:'USD',
  price:4053.699951,
  symbol:'XAU',
  updatedAt:'2026-07-26T13:45:57.000Z'
};
const successFetcher=async url=>{
  if(String(url).includes('gold-api')){
    return new Response(JSON.stringify(goldPayload),{
      status:200,
      headers:{'content-type':'application/json'}
    });
  }
  return new Response(buffer,{
    status:200,
    headers:{'content-type':'application/vnd.ms-excel'}
  });
};
const success=await internals.loadMarketData(successFetcher,100);
assert.equal(success.failures.length,0);
assert.equal(success.body.gold.price,4053.699951);
assert.equal(success.body.brent.price,86.99);
assert.ok(Math.abs(success.body.brent.change-1.98)<1e-10);

const goldError=await internals.loadMarketData(async url=>{
  if(String(url).includes('gold-api'))return new Response('upstream error',{status:502});
  return new Response(buffer,{status:200});
},100);
assert.equal(goldError.body.gold,undefined);
assert.equal(goldError.body.brent.price,86.99);
assert.deepEqual(goldError.failures.map(({asset})=>asset),['gold']);
assert.match(String(goldError.failures[0].error),/gold_http_502/);

const missingGoldField=await internals.loadMarketData(async url=>{
  if(String(url).includes('gold-api')){
    return new Response(JSON.stringify({...goldPayload,updatedAt:undefined}),{status:200});
  }
  return new Response(buffer,{status:200});
},100);
assert.equal(missingGoldField.body.brent.price,86.99);
assert.deepEqual(missingGoldField.failures.map(({asset})=>asset),['gold']);
assert.match(String(missingGoldField.failures[0].error),/invalid_gold_data/);
console.log('PASS Missing Field Test');

const timeoutResult=await internals.loadMarketData((url,{signal})=>{
  if(String(url).includes('gold-api')){
    return new Promise((resolve,reject)=>{
      signal.addEventListener('abort',()=>reject(signal.reason),{once:true});
    });
  }
  return Promise.resolve(new Response(buffer,{status:200}));
},5);
assert.equal(timeoutResult.body.brent.price,86.99);
assert.deepEqual(timeoutResult.failures.map(({asset})=>asset),['gold']);
assert.match(String(timeoutResult.failures[0].error),/upstream_timeout/);
console.log('PASS Timeout Test');

assert.equal(internals.finitePositive(0),null);
assert.equal(internals.finitePositive(undefined),null);

console.log('Market Dashboard API, Gold, Oil, timeout and missing-field tests passed');
