(()=>{
  const endpoint='https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true';
  const assets=[
    {id:'bitcoin',selector:'[data-market-asset="bitcoin"]',priceField:'usd',changeField:'usd_24h_change'},
    {id:'ethereum',selector:'[data-market-asset="ethereum"]',priceField:'usd',changeField:'usd_24h_change'}
  ];
  const priceFormatter=new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',currencyDisplay:'narrowSymbol',minimumFractionDigits:2,maximumFractionDigits:2});
  const state=new Map();
  let intervalId=null;

  function localTime(date){
    return `${String(date.getHours()).padStart(2,'0')}:${String(date.getMinutes()).padStart(2,'0')}`;
  }

  function changeView(value){
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
    changeElement.textContent=view.text;
    changeElement.className=`market-change ${view.className}`;
    timeElement.textContent=localTime(updatedAt);
    timeElement.dateTime=updatedAt.toISOString();
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

  async function update(){
    try{
      const response=await fetch(endpoint,{headers:{accept:'application/json'},cache:'no-store'});
      if(!response.ok)throw new Error(`CoinGecko HTTP ${response.status}`);
      const data=await response.json();
      const updatedAt=new Date();
      for(const asset of assets){
        const row=data?.[asset.id];
        const rawPrice=row?.[asset.priceField];
        const rawChange=row?.[asset.changeField];
        const price=Number(rawPrice);
        const change=Number(rawChange);
        if(typeof rawPrice!=='number'||typeof rawChange!=='number'||!Number.isFinite(price)||price<=0||!Number.isFinite(change)){
          renderUnavailable(asset);
          console.error(`CoinGecko returned invalid ${asset.id} data`);
          continue;
        }
        render(asset,price,change,updatedAt);
      }
    }catch(error){
      assets.forEach(renderUnavailable);
      console.error('Market Dashboard update failed',error);
    }
  }

  function start(){
    if(intervalId!==null||!assets.some(asset=>cardFor(asset)))return;
    update();
    intervalId=window.setInterval(update,60000);
  }

  document.addEventListener('DOMContentLoaded',start,{once:true});
})();
