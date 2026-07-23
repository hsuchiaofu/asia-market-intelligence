(function(){
  const el=document.querySelector('[data-view-count]');if(!el)return;
  const match=location.pathname.match(/^\/reports\/(morning|asia-close)\/(\d{4}-\d{2}-\d{2})(?:\.html)?$/);if(!match){el.textContent='閱讀 — 次';return}
  const id=`${match[1]}-${match[2]}`,key=`ami-view:${id}`,day=24*60*60*1000;
  let last=0;try{last=Number(localStorage.getItem(key)||0)}catch(_){}
  const shouldCount=Date.now()-last>=day;
  async function load(){
    try{let response;if(shouldCount){response=await fetch('/api/views',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({id})});if(response.ok)try{localStorage.setItem(key,String(Date.now()))}catch(_){}}else response=await fetch(`/api/views?id=${encodeURIComponent(id)}`,{cache:'no-store'});if(!response.ok)throw new Error('unavailable');const data=await response.json();const views=Number(data.views);el.textContent=Number.isFinite(views)?`閱讀 ${views.toLocaleString('zh-TW')} 次`:'閱讀 — 次'}catch(_){el.textContent='閱讀 — 次'}
  }
  load();
})();
