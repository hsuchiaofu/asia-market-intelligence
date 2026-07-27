(()=>{
  const endpoints={
    crypto:'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true',
    commodities:'/api/market-dashboard'
  };
  const assets=[
    {id:'bitcoin',source:'crypto',selector:'[data-market-asset="bitcoin"]',priceField:'usd',changeField:'usd_24h_change',suffix:'   USD'},
    {id:'ethereum',source:'crypto',selector:'[data-market-asset="ethereum"]',priceField:'usd',changeField:'usd_24h_change',suffix:'   USD'},
    {id:'gold',source:'commodities',selector:'[data-market-asset="gold"]',priceField:'price',changeField:'changePercent',timeField:'timestamp',suffix:'   USD (XAU)',changeOptional:true},
    {id:'brent',source:'commodities',selector:'[data-market-asset="brent"]',priceField:'price',changeField:'changePercent',dateField:'marketDate',suffix:'   USD (Brent)'}
  ];
  const priceFormatter=new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',currencyDisplay:'narrowSymbol',minimumFractionDigits:2,maximumFractionDigits:2});
  const state=new Map();
  let intervalId=null;

  function localTime(date){
    return `${String(date.getHours()).padStart(2,'0')}:${String(date.getMinutes()).padStart(2,'0')}`;
  }

  function changeView(value){
    if(!Number.isFinite(value))return{text:'—',className:'neutral'};
    const rounded=Math.round(value*100)/100;
    if(rounded>0)return{text:`+${rounded.toFixed(2)}%`,className:'up'};
    if(rounded<0)return{text:`${rounded.toFixed(2)}%`,className:'down'};
    return{text:'0.00%',className:'neutral'};
  }

  function cardFor(asset){
    return document.querySelector(asset.selector);
  }

  function render(asset,price,change,updatedAt){
    const card=cardFor(asset);
    if(!card)return;
    const priceElement=card.querySelector('[data-market-price]');
    const changeElement=card.querySelector('[data-market-change]');
    const timeElement=card.querySelector('[data-market-time]');
    const statusElement=card.querySelector('[data-market-status]');
    const view=changeView(change);
    priceElement.textContent=priceFormatter.format(price).replace('$','$ ');
    priceElement.dataset.marketSuffix=asset.suffix;
    changeElement.textContent=view.text;
    changeElement.className=`market-change ${view.className}`;
    if(asset.dateField){
      timeElement.textContent=updatedAt.slice(5);
      timeElement.dateTime=updatedAt;
    }else{
      timeElement.textContent=localTime(updatedAt);
      timeElement.dateTime=updatedAt.toISOString();
    }
    priceElement.hidden=false;
    changeElement.hidden=false;
    timeElement.hidden=false;
    statusElement.hidden=true;
    state.set(asset.id,{hasData:true});
  }

  function renderUnavailable(asset){
    if(state.get(asset.id)?.hasData)return;
    const card=cardFor(asset);
    if(!card)return;
    card.querySelector('[data-market-status]').textContent='資料暫時無法取得';
  }

  async function updateSource(source){
    const sourceAssets=assets.filter(asset=>asset.source===source);
    try{
      const response=await fetch(endpoints[source],{headers:{accept:'application/json'},cache:'no-store'});
      if(!response.ok)throw new Error(`${source} HTTP ${response.status}`);
      const data=await response.json();
      const fetchedAt=new Date();
      for(const asset of sourceAssets){
        const row=data?.[asset.id];
        const rawPrice=row?.[asset.priceField];
        const rawChange=row?.[asset.changeField];
        const price=Number(rawPrice);
        const change=Number(rawChange);
        const validChange=typeof rawChange==='number'&&Number.isFinite(change);
        if(typeof rawPrice!=='number'||!Number.isFinite(price)||price<=0||(!validChange&&!asset.changeOptional)){
          renderUnavailable(asset);
          console.error(`${source} returned invalid ${asset.id} data`);
          continue;
        }
        const timeValue=asset.dateField?row?.[asset.dateField]:asset.timeField?new Date(row?.[asset.timeField]):fetchedAt;
        if((asset.dateField&&typeof timeValue!=='string')||(!asset.dateField&&Number.isNaN(timeValue.valueOf()))){
          renderUnavailable(asset);
          console.error(`${source} returned invalid ${asset.id} timestamp`);
          continue;
        }
        render(asset,price,validChange?change:NaN,timeValue);
      }
    }catch(error){
      sourceAssets.forEach(renderUnavailable);
      console.error(`Market Dashboard ${source} update failed`,error);
    }
  }

  function update(){
    return Promise.all(Object.keys(endpoints).map(updateSource));
  }

  function start(){
    if(intervalId!==null||!assets.some(asset=>cardFor(asset)))return;
    update();
    intervalId=window.setInterval(update,60000);
  }

  document.addEventListener('DOMContentLoaded',start,{once:true});
})();
