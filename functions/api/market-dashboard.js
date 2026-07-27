import * as XLSX from 'xlsx';

const GOLD_URL='https://api.gold-api.com/price/XAU';
const BRENT_URL='https://www.eia.gov/dnav/pet/hist_xls/RBRTED.xls';
const CACHE_SECONDS=600;
const REQUEST_TIMEOUT_MS=15000;

function json(body,status=200,cacheSeconds=status===200?CACHE_SECONDS:0){
  return new Response(JSON.stringify(body),{
    status,
    headers:{
      'content-type':'application/json; charset=utf-8',
      'cache-control':cacheSeconds>0?`public, max-age=${cacheSeconds}, s-maxage=${cacheSeconds}`:'no-store'
    }
  });
}

function finitePositive(value){
  const number=Number(value);
  return Number.isFinite(number)&&number>0?number:null;
}

function localDateKey(date){
  return[
    date.getFullYear(),
    String(date.getMonth()+1).padStart(2,'0'),
    String(date.getDate()).padStart(2,'0')
  ].join('-');
}

function parseGold(data){
  const price=finitePositive(data?.price);
  const timestamp=new Date(data?.updatedAt);
  if(data?.symbol!=='XAU'||data?.currency!=='USD'||price===null||Number.isNaN(timestamp.valueOf())){
    throw new Error('invalid_gold_data');
  }
  return{
    price,
    changePercent:null,
    timestamp:timestamp.toISOString(),
    benchmark:'XAU'
  };
}

function parseBrent(buffer){
  const workbook=XLSX.read(buffer,{type:'array',cellDates:true});
  const sheet=workbook.Sheets['Data 1'];
  if(!sheet)throw new Error('missing_brent_sheet');
  const rows=XLSX.utils.sheet_to_json(sheet,{header:1,raw:true});
  const values=rows
    .map(row=>({date:row[0],price:finitePositive(row[1])}))
    .filter(row=>row.date instanceof Date&&!Number.isNaN(row.date.valueOf())&&row.price!==null)
    .sort((a,b)=>b.date-a.date);
  if(values.length<2)throw new Error('insufficient_brent_data');
  const [latest,previous]=values;
  const change=latest.price-previous.price;
  return{
    price:latest.price,
    previousClose:previous.price,
    change,
    changePercent:change/previous.price*100,
    marketDate:localDateKey(latest.date)
  };
}

async function fetchWithTimeout(fetcher,url,options={},timeoutMs=REQUEST_TIMEOUT_MS){
  const controller=new AbortController();
  const timeout=setTimeout(()=>controller.abort(new Error('upstream_timeout')),timeoutMs);
  try{
    return await fetcher(url,{...options,signal:controller.signal});
  }finally{
    clearTimeout(timeout);
  }
}

async function loadGold(fetcher=fetch,timeoutMs=REQUEST_TIMEOUT_MS){
  const goldResponse=await fetchWithTimeout(fetcher,GOLD_URL,{headers:{accept:'application/json'}},timeoutMs);
  if(!goldResponse.ok)throw new Error(`gold_http_${goldResponse.status}`);
  return parseGold(await goldResponse.json());
}

async function loadBrent(fetcher=fetch,timeoutMs=REQUEST_TIMEOUT_MS){
  const brentResponse=await fetchWithTimeout(fetcher,BRENT_URL,{headers:{accept:'application/vnd.ms-excel'}},timeoutMs);
  if(!brentResponse.ok)throw new Error(`brent_http_${brentResponse.status}`);
  return{...parseBrent(await brentResponse.arrayBuffer()),benchmark:'Brent'};
}

async function loadMarketData(fetcher=fetch,timeoutMs=REQUEST_TIMEOUT_MS){
  const [goldResult,brentResult]=await Promise.allSettled([
    loadGold(fetcher,timeoutMs),
    loadBrent(fetcher,timeoutMs)
  ]);
  const body={};
  const failures=[];
  if(goldResult.status==='fulfilled')body.gold=goldResult.value;
  else failures.push({asset:'gold',error:goldResult.reason});
  if(brentResult.status==='fulfilled')body.brent=brentResult.value;
  else failures.push({asset:'brent',error:brentResult.reason});
  return{body,failures};
}

export async function onRequestGet({request}){
  const cache=caches.default;
  const cacheKey=new Request(new URL('/api/market-dashboard',request.url),{method:'GET'});
  const cached=await cache.match(cacheKey);
  if(cached)return cached;
  try{
    const {body,failures}=await loadMarketData();
    if(failures.length){
      failures.forEach(({asset,error})=>console.error(`Market data ${asset} unavailable`,error));
      body.unavailable=failures.map(({asset})=>asset);
    }
    if(!body.gold&&!body.brent)return json({error:'market_data_unavailable',unavailable:body.unavailable},503,0);
    const complete=failures.length===0;
    const response=json(body,200,complete?CACHE_SECONDS:0);
    if(complete)await cache.put(cacheKey,response.clone());
    return response;
  }catch(error){
    console.error('Market data unavailable',error);
    return json({error:'market_data_unavailable'},503,0);
  }
}

export const internals={
  finitePositive,
  localDateKey,
  parseGold,
  parseBrent,
  fetchWithTimeout,
  loadGold,
  loadBrent,
  loadMarketData
};
