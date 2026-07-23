const AMI={
  reports:[],loadPromise:null,viewCounts:new Map(),
  validReport(x){return Boolean(x&&/^(morning|asia-close)-\d{4}-\d{2}-\d{2}$/.test(x.id)&&['morning','asia-close'].includes(x.type)&&x.status==='published'&&x.date===x.id.slice(x.type.length+1)&&x.file===`reports/${x.type}/${x.date}.html`&&typeof x.title==='string'&&x.title.trim()&&typeof x.summary==='string')},
  async load(){
    if(this.loadPromise)return this.loadPromise;
    const root=document.body.dataset.root||'.';
    this.loadPromise=fetch(`${root}/data/reports.json`,{cache:'no-store'}).then(async r=>{if(!r.ok)throw new Error('報告索引載入失敗');const raw=await r.json();if(!Array.isArray(raw))throw new Error('報告索引格式錯誤');const ids=new Set();this.reports=raw.filter(x=>this.validReport(x)&&!ids.has(x.id)&&ids.add(x.id)).sort((a,b)=>b.date.localeCompare(a.date));return this.reports}).catch(e=>{this.loadPromise=null;throw e});
    return this.loadPromise;
  },
  typeName:t=>t==='morning'?'全球新聞晨報':'亞洲股市收盤報',
  date:d=>new Intl.DateTimeFormat('zh-TW',{dateStyle:'long',timeZone:'Asia/Taipei'}).format(new Date(`${d}T12:00:00+08:00`)),
  updateCount(count,error=false){document.querySelectorAll('[data-report-count]').forEach(e=>{e.textContent=error?'無法載入報告資料':String(count)});document.querySelectorAll('[data-report-count-container]').forEach(e=>{e.textContent=error?'無法載入報告資料':`共 ${count} 份`})},
  render(items,el,emptyMessage='尚未有正式報告'){
    if(!items.length){el.innerHTML=`<div class="state">${this.escape(emptyMessage)}</div>`;return}
    el.innerHTML=`<ul class="report-list">${items.map(x=>`<li class="report-item"><span><span class="badge">${this.typeName(x.type)}</span><br><small>${this.date(x.date)}</small></span><span><strong><a href="${document.body.dataset.root||'.'}/${x.file}">${this.escape(x.title)}</a></strong><br><span class="muted">${this.escape(x.summary)}</span></span><span class="muted" data-view-id="${x.id}" aria-live="polite">閱讀 — 次</span></li>`).join('')}</ul>`;
    this.applyViewCounts(el);
  },
  applyViewCounts(scope=document){scope.querySelectorAll('[data-view-id]').forEach(el=>{const n=this.viewCounts.get(el.dataset.viewId);el.textContent=Number.isFinite(n)?`閱讀 ${n.toLocaleString('zh-TW')} 次`:'閱讀 — 次'})},
  async loadViewCounts(items,scope=document){
    const ids=[...new Set(items.map(x=>x.id))],missing=ids.filter(id=>!this.viewCounts.has(id));
    if(!missing.length){this.applyViewCounts(scope);return}
    try{const r=await fetch('/api/views/batch',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({ids:missing})});if(!r.ok)throw new Error('閱讀次數服務無法使用');const data=await r.json();for(const row of data.views||[])if(typeof row.id==='string'&&Number.isFinite(Number(row.views)))this.viewCounts.set(row.id,Number(row.views));this.applyViewCounts(scope)}catch(_){this.applyViewCounts(scope)}
  },
  escape:s=>String(s).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]))
};
document.addEventListener('DOMContentLoaded',async()=>{const targets=document.querySelectorAll('[data-report-list]');if(!targets.length)return;try{const all=await AMI.load(),shown=[];targets.forEach(el=>{let list=[...all];const type=el.dataset.type;if(type)list=list.filter(x=>x.type===type);list=list.slice(0,Number(el.dataset.limit||100));shown.push(...list);AMI.render(list,el)});AMI.updateCount(all.length);await AMI.loadViewCounts(shown)}catch(_){AMI.updateCount(0,true);targets.forEach(el=>el.innerHTML='<div class="state">無法載入報告資料</div>')}});
