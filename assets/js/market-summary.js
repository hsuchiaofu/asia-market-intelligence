(()=>{
  const cardKeys=['global_macro','asia_markets','ai_semiconductor','fund_flow'];

  function validText(value){
    return typeof value==='string'&&Boolean(value.trim());
  }

  function validData(data){
    if(!data||typeof data!=='object'||Array.isArray(data))return false;
    if(!validText(data.updated_at)||!Number.isFinite(Date.parse(data.updated_at)))return false;
    if(!Array.isArray(data.source_reports)||!data.source_reports.length||!data.source_reports.every(validText))return false;
    return cardKeys.every(key=>validText(data[key]?.headline)&&validText(data[key]?.summary));
  }

  function updatedLabel(value){
    return `更新：${new Intl.DateTimeFormat('zh-TW',{
      month:'numeric',day:'numeric',hour:'2-digit',minute:'2-digit',hour12:false,timeZone:'Asia/Taipei'
    }).format(new Date(value))}`;
  }

  async function load(){
    const section=document.querySelector('[data-market-summary]');
    if(!section)return;

    try{
      const root=document.body.dataset.root||'.';
      const response=await fetch(`${root}/data/market-summary.json`,{
        cache:'no-store',headers:{accept:'application/json'}
      });
      if(!response.ok)throw new Error(`Market Summary HTTP ${response.status}`);

      const data=await response.json();
      if(!validData(data))throw new Error('Market Summary data format is invalid');

      const targets=cardKeys.map(key=>{
        const card=section.querySelector(`[data-market-summary-card="${key}"]`);
        const headline=card?.querySelector('[data-market-summary-headline]');
        const separator=card?.querySelector('[data-market-summary-separator]');
        const summary=card?.querySelector('[data-market-summary-text]');
        if(!card||!headline||!separator||!summary)throw new Error(`Market Summary target is missing: ${key}`);
        return{key,headline,separator,summary};
      });

      targets.forEach(({key,headline,separator,summary})=>{
        headline.textContent=data[key].headline.trim();
        summary.textContent=data[key].summary.trim();
        separator.hidden=false;
      });

      const updated=section.querySelector('[data-market-summary-updated]');
      if(updated){
        updated.textContent=updatedLabel(data.updated_at);
        updated.dateTime=data.updated_at;
      }
    }catch(error){
      console.error('Market Summary update failed',error);
    }
  }

  document.addEventListener('DOMContentLoaded',load,{once:true});
})();
